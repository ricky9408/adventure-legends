#!/bin/sh
set -eu
BASE=${BASELINE_ROOT:?Set BASELINE_ROOT to the historical Connected Roads checkout}
OUT=${1:?new evidence output path required}
shift
python tests/journey_guidance_earned.py \
 --rom "$BASE/build/connected-roads-c4/emberbond.gba" \
 --symbols "$BASE/build/connected-roads-c4/emberbond.sym" \
 --bridge "$BASE/build/connected-roads-campaign-c4/bridge.so" \
 --source-root "$BASE" --source-manifest "$BASE/build/connected-roads-c4/source-hashes.json" \
 --expected-rom-sha 3f4855b03a08b638c40c21274b858dfca18f2988f9f38deb15c35315bdba7423 \
 --expected-symbols-sha 9c7a93652a792f0c014c8fe6b0d391bfeca8eadd4cfe05f1822f1bf2db53167b \
 --expected-elf-sha "$(sha256sum "$BASE/build/connected-roads-c4/emberbond.elf" | cut -d' ' -f1)" \
 --output "$OUT" --baseline "$@"
