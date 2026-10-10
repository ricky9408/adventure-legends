#!/usr/bin/env python3
"""Porchlight current-balance overlay against shipped C, strict and ASan/UBSan."""
from pathlib import Path
import os
import subprocess

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "build/gear-treasure-porchlight-host"
SOURCES = [
    "tests/gear_treasure_porchlight_native.c",
    "src/equipment.c", "src/equipment_data.c", "src/gear_runtime.c", "src/economy.c",
]


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for label, flags in [
        ("strict", []),
        ("sanitized", ["-fsanitize=address,undefined", "-fno-omit-frame-pointer"]),
    ]:
        executable = OUT / label
        subprocess.run([
            os.environ.get("HOST_CC", "cc"), "-std=c99", "-O1", "-g",
            "-Wall", "-Wextra", "-Werror", "-Wno-misleading-indentation", "-pedantic",
            "-ffunction-sections", "-fdata-sections", "-Wl,--gc-sections", "-Isrc",
            *flags, *SOURCES, "-o", str(executable),
        ], cwd=ROOT, check=True)
        print(f"{label}:", flush=True)
        subprocess.run([str(executable)], cwd=ROOT, check=True, env=dict(
            os.environ, ASAN_OPTIONS="detect_leaks=0", UBSAN_OPTIONS="halt_on_error=1"))


if __name__ == "__main__":
    main()
