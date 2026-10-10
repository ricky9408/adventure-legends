#!/usr/bin/env python3
"""Actual Gear menu/runtime differential, strict and ASan/UBSan host builds."""
from pathlib import Path
import os
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
SOURCES = [
    "tests/gear_preview_effective_host.c",
    "src/gear_preview.c",
    "src/gear_runtime.c",
    "src/weapon_actions.c",
    "src/companion_guide.c",
    "src/creatures.c",
    "src/creature_data.c",
    "src/economy.c",
    "src/equipment.c",
    "src/equipment_data.c",
]


def main():
    with tempfile.TemporaryDirectory(prefix="gear-preview-host-") as temporary:
        for label, flags in [
            ("strict", []),
            ("sanitized", ["-fsanitize=address,undefined", "-fno-omit-frame-pointer"]),
        ]:
            executable = Path(temporary) / label
            subprocess.run(
                [
                    os.environ.get("HOST_CC", "cc"), "-std=c99", "-O1", "-g",
                    "-Wall", "-Wextra", "-Werror", "-Wno-misleading-indentation",
                    "-ffunction-sections", "-fdata-sections", "-Wl,--gc-sections",
                    "-Isrc", *flags, *SOURCES, "-o", str(executable),
                ],
                cwd=ROOT, check=True,
            )
            subprocess.run(
                [str(executable)], cwd=ROOT, check=True,
                env=dict(os.environ, ASAN_OPTIONS="detect_leaks=0", UBSAN_OPTIONS="halt_on_error=1"),
            )


if __name__ == "__main__":
    main()
