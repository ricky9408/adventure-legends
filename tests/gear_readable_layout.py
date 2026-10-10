#!/usr/bin/env python3
"""Readable Gear prototype: independent raster, color, bounds and full-menu oracle."""
from pathlib import Path
import argparse
import hashlib
import json
import os
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
SOURCES = [
    "tests/gear_readable_layout_host.c",
    "src/ui.c",
    "src/gear_preview_text.c",
    "src/equipment_data.c",
    "src/assets.c",
]


def export_screenshots(directory):
    from PIL import Image, PngImagePlugin

    artifacts = []
    for source in sorted(directory.glob("synthetic-gear-*-native.ppm")):
        destination = source.with_suffix(".png")
        description = (
            "SYNTHETIC host-rendered production Gear menu at native 240x160. "
            "Real game labels, palette and built-in village background; preview values "
            "are test fixtures. This is not an emulator capture. 12.25 hearts is a "
            "formatter-only case; the current gameplay maximum remains 12 hearts."
        )
        metadata = PngImagePlugin.PngInfo()
        metadata.add_text("Description", description)
        with Image.open(source) as image:
            assert image.size == (240, 160)
            image.save(destination, pnginfo=metadata)
        artifacts.append({"path": str(destination), "width": 240, "height": 160})
        source.unlink()
        print(f"SYNTHETIC native-size screenshot: {destination}", flush=True)
    assert len(artifacts) == 2
    manifest = {
        "synthetic": True,
        "description": description,
        "fixtures": [
            {"hearts": ["12.25", "12.25"], "speed": ["100.0", "110.0"]},
            {"attack": [17, 71], "defense": [1, 7], "hearts": ["7.25", "11.25"],
             "speed": ["97.7", "101.7"], "recovery": ["1.77", "1.17"], "distance": [71, 117]},
        ],
        "production_source_sha256": {
            filename: hashlib.sha256((ROOT / filename).read_bytes()).hexdigest()
            for filename in ["src/gear_menu.c", "src/gear_preview_text.c", "src/ui.c"]
        },
        "artifacts": artifacts,
    }
    report = directory / "synthetic-gear-raster-report.json"
    report.write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"Synthetic provenance report: {report}", flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--screenshots", type=Path, help="write explicitly synthetic native-size menu PNGs")
    args = parser.parse_args()
    if args.screenshots:
        args.screenshots = args.screenshots.resolve()
        args.screenshots.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="gear-readable-layout-") as temporary:
        for label, flags in [
            ("strict", []),
            ("sanitized", ["-fsanitize=address,undefined", "-fno-omit-frame-pointer"]),
        ]:
            print(f"Readable Gear raster oracle: {label}", flush=True)
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
                [str(executable), *([str(args.screenshots)] if args.screenshots and label == "strict" else [])],
                cwd=ROOT, check=True,
                env=dict(os.environ, ASAN_OPTIONS="detect_leaks=0", UBSAN_OPTIONS="halt_on_error=1"),
            )

    if args.screenshots:
        export_screenshots(args.screenshots)


if __name__ == "__main__":
    main()
