# Game verification

The executable acceptance map is [`.trust/policy.json`](../.trust/policy.json).
It names user paths, expected behavior, check commands and required evidence.
The pinned shared runner is in `tools/trust/vendor/`; `run.py` verifies its hashes.

```sh
make test-trust-host
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
the host compiler. Full asset regeneration needs the pinned Pillow 13.0.0 Linux
environment and Noto/DejaVu fonts. On this Mac the adapter uses the prepared
`codex-pillow-compat:20261027` image by its resolved digest, with network pulls
disabled. `TRUST_LINUX_IMAGE` can select another prepared compatible image.

The existing broader campaign routes remain supplemental regression checks:

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
