# Automatic gameplay regression and debugging

`.github/workflows/gameplay.yml` runs on pull requests, pushes to `main`, and
manual **Actions → Gameplay regression → Run workflow** requests. Host and native
lanes run independently. An optional manual checkbox adds exhaustive two-loop
regional audio diagnostics. An older run of the same PR/ref is cancelled when a
new commit arrives. Jobs have a 60-minute ceiling with separately bounded setup/upload steps and a
35-minute regression budget (leaving time to upload failure evidence); each build/test subprocess
also has a bounded timeout and its entire process group is stopped on timeout.

This is a focused regression gate, not proof that every campaign route, boss,
companion combination, or physical GBA works. Existing historical acceptance
contracts remain pinned and separate from current runtime evidence.

## Coverage

- **Both lanes:** two clean builds of the selected commit, requiring identical
  ROM, ELF, symbol, map and runtime source-manifest hashes; native bridge build;
  CI runner negative/timeout tests. No generated art/music is changed.
- **Host:** the current `make test` aggregate, including retained save/migration,
  interrupted-write, equipment, quest, geometry, UI and current C audio
  sanitizer tests. Historical inverse checks keep their existing hashes and
  labels. Host/source assertions are not native gameplay evidence.
- **Native controller route:** blank-cartridge opening, dialogue, pause, sword,
  companion, village-to-grove transition and native audio. Every measured frame
  must advance and present within the GBA budget, with no core/audio faults.
  Lossless video is independently decoded and audio/video synchronization checked.
- **Fresh early gameplay:** first boss, merchant confirmation/cancellation,
  held-button purchase safety, item use, three optional Fire requests, an earned
  evolution with cancel/accept, equipment preview and same-run earned-save
  Continue. No historical progress, game RAM writes or machine-state imports.
- **Fresh garden reward:** a separate empty-SRAM original-chapter route earns
  access to Reedhaven, walks the three garden stones in order, claims exactly
  one Surestep Boots, previews/equips it with Left/Right and A, verifies its
  actual three-update power-cooldown benefit, then cold Continues and revisits
  the reward twice without duplication. Prefix and garden reports, inputs,
  screenshots and authenticated earned SRAM are retained together. This proves
  this optional quest/reward route, not full collection.
- **Save/load:** opening held buttons, all eight skip/interruption points,
  repository-pinned older-save compatibility and power cuts at every frame of
  first-checkpoint publication. Current help/goal/companion browsing and seeded
  hub navigation must leave both Save5 and the cartridge save unchanged.
- **Separate synthetic diagnostics:** all-room audio-routing/fade assertions.
  The optional long run checks two exact loops for every regional cue. These
  intentionally prepared room states do not establish earned region access.

Known inherited cold-Continue stalls are measured under `cold_continue_observed`
and shown in the summary. A green opening/save result proves persistence and
opening cadence; it does **not** mean the synchronous load path is smooth. See
that report before interpreting a green check as whole-game performance approval.

## Reproduce locally

Use Linux x86_64 with the dependencies in `tools/README.md`, plus NumPy, SciPy
and FFmpeg. The UI/art checks also require Debian `fonts-noto-cjk` and
`fonts-dejavu-core` (NotoSansCJK-Bold.ttc and DejaVuSans.ttf at their standard
`/usr/share/fonts` paths). The preflight loads both fonts before building.
Pixel regeneration requires **Pillow 12.3.0**: Debian's Pillow 11.1
changes Covenant polygon rasterization and is deliberately rejected before the
aggregate can change generated pixels. `tools/install_tools.sh` extracts the existing checksum-pinned
Debian ARM GCC 14.2.1/binutils 2.44/mGBA 0.10.5 packages into `tools/sysroot`.
It does not install their host runtime dependencies. The runner itself never
installs software or edits system settings.

```sh
sh tools/install_tools.sh
python3 tools/run_gameplay_ci.py --suite all --output build/ci-local
# Independently reproduce one Actions lane:
python3 tools/run_gameplay_ci.py --suite host --output build/ci-host-retry
python3 tools/run_gameplay_ci.py --suite native --seed 9408 --output build/ci-native-retry
# Optional exhaustive synthetic audio diagnostics:
python3 tools/run_gameplay_ci.py --suite native --extended-audio --output build/ci-audio-long
```

Choose a new output directory each time; evidence is never overwritten. This
runs `make clean`, so don't run it concurrently with another build/test against
the same checkout. Keep Python assertions enabled: `-O`/`PYTHONOPTIMIZE` is rejected.
The seed controls only the new bounded hub navigation; established routes use
fixed frame/button sequences. No time-based/randomized gameplay fixture is used.

For the closest hosted match, use the official Debian image digest in the
workflow and its signed `20250910T000000Z` package snapshot, then execute the
same setup commands. Debian supplies Python 3.13, NumPy 2.2.4 and SciPy 1.15.3.
CI creates an isolated venv with those system packages, then installs only the
hash-pinned official Pillow 12.3.0 CPython 3.13/manylinux x86_64 wheel from PyPI.
The requirements file intentionally rejects other wheel builds/interpreters.
On a prepared Debian 13 host with `python3-venv` installed:

```sh
python3 -m venv --system-site-packages build/ci-venv
build/ci-venv/bin/python -m pip install --no-deps --require-hashes \
  --only-binary=:all: --index-url https://pypi.org/simple -r tools/ci-requirements.txt
export PATH="$PWD/build/ci-venv/bin:$PATH"
python3 tools/run_gameplay_ci.py --suite all --output build/ci-debian
```

No system Python package is replaced. The Git commit metadata command trusts
only this known checkout for that one invocation (`git -c safe.directory=…`),
which handles container mount ownership without global or wildcard trust.
 That older snapshot is a reproducibility pin, not an
assertion that it contains current security updates. Update image/snapshot/tool
pins in a reviewed PR and rerun both lanes. The ARM/mGBA package downloads have
independent SHA-256 checks in the existing installer. Action references are
immutable commits from the official `actions/checkout` and
`actions/upload-artifact` release repositories. No mutable third-party action,
secret, persistent Git credential, elevated token, or `pull_request_target` is
used. Dependency versions and the exact candidate are recorded in each artifact.

## Debug a failure

1. Open the failed Actions lane and download its `gameplay-host-…` or
   `gameplay-native-…` artifact (seven-day retention). `summary.json` names the
   failed command, exit code, timeout and log. Setup failures before the runner
   starts are in the Actions setup log and may have no artifact.
2. Check out that run's exact commit. Use the recorded candidate hashes and
   tool versions. `candidate/` contains the ROM, ELF, symbols, map and source
   manifest, so an emulator debugger can use the exact binary.
3. Rerun the lane with the same `--seed` and a fresh output directory. For a
   focused retry, copy the command from `summary.json` and change only its
   output directory; prerequisite paths must still refer to the same run.
4. Inspect `controllers/regional-gameplay.mp4`, its lossless master and native
   WAV, PNGs, input records, compressed per-frame traces and `failure.png` when
   captured. Opening failures preserve session inputs and the test cartridge
   save. Fresh-early reports include snapshots and same-run earned saves.
5. `opening/skip-0-village.sav` is generated by this candidate, not personal
   progress. To replay the menu gate directly:

```sh
python3 tests/opening_skip_guides_native.py \
  --bridge build/ci-native-retry/controllers/native-bridge.so \
  --save build/ci-native-retry/opening/skip-0-village.sav \
  --seed 9408 --output build/menu-debug
```

A failed assertion, missing dependency, timed-out command, unfinished route or
failed aggregate cannot be converted into a green result by the wrapper. Forced
runner termination can leave a stage marked `RUNNING`; that is incomplete
verification. Ordinary assertion failures retain structured diagnostics. A hard
kill can only retain files already flushed before termination.

Artifacts are restricted to fresh generated test directories, candidate build
files, repository-owned fixtures and their test derivatives. No home directory,
whole workspace, credential dump, personal save, external BIOS, or unrelated
file is uploaded. Treat CI artifacts as public-safe development data.

### Reproduce the fresh garden scenario

After the native CI lane builds its controller bridge, run the standalone
empty-SRAM scenario with a new output directory:

```sh
python3 tests/fresh_garden_reward.py --output build/garden-replay \
  --bridge build/ci-native-retry/controllers/native-bridge.so
```

CI always uses this standalone route. The helper also supports explicitly
hash-bound, same-candidate earned prefix evidence for focused local diagnosis;
see `--help`. The summary keeps original-prefix and garden metrics separate.
Their `max_cycles` includes cold Continue; active journey miss/overrun counters
are the smooth-gameplay gate, and no whole-load performance claim is made.
