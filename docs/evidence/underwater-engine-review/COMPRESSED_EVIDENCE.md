# Compressed source-export evidence

Four large candidate D/K Magma-return and Southern-rest reports are shipped as
`.json.gz` in source exports to bound individual object payloads. This changes
only their transport representation. No checks, evidence bytes, or original
candidate indexes were changed. Raw copies remain in the working docs and
original build evidence; the export may omit only the four redundant raw docs
paths listed in `compressed-evidence-packaging.json`.

The original candidate D/K indexes identify the **uncompressed** `.json` paths
and SHA-256 hashes. Decompress each `.json.gz` to its matching `.json` basename
to restore exactly those indexed bytes. Do not substitute the compressed hash
for an index's raw report hash. The packaging receipt records both hashes, both
byte counts, original index hashes, and original build evidence paths.

Gzip settings are compression level 9, mtime 0, no embedded filename, and OS
header 255. Each stream was regenerated twice and compared, then decompressed
and checked byte-for-byte against both its indexed raw report and build copy.

## Verify without changing files

Run from the source repository root:

```sh
python3 - <<'PY'
from pathlib import Path
import gzip, hashlib, json
receipt = Path('docs/evidence/underwater-engine-review/compressed-evidence-packaging.json')
for entry in json.loads(receipt.read_text())['reports']:
    packed = Path(entry['compressed_path']).read_bytes()
    raw = gzip.decompress(packed)
    assert hashlib.sha256(packed).hexdigest() == entry['compressed_sha256']
    assert hashlib.sha256(raw).hexdigest() == entry['uncompressed_sha256']
    assert len(packed) == entry['compressed_bytes']
    assert len(raw) == entry['uncompressed_bytes']
    assert int.from_bytes(packed[4:8], 'little') == 0
    index_path = Path(entry['original_index_path'])
    assert hashlib.sha256(index_path.read_bytes()).hexdigest() == entry['original_index_sha256']
    indexed = next(row for row in json.loads(index_path.read_text())['suites']
                   if row['suite'] == entry['suite'])
    assert indexed['report_sha256'] == entry['uncompressed_sha256']
    assert indexed['report'] == Path(entry['uncompressed_path']).name
    print(entry['uncompressed_path'], 'verified')
PY
```

## Restore a raw report when needed

For example, from `docs/evidence/underwater-engine-review`:

```sh
gzip -dk candidate-k-magma-return.json.gz
```

The command keeps the compressed file and does not overwrite an existing raw
report. Verification above also works directly on compressed-only source exports.
