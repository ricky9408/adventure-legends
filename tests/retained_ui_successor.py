"""Proposed explicit, read-only retained-UI adapter; never a build projection.

Historical guards consume the returned C4 view only after the full successor
delta has independently passed. Default callers receive raw current source.
This module writes nothing and never edits or substitutes a historical hash.
"""
from __future__ import annotations
import argparse
import copy
import hashlib
import json
from pathlib import Path
import re

CONTRACT_SHA256 = '213ae3124524331e5a0beebb1260d4ed8ca231395711773f0fbce09130be6e13'
ALLOWED = frozenset(('COMPLETE','THANKS','C_CHAPTER3_CLEAR','C_FINAL_SMALL',
                     'C_POSTGAME','C_ENDING_REPLAY'))
RASTER = re.compile(r'(static const UiRun (txt_(\w+)_[01])\[\] = \{[^\n]*\};)')

class Rejected(ValueError):
    pass

def require(ok, message):
    if not ok:
        raise Rejected(message)

def digest(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()

def canonical(value) -> bytes:
    return json.dumps(value,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()

def strict_json(text):
    def pairs(items):
        result={}
        for key,value in items:
            require(key not in result, 'duplicate JSON key: '+key)
            result[key]=value
        return result
    return json.loads(text,object_pairs_hook=pairs)

def load_contract(path):
    raw=Path(path).read_bytes()
    require(digest(raw)==CONTRACT_SHA256, 'unreviewed successor contract bytes')
    c=strict_json(raw)
    require(c['schema']==1 and c['name']=='journey-guidance-g4','wrong contract identity')
    require(set(c['changed_texts'])==ALLOWED,'scope is not the six reviewed keys')
    require(len(c['changed_rasters'])==12,'wrong replacement-raster scope')
    require(len(c['added_texts'])==105 and all(k.startswith('JG_') for k in c['added_texts']),
            'wrong appended-label scope')
    return c

def corpus_digest(files):
    h=hashlib.sha256()
    ordered=['src/ui.c','src/ui.h']+sorted(p for p in files if p.startswith('src/ui_data/'))
    require(set(ordered)==set(files),'unexpected corpus path')
    for relative in ordered:
        data=files[relative].encode()
        h.update(relative.encode()+b'\0'+str(len(data)).encode()+b'\0'+data)
    return h.hexdigest()

def load_state(root, contract):
    root=Path(root)
    paths=['src/ui.c','src/ui.h']+[p.relative_to(root).as_posix()
          for p in sorted((root/'src/ui_data').glob('*.inc'))]
    files={p:(root/p).read_bytes().decode() for p in paths}
    metadata_paths=list(contract['baseline_metadata_canonical_sha256'])+[
        'assets/journey_guidance_ui.json','assets/ui_texts_journey_guidance.json']
    return {'files':files,'metadata':{p:strict_json((root/p).read_bytes()) for p in metadata_paths},
        'historical':{p:digest((root/p).read_bytes()) for p in contract['historical_contract_sha256']}}

def parse_rasters(source):
    rows=[];seen=set()
    for statement,name,key in RASTER.findall(source):
        require(name not in seen,'duplicate raster: '+name)
        seen.add(name);rows.append((name,key,statement))
    return rows

class UIReadView:
    """Assertion input only. Never feed this legacy view to a compiler/generator."""
    def __init__(self, header, metadata, rasters, proof=None):
        self.header=header
        self._metadata=metadata
        self.raster_source=rasters
        self.proof=proof
    def metadata(self, path):
        require(path in self._metadata,'path outside UI compatibility view: '+path)
        return copy.deepcopy(self._metadata[path])

def verify_state(state, contract):
    require(state['historical']==contract['historical_contract_sha256'],
            'historical contract changed or missing')
    metadata=copy.deepcopy(state['metadata'])
    approved={k:v['g4'] for k,v in contract['changed_texts'].items()}
    require(metadata['assets/journey_guidance_ui.json']==dict(approved,**contract['added_texts']),
            'authoring labels differ from exact approved six+105')
    require(metadata['assets/ui_texts_journey_guidance.json']==contract['added_texts'],
            'appended generated metadata differs')
    base=metadata['assets/ui_texts.json']
    for key,values in contract['changed_texts'].items():
        require(base.get(key)==values['g4'],'wrong approved replacement value: '+key)
        base[key]=values['c4']
    for path,expected in contract['baseline_metadata_canonical_sha256'].items():
        require(digest(canonical(metadata[path]))==expected,'unapproved old metadata: '+path)

    header=state['files']['src/ui.h']
    require(digest(header.encode())==contract['target_header_sha256'],
            'enum source changed, inserted, removed, reordered or shifted')
    for name in contract['appended_enum_names']:
        line=' '+name+',\n'
        require(header.count(line)==1,'appended enum is not unique: '+name)
        header=header.replace(line,'')
    require(digest(header.encode())==contract['baseline_header_sha256'],
            'legacy enum bytes do not reconstruct exact C4')

    source=''.join(state['files'][p] for p in sorted(state['files']) if p.startswith('src/ui_data/'))
    rows=parse_rasters(source);normalized=[];new_seen=set();changed_seen=set()
    for name,key,statement in rows:
        sha=digest(statement.encode())
        if name in contract['added_raster_sha256']:
            require(sha==contract['added_raster_sha256'][name],'changed added raster: '+name)
            new_seen.add(name);continue
        if name in contract['changed_rasters']:
            row=contract['changed_rasters'][name]
            require(key==row['key'] and sha==row['after_sha256'],
                    'wrong approved replacement raster: '+name)
            statement=row['before_statement'];changed_seen.add(name)
        normalized.append(statement)
    require(new_seen==set(contract['added_raster_sha256']),'missing approved appended raster')
    require(changed_seen==set(contract['changed_rasters']),'missing approved replacement raster')
    require(len(normalized)==contract['baseline_raster_count'],'extra/missing legacy raster')
    legacy_rasters='\n'.join(normalized)
    require(digest(legacy_rasters.encode())==contract['baseline_ordered_raster_sha256'],
            'unapproved old raster value/order')
    # Protect generated pointer tables and counts too, not only matched leaves.
    require(len(state['files'])==contract['target_ui_corpus']['file_count'] and
            corpus_digest(state['files'])==contract['target_ui_corpus']['sha256'],
            'UI corpus/table differs outside approved frozen output')
    proof={'contract':contract['name'],'contract_sha256':CONTRACT_SHA256,
        'changed_existing_texts':6,'changed_existing_raster_statements':12,
        'appended_texts':105,'appended_raster_statements':210,
        'unchanged_existing_raster_statements':contract['baseline_raster_count']-12,
        'historical_contracts_preserved':True,'old_enum_bytes_reconstructed':True,
        'filesystem_mutations':0,'scope':'In-memory assertion view; not a build artifact'}
    return UIReadView(header,metadata,legacy_rasters,proof)

def read_view(root, *, successor=False, contract_path=None):
    """Default behavior is raw current data; adaptation is explicit and fail-closed."""
    root=Path(root)
    if not successor:
        paths=['assets/ui_texts.json','assets/ui_texts_return.json','assets/ui_texts_horizons.json',
               'assets/ui_texts_covenants.json','assets/ui_texts_player_feedback.json']
        return UIReadView((root/'src/ui.h').read_bytes().decode(),
            {p:strict_json((root/p).read_bytes()) for p in paths},
            ''.join(p.read_bytes().decode() for p in sorted((root/'src/ui_data').glob('*.inc'))))
    require(contract_path is not None,'explicit successor contract path required')
    contract=load_contract(contract_path)
    return verify_state(load_state(root,contract),contract)

def consume_successor_flag(argv):
    """Optional proposed integration: remove one exact opt-in from unittest argv."""
    flag='--journey-ui-successor'
    require(argv.count(flag)<=1,'repeated successor flag')
    if flag not in argv:
        return False
    argv.remove(flag)
    return True

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,required=True)
    parser.add_argument('--contract',type=Path,required=True)
    args=parser.parse_args()
    print(json.dumps(read_view(args.root,successor=True,contract_path=args.contract).proof,indent=2))
