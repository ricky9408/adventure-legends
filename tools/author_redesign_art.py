#!/usr/bin/env python3
"""Author explicit new art identities after review; never rewrites historical contracts."""
from pathlib import Path
import argparse
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'assets'))
from legacy_art_successor import authoring_definitions, read_base_arrays, sha
from redesign_art_guard import CONTRACT_PATH, SUCCESSOR_ID

REVIEWABLE_ARRAYS = {
    'background_village', 'background_forest', 'background_temple',
    'background_boss', 'background_title', 'sprite_data', 'boss_data',
    'hero_frames', 'companion_frames', 'companion_direction_frames',
    'foreground_canopy_data',
}


def author():
    parent = json.loads((ROOT / 'assets/connected_roads_legacy_art_contract.json').read_text())
    current = read_base_arrays(ROOT)
    assert current.keys() == parent['base_arrays'].keys(), 'Art array set must remain stable'
    arrays, changed = {}, []
    for name, value in current.items():
        prior = parent['base_arrays'][name]
        assert value['declaration'] == prior['declaration'], ('Art memory layout changed', name)
        digest = sha(value['initializer'].encode())
        before = prior['successor_initializer_sha256']
        if digest != before:
            assert name in REVIEWABLE_ARRAYS, ('Protected base array changed', name)
            changed.append(name)
        arrays[name] = {'declaration': value['declaration'],
                        'parent_initializer_sha256': before,
                        'successor_initializer_sha256': digest}
    contracts = {}
    for family in ('underwater_creatures', 'return_creatures'):
        relative = f'assets/{family}/legacy_prefix_sha256.json'
        path = ROOT / relative
        historical = json.loads(path.read_text())
        exceptions = {}
        for name, before in historical['sha256'].items():
            item = ROOT / name
            after = sha(item.read_bytes()) if item.is_file() else None
            if after != before:
                assert name in ('assets/generate_assets.py',
                                'assets/magma_creatures/released65_silhouettes_native.png') or name.startswith(
                    ('src/asset_data/', 'src/evolution_art_data/')), ('Protected released art changed', name)
                exceptions[name] = {'historical_sha256': before, 'successor_sha256': after}
        contracts[relative] = {'contract_sha256': sha(path.read_bytes()),
                               'reviewed_exceptions': exceptions}
    sources = ('assets/generate_assets.py', 'assets/redesign_characters.py',
               'assets/generate_evolutions.py', 'assets/horizons_region/source_plan.json')
    result = {'schema': 1, 'successor': SUCCESSOR_ID,
              'scope': 'Authored art identity, not gameplay or subjective-quality evidence.',
              'parent_successor': 'connected-roads-c4',
              'reviewed_arrays': sorted(changed), 'base_arrays': arrays,
              'base_asset_parts': [p.relative_to(ROOT).as_posix() for p in sorted((ROOT / 'src/asset_data').glob('part_*.inc'))],
              'authoring_sources': {p: sha((ROOT / p).read_bytes()) for p in sources},
              'authoring_definitions': authoring_definitions(ROOT / 'assets/generate_assets.py'),
              'historical_contracts': contracts}
    output = ROOT / CONTRACT_PATH
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
    print(f'Authored {output.relative_to(ROOT)}: {len(changed)} changed base arrays; palette and layouts retained')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--author', action='store_true', required=True,
                        help='Explicitly replace only the new redesign identity manifest')
    parser.parse_args()
    author()
