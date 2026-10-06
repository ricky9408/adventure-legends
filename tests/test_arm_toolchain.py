#!/usr/bin/env python3
"""Deterministic tool-discovery unit tests; no compiler or emulator is run."""
import os
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from arm_toolchain import ArmToolchainError, resolve_arm_tools


class ArmToolchainTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='southern-arm-lookup-')
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.path = self.root / 'installed-bin'
        self.path.mkdir()
        self.env = {'PATH': str(self.path)}
        self.local = str(self.root / 'tools/sysroot/usr/bin/arm-none-eabi-')
        self.installed = str(self.path / 'arm-none-eabi-')

    def make_tools(self, prefix, names=('gcc', 'nm', 'objcopy')):
        result = {}
        for name in names:
            path = Path(prefix + name)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text('#!/bin/sh\nexit 0\n')
            path.chmod(0o755)
            result[name] = str(path)
        return result

    def resolve(self, *names):
        return resolve_arm_tools(*(names or ('gcc', 'nm', 'objcopy')),
                                 root=self.root, environ=self.env)

    def test_explicit_prefix_precedes_devkitarm_local_and_path(self):
        self.make_tools(self.local)
        self.make_tools(self.installed)
        devkit = self.root / 'devkitARM'
        self.make_tools(str(devkit / 'bin/arm-none-eabi-'))
        prefix = str(self.root / 'selected' / 'cross-')
        expected = self.make_tools(prefix)
        self.env.update(ARM_PREFIX=prefix, DEVKITARM=str(devkit))
        self.assertEqual(self.resolve(), expected)

    def test_explicit_command_prefix_resolves_via_path(self):
        expected = self.make_tools(str(self.path / 'chosen-arm-'))
        self.env['ARM_PREFIX'] = 'chosen-arm-'
        self.assertEqual(self.resolve(), expected)

    def test_explicit_relative_prefix_resolves_from_caller_directory(self):
        prefix = str(self.root / 'relative' / 'arm-none-eabi-')
        expected = self.make_tools(prefix)
        self.env['ARM_PREFIX'] = os.path.relpath(prefix)
        self.assertEqual(self.resolve(), expected)

    def test_devkitarm_precedes_local_and_path_and_accepts_spaces(self):
        self.make_tools(self.local)
        self.make_tools(self.installed)
        devkit = self.root / 'devkit ARM'
        expected = self.make_tools(str(devkit / 'bin/arm-none-eabi-'))
        self.env['DEVKITARM'] = str(devkit)
        self.assertEqual(self.resolve(), expected)

    def test_local_precedes_path_when_its_gcc_exists_like_makefile(self):
        expected = self.make_tools(self.local)
        self.make_tools(self.installed)
        self.assertEqual(self.resolve(), expected)

    def test_standard_installed_tools_when_local_gcc_is_absent(self):
        expected = self.make_tools(self.installed)
        self.assertEqual(self.resolve(), expected)

    def test_local_objcopy_without_local_gcc_does_not_select_local(self):
        self.make_tools(self.local, ('objcopy',))
        expected = self.make_tools(self.installed, ('objcopy',))
        self.assertEqual(self.resolve('objcopy'), expected)

    def test_empty_devkitarm_is_unset_like_makefile(self):
        expected = self.make_tools(self.installed)
        for value in ('', '  '):
            with self.subTest(value=value):
                self.env['DEVKITARM'] = value
                self.assertEqual(self.resolve(), expected)

    def test_explicit_missing_prefix_never_falls_back(self):
        self.make_tools(self.local)
        self.make_tools(self.installed)
        self.env['ARM_PREFIX'] = str(self.root / 'missing/arm-none-eabi-')
        with self.assertRaisesRegex(ArmToolchainError, 'selected by ARM_PREFIX='):
            self.resolve()

    def test_explicit_missing_devkitarm_never_falls_back(self):
        self.make_tools(self.local)
        self.make_tools(self.installed)
        self.env['DEVKITARM'] = str(self.root / 'missing-devkit')
        with self.assertRaisesRegex(ArmToolchainError, 'selected by DEVKITARM='):
            self.resolve()

    def test_explicit_empty_prefix_never_selects_native_host_tools(self):
        self.make_tools(self.installed)
        for value in ('', '  '):
            with self.subTest(value=value):
                self.env['ARM_PREFIX'] = value
                with self.assertRaisesRegex(ArmToolchainError, 'ARM_PREFIX is empty'):
                    self.resolve()

    def test_incomplete_explicit_toolchain_never_mixes_with_path(self):
        self.make_tools(self.installed)
        prefix = str(self.root / 'incomplete/arm-none-eabi-')
        self.make_tools(prefix, ('gcc',))
        self.env['ARM_PREFIX'] = prefix
        with self.assertRaisesRegex(ArmToolchainError, 'nm.*no alternate toolchain was used'):
            self.resolve()

    def test_incomplete_local_toolchain_never_mixes_with_path(self):
        self.make_tools(self.installed)
        self.make_tools(self.local, ('gcc',))
        with self.assertRaisesRegex(ArmToolchainError, 'objcopy.*repository tools/sysroot'):
            self.resolve('objcopy')

    def test_nonexecutable_explicit_tool_is_rejected(self):
        prefix = str(self.root / 'nonexecutable/arm-none-eabi-')
        self.make_tools(prefix)
        Path(prefix + 'gcc').chmod(0o644)
        self.env['ARM_PREFIX'] = prefix
        with self.assertRaisesRegex(ArmToolchainError, 'missing or not executable'):
            self.resolve()

    def test_missing_path_tools_give_actionable_error(self):
        with self.assertRaisesRegex(ArmToolchainError, 'standard arm-none-eabi toolchain on PATH'):
            self.resolve()

    def test_tool_symlink_invocation_path_is_preserved(self):
        actual = self.make_tools(str(self.root / 'actual/arm-none-eabi-'), ('gcc',))
        link = self.path / 'arm-none-eabi-gcc'
        link.symlink_to(actual['gcc'])
        self.assertEqual(self.resolve('gcc'), {'gcc': str(link)})


if __name__ == '__main__':
    unittest.main(verbosity=2)
