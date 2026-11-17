import importlib.util
import contextlib
import io
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import time
import unittest
from unittest import mock
from types import SimpleNamespace


ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location('trust_contracts', ROOT / 'tools/trust/contracts.py')
contracts = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(contracts)
ASSET_SPEC = importlib.util.spec_from_file_location('trust_assets', ROOT / 'tools/trust/assets.py')
assets = importlib.util.module_from_spec(ASSET_SPEC)
ASSET_SPEC.loader.exec_module(assets)


class ContractMutationTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='trust-contract-')
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        subprocess.run(['git', 'init', '--quiet', str(self.root)], check=True)
        self.put('src/main.c', '#include "api.h"\nint main(void) { return value; }\n')
        self.put('src/api.h', '#include "example_data/part_000.inc"\n')
        self.put('src/example_data/part_000.inc', 'static const int value = 0;\n')
        self.put('linker.ld', 'SECTIONS {}\n')
        self.put('Makefile', 'BUILD := build\nOBJECTS := $(BUILD)/main.o\n')
        self.put('tests/test_sample.py', 'import unittest\n')
        self.put('tools/run_sample.py', 'print("sample")\n')
        self.put('tests/fixtures/old/source.c', 'historical fixture\n')
        self.put('.gitignore', 'build/\n__pycache__/\n')
        contracts.write_catalog(self.root)

    def put(self, name, contents):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(contents)
        return path

    def test_inventory_accounts_for_source_generated_data_and_historical_fixtures(self):
        result = contracts.inventory(self.root)
        rows = {row['path']: row for row in result['files']}
        self.assertEqual(result['build']['translation_units'], ['src/main.c'])
        self.assertEqual(rows['src/main.c']['role'], 'production-source')
        self.assertEqual(rows['src/example_data/part_000.inc']['role'], 'generated-production-data')
        self.assertEqual(rows['tests/fixtures/old/source.c']['role'], 'historical-fixture')
        self.assertEqual(set(rows), set(contracts.visible_paths(self.root)))

    def test_policy_routes_exclude_unreferenced_test_namespace_members(self):
        self.put('.trust/policy.json', json.dumps({'checks': [{'command': ['python3', 'tools/trust/check.py']}]}))
        graph = {'tools/trust/check.py': ['tests/trust/test_used.py'],
                 'tests/trust/test_used.py': [], 'tests/trust/test_unused.py': [],
                 'tools/run_equipment_rewards_host.py': []}
        routes = contracts.reference_routes(self.root, graph)
        self.assertIn('policy_command_references', routes['tests/trust/test_used.py'])
        self.assertNotIn('policy_command_references', routes['tests/trust/test_unused.py'])
        self.assertEqual(['supplemental_host_references'], routes['tools/run_equipment_rewards_host.py'])

    def test_unlinked_production_translation_unit_is_rejected(self):
        self.put('src/unaccounted.c', 'int forgotten(void) { return 1; }\n')
        with self.assertRaisesRegex(contracts.ContractError, 'missing from build'):
            contracts.source_graph(self.root)

    def test_new_generated_fragment_must_be_reachable(self):
        self.put('src/example_data/part_001.inc', 'static const int hidden = 1;\n')
        with self.assertRaisesRegex(contracts.ContractError, 'unreachable'):
            contracts.source_graph(self.root)

    def test_dangling_include_is_rejected(self):
        self.put('src/main.c', '#include "missing.h"\n')
        with self.assertRaisesRegex(contracts.ContractError, 'Unresolved'):
            contracts.source_graph(self.root)

    def test_host_test_header_requires_its_exact_preprocessor_guard(self):
        self.put('tests/test_region_game.py', 'generate_host_test_header = True\n')
        with (self.root / 'src/main.c').open('a') as stream:
            stream.write('#include "region_game_test_ui.h"\n')
        with self.assertRaisesRegex(contracts.ContractError, 'unguarded'):
            contracts.source_graph(self.root)
        self.put('src/main.c', '#include "api.h"\n#ifdef REGION_GAME_HOST_TEST\n#include "region_game_test_ui.h"\n#endif\n')
        contracts.source_graph(self.root)

    def test_production_cannot_include_test_implementation(self):
        with (self.root / 'src/main.c').open('a') as stream:
            stream.write('#include "../tests/fixtures/old/source.c"\n')
        with self.assertRaisesRegex(contracts.ContractError, 'escapes src'):
            contracts.source_graph(self.root)

    def test_duplicate_build_object_is_rejected(self):
        self.put('Makefile', 'OBJECTS := $(BUILD)/main.o $(BUILD)/main.o\n')
        with self.assertRaisesRegex(contracts.ContractError, 'Duplicate'):
            contracts.build_units(self.root)

    def test_unregistered_nested_checker_is_rejected(self):
        self.put('tests/new_group/test_unreviewed.py', 'raise SystemExit(0)\n')
        with self.assertRaisesRegex(contracts.ContractError, 'unreviewed'):
            contracts.validate_catalog(self.root)

    def test_deleted_registered_checker_is_rejected(self):
        (self.root / 'tests/test_sample.py').unlink()
        with self.assertRaisesRegex(contracts.ContractError, 'missing'):
            contracts.validate_catalog(self.root)

    def test_freshness_rejects_new_changed_and_deleted_source(self):
        before = contracts.runtime_snapshot(self.root)
        added = self.put('src/added.h', 'int added;\n')
        with self.assertRaisesRegex(contracts.ContractError, 'added'):
            contracts.require_unchanged(before, contracts.runtime_snapshot(self.root))
        added.unlink()
        self.put('src/main.c', 'int main(void) { return 7; }\n')
        with self.assertRaisesRegex(contracts.ContractError, 'changed'):
            contracts.require_unchanged(before, contracts.runtime_snapshot(self.root))
        (self.root / 'src/api.h').unlink()
        with self.assertRaisesRegex(contracts.ContractError, 'removed'):
            contracts.require_unchanged(before, contracts.runtime_snapshot(self.root))

    def test_freshness_covers_recursive_helpers_and_build_configuration(self):
        helper = self.put('tools/nested/observe.py', 'print(1)\n')
        design = self.put('docs/design/thresholds.json', '{"limit": 4}\n')
        before = contracts.input_snapshot(self.root)
        helper.write_text('print(2)\n')
        design.write_text('{"limit": 5}\n')
        self.put('Makefile', 'OBJECTS := $(BUILD)/other.o\n')
        delta = contracts.snapshot_delta(before, contracts.input_snapshot(self.root))
        self.assertEqual(delta['changed'], ['Makefile', 'docs/design/thresholds.json', 'tools/nested/observe.py'])

    def test_build_output_is_not_a_source_change(self):
        before = contracts.input_snapshot(self.root)
        self.put('build/evidence.json', '{"passed": true}\n')
        contracts.require_unchanged(before, contracts.input_snapshot(self.root))

    def test_generated_report_cannot_be_added_to_reviewed_documentation(self):
        before = contracts.input_snapshot(self.root)
        self.put('docs/evidence/powerloss.json', '{"passed": true}\n')
        with self.assertRaisesRegex(contracts.ContractError, 'docs/evidence/powerloss.json'):
            contracts.require_unchanged(before, contracts.input_snapshot(self.root))

    def test_runtime_symlink_is_rejected(self):
        (self.root / 'src/link.h').symlink_to(self.root / 'src/api.h')
        with self.assertRaisesRegex(contracts.ContractError, 'symlinks'):
            contracts.runtime_snapshot(self.root)

    def test_uncompiled_runtime_file_is_rejected(self):
        self.put('src/instructions.txt', 'trust me\n')
        with self.assertRaisesRegex(contracts.ContractError, 'Uncompiled'):
            contracts.runtime_snapshot(self.root)

    def test_optimized_python_cannot_disable_contract_checks(self):
        self.put('src/unlinked.c', 'int lost;\n')
        result = subprocess.run(
            [sys.executable, '-O', str(ROOT / 'tools/trust/contracts.py'), '--root', str(self.root)],
            capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn('missing from build', result.stderr)

    def test_changed_generated_pixels_and_extra_chunks_are_rejected(self):
        with tempfile.TemporaryDirectory(prefix='trust-generated-') as directory:
            generated = Path(directory)
            for name in (*assets.OUTPUTS, 'src/asset_data/part_000.inc'):
                self.put(name, 'const unsigned char pixel = 7;\n')
                target = generated / name
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes((self.root / name).read_bytes())
            assets.compare_generated(self.root, generated)
            target = generated / 'src/asset_data/part_000.inc'
            target.write_text('const unsigned char pixel = 8;\n')
            with self.assertRaisesRegex(ValueError, 'Generated source differs'):
                assets.compare_generated(self.root, generated)
            target.write_bytes((self.root / 'src/asset_data/part_000.inc').read_bytes())
            (generated / 'src/asset_data/part_001.inc').write_text('unexpected chunk\n')
            with self.assertRaisesRegex(ValueError, 'file set differs'):
                assets.compare_generated(self.root, generated)

    def test_current_host_routes_disclose_historical_replacements(self):
        self.put('build/source-hashes.json', '{}')
        self.put('tools/run_player_feedback_host.py', (ROOT / 'tools/run_player_feedback_host.py').read_text())
        for filename, extra, expected_retired in (
                ('run_equipment_rewards_host.py', [], 5),
                ('run_connected_roads_host.py', ['--field-controls-successor'], 2)):
            with self.subTest(runner=filename):
                spec = importlib.util.spec_from_file_location('selected_host', ROOT / 'tools' / filename)
                runner = importlib.util.module_from_spec(spec)
                with mock.patch.object(sys, 'path', [str(ROOT / 'tools'), *sys.path]):
                    spec.loader.exec_module(runner)
                runner.ROOT = self.root
                output = self.root / filename.removesuffix('.py')
                commands = []
                def run(command, **kwargs):
                    commands.append(command)
                    return SimpleNamespace(returncode=0)
                with mock.patch.object(sys, 'argv', [filename, '--output', str(output), *extra]), \
                        mock.patch.object(runner, 'sha', return_value='0' * 64), \
                        mock.patch.object(runner, 'ProductionGuard', return_value=SimpleNamespace(error=lambda: None)), \
                        mock.patch.object(runner.subprocess, 'run', side_effect=run), \
                        contextlib.redirect_stdout(io.StringIO()):
                    self.assertEqual(runner.main(), 0)
                report_name = 'report.json' if filename.startswith('run_equipment') else 'run-status.json'
                report = json.loads((output / report_name).read_text())
                self.assertEqual(len(report['retired_historical_contracts']), expected_retired)
                self.assertTrue(all(row['reason'] for row in report['retired_historical_contracts']))
                self.assertFalse(any('tests/field_controls_boundary.py' in command for command in commands))
                expected = 'tests/trust/test_contracts.py' if expected_retired == 5 else 'tests/trust/test_asset_geometry.py'
                self.assertTrue(any(expected in command for command in commands))


class GeneratorLifecycleTests(unittest.TestCase):
    def test_generator_exit_and_timeout_leave_no_running_descendant(self):
        for outcome in ('success', 'failure', 'timeout'):
            with self.subTest(outcome=outcome), tempfile.TemporaryDirectory(prefix='trust-generator-') as directory:
                root = Path(directory)
                child = root / 'child.py'
                child.write_text('import os, pathlib, time\npathlib.Path("child.pid").write_text(str(os.getpid()))\ntime.sleep(30)\n')
                driver = root / 'driver.py'
                driver.write_text(
                    'import pathlib, subprocess, sys, time\n'
                    'subprocess.Popen([sys.executable, "child.py"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)\n'
                    'while not pathlib.Path("child.pid").exists(): time.sleep(0.01)\n'
                    'if sys.argv[1] == "timeout": time.sleep(30)\n'
                    'raise SystemExit(7 if sys.argv[1] == "failure" else 0)\n')
                original = signal.getsignal(signal.SIGTERM)
                command = [sys.executable, str(driver), outcome]
                expected = {'failure': subprocess.CalledProcessError, 'timeout': subprocess.TimeoutExpired}
                if outcome in expected:
                    with self.assertRaises(expected[outcome]):
                        assets.run_generator(command, cwd=root, env=os.environ.copy(), timeout=2)
                else:
                    self.assertEqual(0, assets.run_generator(command, cwd=root, env=os.environ.copy(), timeout=2).returncode)
                self.assertEqual(original, signal.getsignal(signal.SIGTERM))
                pid = int((root / 'child.pid').read_text())
                def running():
                    if sys.platform.startswith('linux'):
                        try:
                            status = Path(f'/proc/{pid}/stat').read_text().rsplit(')', 1)[1].split()[0]
                        except FileNotFoundError:
                            return False
                        return status != 'Z'
                    status = subprocess.run(['ps', '-o', 'stat=', '-p', str(pid)], capture_output=True, text=True).stdout.strip()
                    return bool(status) and not status.startswith('Z')
                deadline = time.monotonic() + 2
                while running() and time.monotonic() < deadline:
                    time.sleep(0.01)
                try:
                    self.assertFalse(running(), f'Generator left descendant {pid} alive')
                finally:
                    if running():
                        os.kill(pid, signal.SIGKILL)

    def test_generator_spawn_failure_restores_signal_handler(self):
        original = signal.getsignal(signal.SIGTERM)
        with self.assertRaises(FileNotFoundError):
            assets.run_generator(['/missing/trust-generator'], cwd=ROOT, env=os.environ.copy(), timeout=1)
        self.assertEqual(original, signal.getsignal(signal.SIGTERM))


if __name__ == '__main__':
    unittest.main()
