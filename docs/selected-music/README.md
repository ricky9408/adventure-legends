# Owner-selected soundtrack integration

The selected catalog records the owner's final whole-soundtrack choice. The
large C include diff is generated PCM. Reviewer entry points are the selected
catalog/provenance, generator, PSG pitch table and verification summary.

`contract.json` pins the full current production file set and permits only
music input/data and music-credit production changes from the previous main
commit. Non-music runtime, all78room routing, license and historical proofs
remain exact. `parent-inverse.json.gz` contains the replaced previous-main
files (predominantly old PCM includes) so historical tests can still run on
an exact previous-main source tree. It contains source bytes, not build tools
or emulator states. It is separate from the existing historical contracts.

`tests/selected_music_boundary.py` authenticates the current file inventory
and mutation controls before any historical reconstruction. Current geometry
runs on current source; old renderer/UI proofs run only in the authenticated
parent tree. Host aggregates use that boundary to detect producer mutations.
Current actual-C and native transport tests use the newly selected data.

The verification summary contains reproducible build hashes and focused host
and mGBA outcomes. Large native captures and frame traces remain local. The
full gameplay CI is a separate required PR review signal; this document does
not substitute historical proof results for current campaign acceptance.
