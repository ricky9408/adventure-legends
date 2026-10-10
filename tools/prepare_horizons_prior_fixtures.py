#!/usr/bin/env python3
"""Verify and materialize portable accepted-H producer reports and exact SRAM."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT/'tests/fixtures/horizons-native-prior-h'
PINNED = {
    'full': ('eb62317f54af072892e9eadc3b4e73ad5cd70788e9c20053afba2eeb897f2b82',
             'd482466d04050c3d7f2e8eb8e1960729c9b9b33aa3e32440d186a4b54b854a69'),
    'minimal-north-lifecycle': ('e99750715413bd8a1ae62b70a064c4f7e22be3ea5f72ff8cf59a9b95dda416e7',
                                '0c49f8cee8c601dbc3de35f2f98911b96f483fc32060b4b6817e650151fee970'),
}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    manifest = json.loads((FIXTURES/'manifest.json').read_text())
    assert {row['stage'] for row in manifest['files']} == set(PINNED)
    materialized = []
    for row in manifest['files']:
        folder = FIXTURES/row['stage']
        packed = (folder/'return-journey.json.gz').read_bytes()
        assert sha(packed) == row['producer_gzip_sha256']
        report = gzip.decompress(packed)
        sram = (folder/row['sram_filename']).read_bytes()
        assert (sha(report), sha(sram)) == PINNED[row['stage']]
        producer = json.loads(report)
        assert producer['controller_only'] and not producer['game_ram_writes']
        assert not producer['machine_state_loads'] and not producer['failures']
        assert producer['global_native']['closed'] and not producer['global_native']['exceptions']
        assert all(check['passed'] for check in producer['checks'])
        assert producer['rom_sha256'] == manifest['source_rom_sha256']
        assert producer['snapshots'][row['snapshot']]['sram_sha256'] == sha(sram)
        target = args.output.resolve()/row['stage']
        target.mkdir(parents=True, exist_ok=True)
        for name, data in [('return-journey.json', report), (row['sram_filename'], sram)]:
            path = target/name
            if path.exists():
                assert path.read_bytes() == data, 'Refusing to overwrite different fixture: '+str(path)
            else:
                path.write_bytes(data)
            materialized.append({'path': str(path), 'sha256': sha(data)})
    receipt = {'scope': 'Exact prior H SRAM and portable producer reports; this does not run current-ROM tests',
               'manifest_sha256': sha((FIXTURES/'manifest.json').read_bytes()),
               'files': materialized}
    (args.output/'materialization.json').write_text(json.dumps(receipt, indent=2)+'\n')
    print(json.dumps(receipt, indent=2))


if __name__ == '__main__':
    main()
