#!/usr/bin/env python3
import concurrent.futures
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import time


ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
OUTPUT = ROOT / "build" / "trust-review" / "gameplay"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def execute(arguments, label, directory):
    result = subprocess.run(arguments, cwd=ROOT, text=True, capture_output=True, timeout=240)
    (directory / (label + ".stdout.log")).write_text(result.stdout)
    (directory / (label + ".stderr.log")).write_text(result.stderr)
    return result


def require_check_failure(result, condition):
    diagnostic = (re.escape(str(HERE / "gameplay_properties.c")) + r":\d+: " +
                  re.escape(condition) + r" \(room=-?\d+ px=-?\d+ py=-?\d+\)")
    if result.returncode != 1 or result.stdout or not re.fullmatch(diagnostic, result.stderr.strip()):
        raise AssertionError(f"Expected CHECK failure: {condition}; got {result.returncode}: {result.stderr}")


def main():
    OUTPUT.mkdir(parents=True, exist_ok=True)
    directory = Path(tempfile.mkdtemp(prefix="properties-", dir=OUTPUT)).resolve()
    sources = sorted((ROOT / "src").glob("*.c"))
    inputs = sorted(p for p in (ROOT / "src").rglob("*") if p.is_file())
    before = {str(p.relative_to(ROOT)): digest(p) for p in inputs}
    started = time.monotonic()
    compiler = os.environ.get("HOST_CC", "cc")
    flags = [compiler, "-std=c99", "-O1", "-g", "-fno-builtin", "-Wno-attributes",
             "-Wno-pointer-to-int-cast", "-Wno-int-to-pointer-cast", "-DSAVE4_HOST_TEST",
             "-DSAVE5_HOST_TEST", "-DGAME_HOST_TEST", "-Dmain=gba_main", "-I" + str(ROOT / "src"),
             "-fsanitize=undefined", "-fno-sanitize-recover=all"]
    if sys.platform == "darwin":
        flags.append("-Dsection(x)=unused")

    def compile_source(source, label, extras=()):
        destination = directory / (label + ".o")
        result = execute([*flags, *extras, "-c", str(source), "-o", str(destination)], "compile-" + label, directory)
        if result.returncode:
            raise AssertionError(f"Compilation failed for {source}: {result.stderr[-4000:]}")
        return destination

    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        futures = {source.stem: pool.submit(compile_source, source, source.stem) for source in sources}
        objects = {name: future.result() for name, future in futures.items()}
    driver = compile_source(HERE / "gameplay_properties.c", "gameplay-properties")

    def link(label, replacements=None, driver_object=None):
        replacements = replacements or {}
        executable = directory / label
        result = execute([compiler, "-fsanitize=undefined", *[str(replacements.get(name, obj)) for name, obj in objects.items()],
                          str(driver_object or driver), "-o", str(executable)], "link-" + label, directory)
        if result.returncode:
            raise AssertionError(f"Link failed: {result.stderr[-4000:]}")
        return executable

    executable = link("gameplay-properties")
    scenarios = {}
    for scenario in ("movement", "invalid_rooms", "geometry", "updates", "combat", "controls", "arrows"):
        result = execute([str(executable), scenario], scenario, directory)
        if result.returncode:
            raise AssertionError(f"{scenario} failed with {result.returncode}: {result.stderr[-4000:]}")
        scenarios[scenario] = json.loads(result.stdout)

    mutations = [
        ("diagonal_uses_previous_x", "game", "movement",
         "!solid(px,py)",
         "px=px_q8>>8;\n  if(!solid(px,ny>>8))py_q8=ny;",
         "if(!solid(px,ny>>8))py_q8=ny;\n  px=px_q8>>8;"),
        ("bonus_exceeds_weapon_contract", "gear_runtime", "combat",
         "stats.attack_q4>=attack&&stats.attack_q4<=EQUIPMENT_MAX_ATTACK_Q4",
         "attack>EQUIPMENT_MAX_ATTACK_Q4?EQUIPMENT_MAX_ATTACK_Q4:attack", "attack>32u?32u:attack"),
        ("arrow_skips_wall_pixels", "weapon_actions", "arrows",
         "!arrow.active&&scenario.hit==0",
         "step=remaining>256u?256u:remaining;", "step=remaining;"),
    ]
    rejected = {}
    for name, module, scenario, condition, old, new in mutations:
        source = (ROOT / "src" / (module + ".c")).read_text()
        if source.count(old) != 1:
            raise AssertionError(f"Mutation location changed: {name}; review this negative control")
        changed = directory / (name + ".c")
        changed.write_text(source.replace(old, new))
        replacement = compile_source(changed, name)
        mutant = link(name, {module: replacement})
        result = execute([str(mutant), scenario], "mutant-" + name, directory)
        require_check_failure(result, condition)
        rejected[name] = {"rejected": True, "scenario": scenario, "reason": result.stderr.strip()}

    source = (ROOT / "src" / "field_controls.h").read_text()
    old = "state->power_blocked=1;"
    if source.count(old) != 1:
        raise AssertionError("Chord-blocking mutation location changed")
    changed = directory / "controls-without-chord-ownership.h"
    changed.write_text(source.replace(old, "state->power_blocked=0;"))
    changed_driver = compile_source(HERE / "gameplay_properties.c", "controls-mutant-driver",
                                    ['-DGAMEPLAY_CONTROLS_HEADER="' + str(changed) + '"'])
    mutant = link("companion_chord_casts_power", driver_object=changed_driver)
    result = execute([str(mutant), "controls"], "mutant-companion_chord_casts_power", directory)
    require_check_failure(result, "!!(actual.power_held&256u)==(!!(buttons&1u)&&!blocked)")
    rejected["companion_chord_casts_power"] = {"rejected": True, "scenario": "controls", "reason": result.stderr.strip()}
    after = {str(p.relative_to(ROOT)): digest(p) for p in inputs}
    if before != after:
        raise AssertionError("Production sources changed during verification; rerun against a stable workspace")
    report = {
        "passed": True,
        "scope": "Host execution of all production C translation units; synthetic geometry and combat states",
        "not_a_controller_walkthrough": True,
        "not_hardware_timing_evidence": True,
        "compiler": subprocess.check_output([compiler, "--version"], text=True).splitlines()[0],
        "sanitizers": ["undefined"],
        "darwin_section_placement_removed_for_host": sys.platform == "darwin",
        "compiled_translation_units": len(sources),
        "scenarios": scenarios,
        "negative_controls": rejected,
        "source_sha256": before,
        "harness_sha256": {str(p.relative_to(ROOT)): digest(p) for p in (Path(__file__), HERE / "gameplay_properties.c")},
        "elapsed_seconds": round(time.monotonic() - started, 3),
        "local_logs": str(directory),
    }
    (OUTPUT / "gameplay-results.json").write_text(json.dumps(report, indent=2) + "\n")
    if os.environ.get("TRUST_EVIDENCE_DIR"):
        (Path(os.environ["TRUST_EVIDENCE_DIR"]) / "gameplay-results.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({key: value for key, value in report.items() if key not in ("source_sha256", "harness_sha256")}, indent=2))


if __name__ == "__main__":
    main()
