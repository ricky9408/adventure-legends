"""Resolve Southern QA ARM tools using the game's Makefile selection order.

ARM_PREFIX overrides DEVKITARM, followed by the repository's extracted official
toolchain when its GCC exists, otherwise arm-none-eabi-* on PATH. Select one
prefix for the whole request; a broken selected toolchain must never silently
fall back to a different compiler or mix binutils from different prefixes.
"""
from __future__ import annotations

import os
from pathlib import Path
import shutil
from typing import Mapping


class ArmToolchainError(RuntimeError):
    """The selected ARM toolchain cannot provide a requested executable."""


def resolve_arm_tools(*names: str, root: Path | None = None,
                      environ: Mapping[str, str] | None = None) -> dict[str, str]:
    """Return absolute executable paths, without running or installing tools.

    Relative ARM_PREFIX/DEVKITARM paths are relative to the caller's working
    directory, just as Makefile/subprocess commands are. Explicit empty
    ARM_PREFIX is rejected instead of accidentally selecting native host tools.
    Empty DEVKITARM is ignored, as in the Makefile. ``environ`` exists so tests
    can supply a fully isolated PATH rather than relying on the test machine.
    """
    env = os.environ if environ is None else environ
    root = Path(__file__).resolve().parents[1] if root is None else Path(root)
    local_prefix = str(root.resolve() / 'tools/sysroot/usr/bin/arm-none-eabi-')
    if 'ARM_PREFIX' in env:
        prefix = env['ARM_PREFIX']
        source = f'ARM_PREFIX={prefix!r}'
        if not prefix.strip():
            raise ArmToolchainError('ARM_PREFIX is empty; set an ARM tool prefix or unset it')
    elif env.get('DEVKITARM', '').strip():
        prefix = str(Path(env['DEVKITARM']) / 'bin/arm-none-eabi-')
        source = f'DEVKITARM={env["DEVKITARM"]!r}'
    elif Path(local_prefix + 'gcc').exists():
        prefix = local_prefix
        source = 'repository tools/sysroot (selected because its ARM GCC exists)'
    else:
        prefix = 'arm-none-eabi-'
        source = 'standard arm-none-eabi toolchain on PATH'

    result = {}
    for name in names:
        command = prefix + name
        found = shutil.which(command, path=env.get('PATH', os.defpath))
        if found is None:
            raise ArmToolchainError(
                f'ARM tool {command!r} is missing or not executable; selected by {source}. '
                'Fix that toolchain or explicitly select ARM_PREFIX/DEVKITARM; '
                'no alternate toolchain was used.'
            )
        # Keep symlinks intact: compiler drivers may use their invocation path
        # to locate support files in a relocatable toolchain.
        result[name] = os.path.abspath(found)
    return result
