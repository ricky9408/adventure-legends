#!/usr/bin/env python3
"""Run unchanged geometry methods despite the intentionally obsolete font pin.

The historical test file is byte-pinned and remains unedited. Only its top-level
_UI initialization is removed in an isolated AST; the four selected geometry
methods never reference _UI. The old-font fifth method is NOT run or relabeled.
Its relevant ID/content guarantees are covered by the authenticated successor,
its current pixel guarantees by the all-six-span/native suites. Current artifact
size bounds are checked here separately. No modified game source is compiled.
"""
from pathlib import Path
import ast,hashlib,types,unittest
from verify_gbj_font_successor import verify
ROOT=Path(__file__).resolve().parents[1]
verify()
path=ROOT/'tests/test_return_geometry.py';raw=path.read_bytes()
assert hashlib.sha256(raw).hexdigest()=='a81bda129ca8e479f7d3c6e786a3a061d3fdb2372f63a09fb40a2d0568bf1a49'
parsed=ast.parse(raw,str(path));removed=[n for n in parsed.body if isinstance(n,ast.Assign)and any(isinstance(t,ast.Name)and t.id=='_UI'for t in n.targets)]
assert len(removed)==1 and ast.unparse(removed[0])=='_UI = read_view_for_flags(ROOT, sys.argv)'
parsed.body.remove(removed[0]);module=types.ModuleType('gbj_unchanged_return_geometry');module.__file__=str(path)
exec(compile(parsed,str(path),'exec'),module.__dict__)
names=('test_dimensions_spawns_and_all_dynamic_state_reachability','test_row_band_exact_half_open_rectangles','test_distinct_local_trial_workspaces_and_marked_targets','test_original_npc_approaches_are_not_stolen')
for node in ast.walk(parsed):
 if isinstance(node,ast.FunctionDef)and node.name in names:assert all(not isinstance(n,ast.Name)or n.id!='_UI'for n in ast.walk(node))
class CurrentBounds(unittest.TestCase):
 def test_current_artifact_bounds(self):
  files=list((ROOT/'src/return_art_data').glob('*.inc'))+list((ROOT/'assets/return_region').glob('*.json'))+[ROOT/'assets/ui_texts.json',ROOT/'assets/ui_texts_return.json']
  for p in files:self.assertLess(p.stat().st_size,75000,str(p))
route_path=ROOT/'tests/test_connected_route_copy.py';route_raw=route_path.read_bytes()
assert hashlib.sha256(route_raw).hexdigest()=='a20fb28111f306603bafcb25038f2a2f13e7302fc20ff85d47e08fd9a5b04ec5'
route_ast=ast.parse(route_raw,str(route_path));initializers=[n for n in route_ast.body if isinstance(n,ast.Assign)and any(isinstance(t,ast.Name)and t.id=='_UI'for t in n.targets)]
assert len(initializers)==1 and ast.unparse(initializers[0])=='_UI = read_view_for_flags(ROOT, sys.argv)'
route_ast.body.remove(initializers[0]);route=types.ModuleType('gbj_unchanged_route_copy');route.__file__=str(route_path)
exec(compile(route_ast,str(route_path),'exec'),route.__dict__)
route_name='test_exact_approved_authoring_and_rendered_text'
for node in ast.walk(route_ast):
 if isinstance(node,ast.FunctionDef)and node.name==route_name:assert all(not isinstance(n,ast.Name)or n.id!='_UI'for n in ast.walk(node))
suite=unittest.TestSuite([module.Geometry(name)for name in names]+[CurrentBounds('test_current_artifact_bounds'),route.RouteCopy(route_name)])
result=unittest.TextTestRunner(verbosity=2).run(suite)
raise SystemExit(not result.wasSuccessful())
