# Game verification

The executable acceptance map is [`.trust/policy.json`](../.trust/policy.json).
It names user paths, expected behavior, check commands and required evidence.
The pinned shared runner is in `tools/trust/vendor/`; `run.py` verifies its hashes.

```sh
make test-trust-host
```

`test-trust-host` is partial local feedback, not full acceptance. Inside the
prepared Linux verification environment, run:

```sh
make test
python3 tools/trust/run.py gate --root . --receipt /printed/path/receipt.json
```

The full run performs source/build inventory checks, negative controls, two clean
ARM builds, independent gameplay and persistence properties, native mGBA scenarios,
and disposable asset regeneration. Missing tools or artifacts fail the run.
Source edits invalidate its receipt. Outputs live in `.trust/runs/`.

Local requirements: Python 3.11+, Git, a C compiler with ASan/UBSan, ARM GCC and
mGBA development headers. `ARM_PREFIX` or `DEVKITARM` selects the ARM toolchain;
the local adapter also recognizes `/opt/devkitpro/devkitARM`. `HOST_CC` selects
the host compiler. Full asset regeneration requires Pillow 13.0.0, zlib 1.3.1,
`/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc` and
`/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf` in the current runtime.
The prepared `codex-pillow-compat:20261027` Linux image supplies these through
`/opt/pillow13/bin/python`; select that Python on `PATH` before `make test`.
GitHub prepares the same requirements through the pinned workflow dependencies.
The adapter fails if these requirements are absent. It does not launch Docker:
the container or CI job owner controls that external lifecycle, while the runner
owns process groups inside the verification environment.

The existing broader campaign routes remain supplemental regression checks.
The empty-SRAM Mina and Edda routes check their optional A cues before and
after the original reward, beside the resident whose conversation takes
priority, on a return visit, and after saved cold Continue. Their OAM, input,
SRAM and frame records remain scoped to those earned routes.

Run the broader lanes separately:

```sh
python3 tools/run_gameplay_ci.py --suite host --output build/ci-host-new
python3 tools/run_gameplay_ci.py --suite native --output build/ci-native-new
```

Those routes require the Linux dependencies in `.github/workflows/gameplay.yml`.
They rebuild `build/emberbond.*`; run them sequentially in a stable checkout.
Their reports distinguish controller-earned progress, synthetic states and
historical fixtures. Historical byte-identity assertions are not current
gameplay acceptance. Archived fixture hashes remain unchanged.

GitHub runs independent contracts in the host lane and broad host/native routes
in separate jobs. Logs and captures upload even after failure. This does not
configure branch protection or grant merge authority.

Native emulator results do not establish physical-cartridge behavior, every
optional route, or full companion collection. Host properties and a passing
manifest do not establish those either. Read each report's measured scope.
