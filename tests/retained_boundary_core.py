"""Strict shared-core contracts for retained boundary algorithm comparisons.

The historical contract remains valid only for its unchanged core. Content8
has a separate explicit, immutable contract; it never rewrites an oracle or
claims equivalence of the historical and current catalog/save implementations.
"""
import gzip
import hashlib
import json
import re
from pathlib import Path

CONTRACT_SHA256 = '752e7874ad0ef81ce96a1b274a60d8fcc3db7a16fa02f9835670d4c2a2593d1e'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def include_closure(root, modules):
    paths = set()
    pending = [root/'src'/f'{name}.c' for name in modules]
    while pending:
        path = pending.pop()
        if path in paths:
            continue
        paths.add(path)
        for name in re.findall(r'^\s*#\s*include\s*"([^"]+)"', path.read_text(), re.M):
            target = path.parent/name
            assert target.is_file(), ('Missing quoted core include', path, name)
            pending.append(target)
    return {str(path.relative_to(root)): sha(path) for path in sorted(paths)}


def verify_manifest_provenance(root, contract, candidate):
    """Require the exact one-backup packaging delta from native C to export."""
    provenance = contract['native_source_manifest_provenance']
    archive = root/provenance['original_manifest_archive']
    assert sha(archive) == provenance['original_manifest_archive_sha256']
    original_bytes = gzip.decompress(archive.read_bytes())
    assert hashlib.sha256(original_bytes).hexdigest() == provenance['original_manifest_sha256']
    original = json.loads(original_bytes)
    assert len(original) == provenance['original_input_files']
    assert len(candidate) == provenance['canonical_input_files']
    removed = provenance['source_path_removed']
    assert set(original)-set(candidate) == {removed}
    assert candidate == {p: h for p, h in original.items() if p != removed}
    backup = root/provenance['archived_path']
    assert sha(backup) == original[removed] == provenance['archived_sha256']
    assert backup.stat().st_size == provenance['archive_bytes']
    correspondence_path = root/provenance['correspondence']
    assert sha(correspondence_path) == provenance['correspondence_sha256']
    correspondence = json.loads(correspondence_path.read_text())
    for key in ('original_manifest_sha256', 'original_input_files',
                'source_path_removed', 'archived_path', 'archived_sha256', 'archive_bytes'):
        assert correspondence[key] == provenance[key]
    assert correspondence['expected_export_manifest_sha256'] == contract['candidate_source_manifest_sha256']
    assert correspondence['retained_runtime_input_files'] == len(candidate)
    assert correspondence['rom_sha256'] == contract['candidate_rom_sha256']
    assert correspondence['included_by_any_current_object_dependency'] is False
    assert correspondence['compiled_source_hashes_unchanged'] is True
    return {**provenance, 'exact_single_backup_delta_verified': True}


def verify_core(root, name, modules, frozen_hashes):
    """Return evidence only after checking exact historical or content8 pins."""
    current = include_closure(root, modules)
    historical = (dict(frozen_hashes) if name == 'magma' else
                  {path: frozen_hashes[path] for path in current if path in frozen_hashes})
    # Preserve the original historical guard, including the complete closure.
    if current == historical:
        return {'mode': 'unchanged-historical-core', 'core_hashes': current,
                'same_core_for_both_algorithms': True}

    path = root/'tests/retained_boundary_content8_core.json'
    assert sha(path) == CONTRACT_SHA256, 'Unreviewed content8 boundary contract'
    contract = json.loads(path.read_text())
    item = contract['contracts'][name]
    assert modules == item['modules'], 'Unreviewed module closure'
    assert sha(root/item['frozen_core_manifest']) == item['frozen_core_manifest_sha256']
    assert historical == item['frozen_core_hashes'], 'Historical core pins changed'
    assert current == item['current_core_hashes'], 'Unreviewed current core bytes or include closure'
    actual_changes = {p: {'frozen_sha256': historical.get(p), 'current_sha256': h}
                      for p, h in current.items() if historical.get(p) != h}
    declared_changes = {p: {k: row[k] for k in ('frozen_sha256', 'current_sha256')}
                        for p, row in item['changed_or_added_core_files'].items()}
    assert actual_changes == declared_changes, 'Core changes must be explicitly enumerated'
    manifest = root/'build/source-hashes.json'
    assert sha(manifest) == contract['candidate_source_manifest_sha256']
    candidate = json.loads(manifest.read_text())
    provenance = verify_manifest_provenance(root, contract, candidate)
    assert all(candidate.get(p) == h for p, h in current.items())
    assert all(sha(root/p) == h for p, h in candidate.items()), 'Candidate runtime changed'
    assert sha(root/'build/emberbond.gba') == contract['candidate_rom_sha256']
    return {'mode': 'pinned-content8-shared-core', 'scope': contract['scope'],
            'limitations': contract['limitations'], 'contract_sha256': sha(path),
            'verifier_sha256': sha(Path(__file__)),
            'candidate_rom_sha256': contract['candidate_rom_sha256'],
            'candidate_source_manifest_sha256': sha(manifest),
            'native_source_manifest_provenance': provenance,
            'candidate_runtime_verified': True, 'same_core_for_both_algorithms': True,
            'historical_core_equivalence_claimed': False, **item}
