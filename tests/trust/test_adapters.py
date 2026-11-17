import hashlib
import importlib.util
import json
import marshal
import os
from pathlib import Path
import shutil
import signal
import struct
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[2]


def load_module(name, filename):
    specification = importlib.util.spec_from_file_location(name, ROOT / "tools/trust" / filename)
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


ADAPTER = load_module("trust_adapter_under_test", "check.py")
NATIVE = load_module("trust_native_under_test", "native_probe.py")


class HarnessPinProperties(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="trust-pin-")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        self.entry = self.root / "run.py"
        shutil.copyfile(ROOT / "tools/trust/run.py", self.entry)
        self.vendor = self.root / "vendor"
        self.package = self.vendor / "trustkit"
        self.package.mkdir(parents=True)
        (self.package / "__init__.py").write_text("")
        (self.package / "cli.py").write_text("import argparse\ndef main():\n    print('PINNED-CODE')\n    return 0\n")
        files = {path.relative_to(self.vendor).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
                 for path in self.package.iterdir()}
        (self.vendor / "ORIGIN.json").write_text(json.dumps({"files": files}))

    def invoke(self):
        environment = {**os.environ, "PYTHONDONTWRITEBYTECODE": ""}
        return subprocess.run([sys.executable, str(self.entry)], env=environment, capture_output=True, text=True, timeout=10)

    def assert_rejected(self):
        result = self.invoke()
        self.assertNotEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertNotIn("PINNED-CODE", result.stdout)
        self.assertNotIn("UNPINNED-CODE", result.stdout)

    def test_exact_pinned_package_can_execute_twice_without_creating_cache(self):
        for _ in range(2):
            result = self.invoke()
            self.assertEqual(0, result.returncode, result.stderr)
            self.assertIn("PINNED-CODE", result.stdout)
        self.assertFalse(list(self.package.rglob("*.pyc")))

    def test_modified_pinned_module_is_rejected(self):
        (self.package / "cli.py").write_text("def main():\n    print('UNPINNED-CODE')\n    return 0\n")
        self.assert_rejected()

    def test_nested_unpinned_module_is_rejected(self):
        nested = self.package / "nested"
        nested.mkdir()
        (nested / "extra.py").write_text("value = 1\n")
        self.assert_rejected()

    def test_unpinned_sibling_cannot_shadow_a_standard_library_import(self):
        (self.vendor / "argparse.py").write_text("print('UNPINNED-CODE')\nraise SystemExit(0)\n")
        self.assert_rejected()

    def test_unpinned_sibling_directory_is_rejected(self):
        (self.vendor / "unreviewed-package").mkdir()
        self.assert_rejected()

    @unittest.skipUnless(hasattr(os, "mkfifo"), "Special-file inspection requires POSIX")
    def test_unpinned_special_file_is_rejected_without_reading_it(self):
        os.mkfifo(self.vendor / "unreviewed-pipe")
        self.assert_rejected()

    def test_symlinked_nested_file_is_rejected(self):
        external = self.root / "external.py"
        external.write_text("value = 1\n")
        (self.package / "extra.py").symlink_to(external)
        self.assert_rejected()

    def test_symlinked_nested_directory_is_rejected(self):
        external = self.root / "external"
        external.mkdir()
        (self.package / "nested").symlink_to(external, target_is_directory=True)
        self.assert_rejected()

    def test_symlinked_pin_manifest_is_rejected(self):
        manifest = self.vendor / "ORIGIN.json"
        external = self.root / "origin.json"
        manifest.rename(external)
        manifest.symlink_to(external)
        self.assert_rejected()

    def test_matching_bytecode_cache_cannot_replace_pinned_source(self):
        source = self.package / "cli.py"
        compiled = Path(importlib.util.cache_from_source(str(source)))
        compiled.parent.mkdir()
        header = importlib.util.MAGIC_NUMBER + struct.pack("<III", 0, int(source.stat().st_mtime), source.stat().st_size)
        code = compile("def main():\n    print('UNPINNED-CODE')\n    return 0\n", str(source), "exec")
        compiled.write_bytes(header + marshal.dumps(code))
        self.assert_rejected()


class BuildAdapterProperties(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="trust-build-adapter-")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        subprocess.run(["git", "init", "-q", str(self.root)], check=True)
        (self.root / "src").mkdir()
        (self.root / "src/main.c").write_text("int main(void) { return 0; }\n")
        (self.root / "linker.ld").write_text("SECTIONS {}\n")
        (self.root / "Makefile").write_text("all:\n\ttrue\n")
        self.output = self.root / "build/evidence"
        self.output.mkdir(parents=True)
        self.mode = "valid"
        self.builds = 0

    def fake_make(self, command, output, name, env, timeout=600):
        candidate = self.output / "candidate"
        if "clean" in command:
            if candidate.exists():
                shutil.rmtree(candidate)
            return
        self.builds += 1
        candidate.mkdir()
        rom = bytearray(256)
        rom[0xBD] = (-0x19) & 255
        rom[0xC0:0xC9] = b"SRAM_V113"
        if self.mode == "bad-header":
            rom[0xBD] ^= 1
        (candidate / "emberbond.gba").write_bytes(rom)
        (candidate / "emberbond.elf").write_bytes(b"ELF" + (bytes([self.builds]) if self.mode == "nondeterminism" else b""))
        (candidate / "emberbond.map").write_text("map\n")
        iwram_end = "03008000" if self.mode == "overlap-stack" else "03006000"
        (candidate / "emberbond.sym").write_text(
            "03000000 T __iwram_start\n" + iwram_end + " T __iwram_end\n"
            "02000000 D __data_start\n02010000 B __bss_end\n"
        )
        source_hashes = ADAPTER.runtime_snapshot(self.root)
        if self.mode == "stale-source-receipt":
            source_hashes["src/main.c"] = "0" * 64
        (candidate / "source-hashes.json").write_text(json.dumps(source_hashes))
        if self.mode == "source-mutation":
            (self.root / "src/main.c").write_text("int main(void) { return 1; }\n")

    def build(self):
        with patch.object(ADAPTER, "ROOT", self.root), patch.object(ADAPTER, "run", self.fake_make), \
             patch.object(ADAPTER, "resolve_arm_tools", return_value={"gcc": sys.executable}):
            ADAPTER.build(self.output, os.environ.copy())

    def test_matching_clean_builds_publish_a_successful_artifact_receipt(self):
        self.build()
        report = json.loads((self.output / "build.json").read_text())
        self.assertIs(True, report["passed"])
        self.assertEqual(2, len(report["clean_builds"]))
        self.assertEqual(report["clean_builds"][0], report["clean_builds"][1])

    def test_bad_candidate_or_changed_input_never_publishes_success(self):
        for mode in ("nondeterminism", "stale-source-receipt", "source-mutation", "bad-header", "overlap-stack"):
            with self.subTest(mode=mode):
                self.mode = mode
                (self.root / "src/main.c").write_text("int main(void) { return 0; }\n")
                with self.assertRaises((RuntimeError, ValueError)):
                    self.build()
                self.assertFalse((self.output / "build.json").exists())


class ChildProcessProperties(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="trust-child-adapter-")
        self.addCleanup(temporary.cleanup)
        self.output = Path(temporary.name).resolve()

    def test_failed_child_is_not_reported_as_success(self):
        with self.assertRaises(RuntimeError):
            ADAPTER.run([sys.executable, "-c", "print('diagnostic'); raise SystemExit(7)"],
                        self.output, "failed", os.environ.copy(), timeout=5)
        self.assertIn("diagnostic", (self.output / "failed.log").read_text())

    @unittest.skipUnless(os.name == "posix", "Runner process-group cleanup requires POSIX")
    def test_pinned_runner_sigterm_stops_checks_and_descendants_without_passing_evidence(self):
        root = self.output / "repository"
        root.mkdir()
        subprocess.run(["git", "init", "-q", str(root)], check=True)
        (root / ".trust").mkdir()
        for ignore_term in (False, True):
            with self.subTest(ignore_term=ignore_term):
                prefix = self.output / str(ignore_term)
                ready, child_ready = prefix.with_suffix(".ready"), prefix.with_suffix(".child-ready")
                markers = [prefix.with_suffix(".check-survived"), prefix.with_suffix(".child-survived")]
                disposition = "signal.signal(signal.SIGTERM, signal.SIG_IGN); " if ignore_term else ""
                child_code = (
                    "import signal, time; from pathlib import Path; " + disposition +
                    f"Path({str(child_ready)!r}).touch(); time.sleep(0.8); "
                    f"Path({str(markers[1])!r}).touch(); time.sleep(20)"
                )
                check_code = (
                    "import os, signal, subprocess, sys, time; from pathlib import Path; " + disposition +
                    f"subprocess.Popen([sys.executable, '-c', {child_code!r}]); "
                    f"child_ready = Path({str(child_ready)!r})\n"
                    "while not child_ready.exists(): time.sleep(0.01)\n"
                    f"Path({str(ready)!r}).write_text(str(os.getpid())); time.sleep(0.8); "
                    f"Path({str(markers[0])!r}).touch(); time.sleep(20)"
                )
                runtime = "import os; from pathlib import Path; Path(os.environ['TRUST_EVIDENCE_DIR'], 'observed.json').write_text('{}')"
                policy = {
                    "version": 1, "project": "cancellation",
                    "checks": [
                        {"id": "active", "layer": "static", "command": [sys.executable, "-c", check_code], "timeout_seconds": 20},
                        {"id": "behavior", "layer": "runtime", "command": [sys.executable, "-c", runtime],
                         "timeout_seconds": 5, "artifacts": ["observed.json"]},
                    ],
                    "features": [{"id": "observed", "user_path": "run", "expectation": "evidence", "checks": ["behavior"]}],
                }
                (root / ".trust/policy.json").write_text(json.dumps(policy))
                process = subprocess.Popen(
                    [sys.executable, str(ROOT / "tools/trust/run.py"), "run", "--root", str(root)],
                    env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}, stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE, text=True, start_new_session=True,
                )
                check_pid = None
                try:
                    deadline = time.monotonic() + 5
                    while not ready.exists() and process.poll() is None and time.monotonic() < deadline:
                        time.sleep(0.01)
                    self.assertTrue(ready.exists(), "The check and descendant must start before cancellation")
                    check_pid = int(ready.read_text())
                    process.send_signal(signal.SIGTERM)
                    if ignore_term:
                        time.sleep(0.05)
                        process.send_signal(signal.SIGTERM)
                    stdout, stderr = process.communicate(timeout=5)
                    self.assertNotEqual(0, process.returncode, stdout + stderr)
                    self.assertNotIn("Traceback (most recent call last)", stderr)
                    time.sleep(0.9)
                    self.assertFalse(any(path.exists() for path in markers), "Cancelled work continued running")
                    self.assertFalse(any(json.loads(path.read_text())["passed"] for path in root.rglob("receipt.json")))
                finally:
                    if process.poll() is None:
                        os.killpg(process.pid, signal.SIGKILL)
                    process.communicate(timeout=5)
                    if check_pid is not None:
                        try:
                            os.killpg(check_pid, signal.SIGKILL)
                        except ProcessLookupError:
                            pass

    def test_spawn_failure_restores_original_signal_handler(self):
        original = signal.getsignal(signal.SIGTERM)
        try:
            with self.assertRaises(FileNotFoundError):
                ADAPTER.run([str(self.output / "missing-command")], self.output, "missing", os.environ.copy())
            self.assertEqual(original, signal.getsignal(signal.SIGTERM))
        finally:
            signal.signal(signal.SIGTERM, original)

    def test_log_open_failure_restores_original_signal_handler(self):
        original = signal.getsignal(signal.SIGTERM)
        try:
            with self.assertRaises(FileNotFoundError):
                ADAPTER.run([sys.executable, "-c", "pass"], self.output / "missing", "missing", os.environ.copy())
            self.assertEqual(original, signal.getsignal(signal.SIGTERM))
        finally:
            signal.signal(signal.SIGTERM, original)

    def child_command(self, marker, ready=None):
        descendant = ("import signal,time; from pathlib import Path; signal.signal(signal.SIGTERM, signal.SIG_IGN); "
                      "time.sleep(0.7); Path(" + repr(str(marker)) + ").touch()")
        parent = "import os,signal,subprocess,sys,time; from pathlib import Path; signal.signal(signal.SIGTERM, signal.SIG_IGN); "
        parent += "subprocess.Popen([sys.executable,'-c'," + repr(descendant) + "]); "
        if ready:
            parent += "Path(" + repr(str(ready)) + ").write_text(str(os.getpid())); "
        parent += "time.sleep(30)"
        return [sys.executable, "-c", parent]

    @unittest.skipUnless(os.name == "posix", "Adapter process-group cleanup requires POSIX")
    def test_timeout_terminates_descendants_even_when_sigterm_is_ignored(self):
        marker = self.output / "orphan-wrote"
        with self.assertRaises(subprocess.TimeoutExpired):
            ADAPTER.run(self.child_command(marker), self.output, "timeout", os.environ.copy(), timeout=0.15)
        time.sleep(0.8)
        self.assertFalse(marker.exists())

    @unittest.skipUnless(os.name == "posix", "Adapter process-group cleanup requires POSIX")
    def test_outer_termination_cleans_child_group_before_outer_kill_deadline(self):
        marker, ready = self.output / "orphan-wrote", self.output / "ready"
        helper = (
            "import importlib.util, os; from pathlib import Path; "
            "spec=importlib.util.spec_from_file_location('adapter'," + repr(str(ROOT / "tools/trust/check.py")) + "); "
            "module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module); "
            "module.run(" + repr(self.child_command(marker, ready)) + ", Path(" + repr(str(self.output)) + "), 'outer', os.environ.copy())"
        )
        process = subprocess.Popen([sys.executable, "-c", helper], stdout=subprocess.DEVNULL,
                                   stderr=subprocess.DEVNULL, start_new_session=True)
        child_group = None
        cleanup_child = True
        try:
            deadline = time.monotonic() + 5
            while not ready.exists() and time.monotonic() < deadline:
                time.sleep(0.01)
            self.assertTrue(ready.exists(), "Child process did not start")
            child_group = int(ready.read_text())
            os.killpg(process.pid, signal.SIGTERM)
            time.sleep(0.25)
            if process.poll() is None:
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
            process.wait(timeout=5)
            time.sleep(0.6)
            self.assertFalse(marker.exists())
            cleanup_child = False
        finally:
            for group in (child_group if cleanup_child else None, process.pid if process.poll() is None else None):
                if group:
                    try:
                        os.killpg(group, signal.SIGKILL)
                    except (ProcessLookupError, PermissionError):
                        pass
            process.wait(timeout=5)


READ_ONLY_CORE = r"""
#ifndef TRUST_READ_ONLY_CORE_H
#define TRUST_READ_ONLY_CORE_H
#include <stdint.h>
#include <stdbool.h>
#include <stdarg.h>
#include <stdio.h>
#include <fcntl.h>
typedef uint32_t color_t;
struct VFile;
struct mCoreConfig { int unused; };
struct mCoreCallbacks { void *context; void (*coreCrashed)(void *); };
struct mCore {
 struct mCoreConfig config;
 bool (*init)(struct mCore *);
 void (*deinit)(struct mCore *);
 void (*setVideoBuffer)(struct mCore *, color_t *, unsigned);
 void (*addCoreCallbacks)(struct mCore *, const struct mCoreCallbacks *);
 bool (*loadTemporarySave)(struct mCore *, struct VFile *);
 void (*reset)(struct mCore *);
 void (*setKeys)(struct mCore *, unsigned);
 void (*runFrame)(struct mCore *);
 uint32_t (*busRead32)(struct mCore *, uint32_t);
 uint16_t (*busRead16)(struct mCore *, uint32_t);
 uint8_t (*busRead8)(struct mCore *, uint32_t);
};
enum mLogLevel { mLOG_ERROR=1, mLOG_FATAL=2 };
struct mLogger { void (*log)(struct mLogger *, int, enum mLogLevel, const char *, va_list); };
extern void mLogSetDefaultLogger(struct mLogger *);
extern struct mCore *mCoreFind(const char *);
extern void mCoreConfigInit(struct mCoreConfig *, const char *);
extern void mCoreConfigSetDefaultIntValue(struct mCoreConfig *, const char *, int);
extern void mCoreConfigDeinit(struct mCoreConfig *);
extern void mCoreLoadConfig(struct mCore *);
extern bool mCoreLoadFile(struct mCore *, const char *);
extern struct VFile *VFileOpen(const char *, int);
#endif
"""


class NativeCapabilityProperties(unittest.TestCase):
    def test_bridge_compiles_against_read_only_core_and_exports_only_observation_api(self):
        with tempfile.TemporaryDirectory(prefix="trust-native-capabilities-") as directory:
            root = Path(directory)
            for filename in ("mgba/core/core.h", "mgba/core/log.h", "mgba-util/vfs.h"):
                target = root / filename
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(READ_ONLY_CORE)
            compiler = shutil.which(os.environ.get("HOST_CC", "cc"))
            self.assertIsNotNone(compiler)
            object_file = root / "observer.o"
            result = subprocess.run([compiler, "-std=c11", "-D_GNU_SOURCE", "-Wall", "-Wextra", "-Werror", "-I", str(root),
                                     "-c", str(ROOT / "tools/trust/native_bridge.c"), "-o", str(object_file)],
                                    capture_output=True, text=True, timeout=30)
            self.assertEqual(0, result.returncode, result.stderr)
            command = ["nm", "-gU"] if sys.platform == "darwin" else ["nm", "-g", "--defined-only"]
            symbols = subprocess.check_output(command + [str(object_file)], text=True)
            defined = {line.split()[-1].removeprefix("_") for line in symbols.splitlines() if len(line.split()) >= 3}
            self.assertEqual({"trust_open", "trust_close", "trust_step", "trust_read", "trust_faults", "trust_rgb", "trust_library_path"}, defined)

    def test_observer_rejects_dropped_updates_deadline_misses_and_native_faults(self):
        class Function:
            def __init__(self, callback):
                self.callback = callback

            def __call__(self, *args):
                return self.callback(*args)

        with tempfile.TemporaryDirectory(prefix="trust-native-observer-") as directory:
            output = Path(directory)
            names = ("game_state", "room", "px", "py", "hp", "has_save", "frame", "render_cycles",
                     "render_profile_serial", "music_faults")
            symbols = output / "symbols"
            symbols.write_text("".join(f"{index:08x} T {name}\n" for index, name in enumerate(names)))
            values = {index: 0 for index in range(len(names))}
            mode = {"serial": 2, "faults": 0}
            calls = []

            def step(handle, keys):
                calls.append(("keys", keys))
                values[8] += mode["serial"]

            class ReadOnlyLibrary:
                trust_open = Function(lambda rom, save: 1)
                trust_close = Function(lambda handle: calls.append(("close", handle)))
                trust_step = Function(step)
                trust_read = Function(lambda handle, address, width: values[address])
                trust_faults = Function(lambda handle: mode["faults"])
                trust_rgb = Function(lambda handle, output: None)
                trust_library_path = Function(lambda: str(output / "mgba-library").encode())

            with patch.object(NATIVE.C, "CDLL", return_value=ReadOnlyLibrary()):
                observer = NATIVE.Observation(output / "rom", symbols, output / "bridge", output)
                try:
                    observer.step(3, 16)
                    self.assertEqual(3, observer.measured_frames)
                    self.assertEqual([("keys", 16)] * 3, calls)
                    for serial, cycles, faults, audio in ((0, 0, 0, 0), (2, 280897, 0, 0), (2, 0, 1, 0), (2, 0, 0, 1)):
                        mode.update(serial=serial, faults=faults)
                        values[7], values[9] = cycles, audio
                        with self.assertRaises(AssertionError):
                            observer.step()
                finally:
                    observer.close()


if __name__ == "__main__":
    unittest.main()
