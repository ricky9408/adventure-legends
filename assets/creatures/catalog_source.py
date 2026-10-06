"""Strict deterministic catalog authoring fragments, assembled before validation.

catalog.json is a descriptor. Referenced JSON fragments are relative, single-use,
contained below its directory, and small enough for public review. Conventional
monolithic JSON remains readable for immutable fixtures and mutation tests.
"""
import json
from pathlib import Path

MAX_SOURCE_BYTES = 90000
class CatalogError(ValueError): pass

def _read_json(path):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result: raise CatalogError('duplicate JSON key: '+key)
            result[key] = value
        return result
    def constant(value): raise CatalogError('non-finite JSON value: '+value)
    path = Path(path)
    data = json.loads(path.read_text(encoding='utf-8'), object_pairs_hook=pairs, parse_constant=constant)
    return data

def load_json(path):
    data=_read_json(path)
    return load_catalog(path,data) if isinstance(data,dict) and '$catalog_source' in data else data

def load_catalog(path, descriptor=None):
    path = Path(path)
    if descriptor is None: return load_json(path)
    if set(descriptor) != {'$catalog_source','sections'} or descriptor['$catalog_source'] != 1 or not isinstance(descriptor['sections'], dict):
        raise CatalogError('unsupported catalog source descriptor')
    if path.stat().st_size >= MAX_SOURCE_BYTES: raise CatalogError('catalog descriptor reaches source bound')
    result = {}; used = set(); base = path.parent.resolve()
    for key, files in descriptor['sections'].items():
        if not isinstance(key, str) or not isinstance(files, list) or not files:
            raise CatalogError('invalid catalog source section')
        chunks = []
        for name in files:
            if not isinstance(name,str) or Path(name).is_absolute() or '..' in Path(name).parts:
                raise CatalogError('duplicate or unsafe catalog fragment path')
            target = (base/name).resolve()
            if target in used or not target.is_relative_to(base) or target.suffix != '.json' or target.stat().st_size >= MAX_SOURCE_BYTES:
                raise CatalogError('catalog fragment outside source bounds')
            used.add(target); value = _read_json(target)
            if isinstance(value,dict) and '$catalog_source' in value: raise CatalogError('nested catalog descriptor fragment')
            if key == '$metadata':
                if len(files) != 1 or not isinstance(value,dict) or set(value)&set(descriptor['sections']):
                    raise CatalogError('invalid catalog metadata fragment')
                result.update(value)
            else:
                if not isinstance(value,list): raise CatalogError('catalog row fragment must be array')
                chunks.extend(value)
        if key != '$metadata':
            if key in result: raise CatalogError('duplicate catalog section')
            result[key] = chunks
    return result
