"""Validate the explicitly reviewed Lantern Trails art against released inputs."""
from pathlib import Path
import json
import re

from legacy_art_successor import authoring_definitions, read_base_arrays, sha

SUCCESSOR_ID = 'lantern-trails-r1'
CONTRACT_PATH = 'assets/redesign/art-contract.json'


def validate(root, contract_path, contract):
    root = Path(root)
    reviewed = json.loads((root / CONTRACT_PATH).read_text())
    assert reviewed['schema'] == 1 and reviewed['successor'] == SUCCESSOR_ID
    relative = contract_path.relative_to(root).as_posix()
    rule = reviewed['historical_contracts'][relative]
    assert sha(contract_path.read_bytes()) == rule['contract_sha256'], 'Historical art contract changed'
    exceptions = rule['reviewed_exceptions']
    assert set(exceptions) <= set(contract['sha256']), 'Unknown historical art exception'
    for path, historical in contract['sha256'].items():
        current = sha((root / path).read_bytes()) if (root / path).is_file() else None
        if path in exceptions:
            expected = exceptions[path]
            assert expected['historical_sha256'] == historical, ('Historical identity changed', path)
            assert current == expected['successor_sha256'], ('Unreviewed redesign art', path)
        else:
            assert current == historical, ('Protected companion art changed', path)
    parts = [p.relative_to(root).as_posix() for p in sorted((root / 'src/asset_data').glob('part_*.inc'))]
    assert parts == reviewed['base_asset_parts'], 'Unexpected base art chunks'
    arrays = read_base_arrays(root)
    assert set(arrays) == set(reviewed['base_arrays']), 'Base art array set changed'
    for name, value in arrays.items():
        expected = reviewed['base_arrays'][name]
        assert value['declaration'] == expected['declaration'], ('Art memory layout changed', name)
        assert sha(value['initializer'].encode()) == expected['successor_initializer_sha256'], ('Unreviewed art pixels', name)
        if name not in reviewed['reviewed_arrays']:
            assert expected['successor_initializer_sha256'] == expected['parent_initializer_sha256'], ('Protected base art changed', name)
    assert 'game_palette' not in reviewed['reviewed_arrays'], 'Shared palette is protected'
    canopies = bytes(map(int, re.findall(r'\d+', arrays['foreground_canopy_data']['initializer'])))
    assert len(canopies) == 6144 and not any(canopies[:2048]), 'Village paths must remain free of foreground canopy'
    for path, expected in reviewed['authoring_sources'].items():
        assert sha((root / path).read_bytes()) == expected, ('Unreviewed art authoring', path)
    assert authoring_definitions(root / 'assets/generate_assets.py') == reviewed['authoring_definitions']
    return {'baseline': contract['baseline'], 'files': len(contract['sha256']),
            'unchanged': False, 'reviewed_world_successor': SUCCESSOR_ID,
            'reviewed_art_file_exceptions': len(exceptions),
            'shared_palette_and_array_layout_unchanged': True,
            'unchanged_historical_files': len(contract['sha256']) - len(exceptions)}
