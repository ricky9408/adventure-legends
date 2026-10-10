#!/usr/bin/env python3
"""Production content11 treasure/Gear matrix, strict and ASan/UBSan host builds.

Authenticates the bundled developer SRAM before the native C decoder imports
it. The C test prepares valid wallets and loadouts from that historical state.
Host arithmetic and menu/cache assertions are not native controller evidence.
No ROM, source, save fixture, or build-system file is modified by this runner.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shlex
import subprocess
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests/fixtures/v5-revision9/covenants-all128-72-cold.sav"
FIXTURE_SHA = "eec8efbfeaf83a51b66faa0c8e9d6a3061af36b88fb6d7b3aa77fbc47107122a"
SOURCES = [
    "tests/gear_treasure_effective_host.c", "src/gear_preview.c",
    "src/gear_runtime.c", "src/weapon_actions.c", "src/companion_guide.c",
    "src/creatures.c", "src/creature_data.c", "src/economy.c",
    "src/equipment.c", "src/equipment_data.c", "src/save4.c", "src/save5.c",
    "src/southern_quests.c", "src/magma_quests.c",
]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, help="Optional JSON evidence report")
    parser.add_argument("--candidate", type=Path, help="Verify tested production sources against a frozen candidate")
    args = parser.parse_args()
    assert sha(FIXTURE) == FIXTURE_SHA
    provenance = json.loads((FIXTURE.parent / "provenance.json").read_text())
    declared = next(row for row in provenance["fixtures"] if row["path"].endswith(FIXTURE.name))
    assert declared["sha256"] == FIXTURE_SHA and declared["gear_count"] == 48
    compiler = shlex.split(os.environ.get("HOST_CC", "cc"))
    # Include every transitive local header/policy/table, not just the C units.
    dependencies = subprocess.check_output(
        [*compiler, "-DSAVE4_HOST_TEST", "-DSAVE5_HOST_TEST", "-Isrc", "-MM", *SOURCES],
        cwd=ROOT, text=True,
    )
    tracked = {str((ROOT / name).resolve().relative_to(ROOT))
               for name in shlex.split(dependencies.replace("\\\n", " ")) if not name.endswith(":")}
    tracked.add("tests/gear_treasure_host.py")
    source_hashes = {name: sha(ROOT / name) for name in sorted(tracked)}
    candidate = None
    if args.candidate:
        folder = args.candidate.resolve()
        frozen = json.loads((folder / "source-hashes.json").read_text())
        for name, digest in source_hashes.items():
            if name.startswith("src/"):
                assert frozen[name] == digest, f"Production source differs from candidate: {name}"
        candidate = {name: sha(folder / name) for name in ("emberbond.gba", "emberbond.sym", "source-hashes.json")}
    runs = []
    with tempfile.TemporaryDirectory(prefix="gear-treasure-host-") as temporary:
        for label, flags in [
            ("strict", []),
            ("asan-ubsan", ["-fsanitize=address,undefined", "-fno-omit-frame-pointer"]),
        ]:
            executable = Path(temporary) / label
            compile_command = [
                *compiler, "-std=c99", "-O1", "-g",
                "-Wall", "-Wextra", "-Werror", "-Wno-misleading-indentation",
                "-ffunction-sections", "-fdata-sections", "-Wl,--gc-sections",
                "-DSAVE4_HOST_TEST", "-DSAVE5_HOST_TEST", "-Isrc",
                *flags, *SOURCES, "-o", str(executable),
            ]
            subprocess.run(compile_command, cwd=ROOT, check=True)
            started = time.monotonic()
            result = subprocess.run(
                [str(executable), str(FIXTURE)], cwd=ROOT, text=True,
                capture_output=True,
                env=dict(os.environ, ASAN_OPTIONS="detect_leaks=0:halt_on_error=1", UBSAN_OPTIONS="halt_on_error=1"),
            )
            if result.stdout:
                print(f"{label}: {result.stdout.strip()}", flush=True)
            if result.stderr:
                print(result.stderr, end="", flush=True)
            result.check_returncode()
            runs.append({"mode": label, "result": "PASS", "seconds": round(time.monotonic() - started, 3),
                         "compiler": compile_command, "stdout": result.stdout, "stderr": result.stderr})
    assert all(sha(ROOT / name) == digest for name, digest in source_hashes.items())
    if candidate:
        assert all(sha(args.candidate / name) == digest for name, digest in candidate.items())
    report = {
        "result": "PASS", "suite": "gear-treasure-effective-host",
        "scope": "Production economy/runtime/menu/cache host assertions; synthetic prepared states from authenticated historical save; no native controller claim",
        "fixture": {"path": str(FIXTURE.relative_to(ROOT)), "sha256": FIXTURE_SHA,
                    "claimed_quests": [21, 24, 32, 40], "all_prepared_saves_validate": True},
        "matrix": {"later_combinations": 16, "old_relic_combinations": 8, "shop_states": 2,
                   "story_bases": [6, 8], "authored_loadouts": 4, "prepared_states": 2048,
                   "items": 48, "item_and_removal_commits": 196608, "selected_command_ids": 128,
                   "later_bit_cache_transitions": 1024},
        "synthetic_only_boundary": "Speed352 cap; fastest current authored gear plus Compass is350",
        "source_sha256": source_hashes, "candidate": candidate, "runs": runs,
    }
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2) + "\n")
        print(f"Report: {args.output}")


if __name__ == "__main__":
    main()
