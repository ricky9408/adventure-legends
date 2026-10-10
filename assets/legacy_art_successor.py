"""Strict historical art guards plus one explicitly reviewed world successor.

No hashes are refreshed at runtime. An explicit successor selection accepts only
its frozen background-authoring/chunk hashes and independently checks every base
asset initializer, unchanged creature-authoring definition, and historical file.
"""
from pathlib import Path
import ast, hashlib, json, re

SUCCESSOR_ID='connected-roads-c4'
SUCCESSOR_FILE='assets/connected_roads_legacy_art_contract.json'
_ARRAY=re.compile(r'(^const[^\n=]*?)(\b[A-Za-z_]\w*)((?:\[[^\]\n]+\])+)[ \t]*=[ \t]*(\{.*?\});',re.M|re.S)

def sha(data):return hashlib.sha256(data).hexdigest()

def read_base_arrays(root):
    paths=sorted((root/'src/asset_data').glob('part_*.inc'))
    text=''.join(p.read_text()for p in paths)
    arrays={};last=0
    for m in _ARRAY.finditer(text):
        assert not text[last:m.start()].strip(),'Unexpected code between base asset arrays'
        assert m[2] not in arrays,('Duplicate base array',m[2])
        arrays[m[2]]={'declaration':re.sub(r'\s+',' ',m[1]+m[2]+m[3]).strip(),
                      'initializer':re.sub(r'\s+','',m[4])}
        last=m.end()
    assert not text[last:].strip(),'Unexpected code after base asset arrays'
    assert arrays,'Missing base asset arrays'
    return arrays

def authoring_definitions(path):
    tree=ast.parse(path.read_text())
    return {node.name:sha(ast.dump(node,include_attributes=False).encode())
            for node in tree.body if isinstance(node,(ast.FunctionDef,ast.ClassDef))}

def validate_reviewed_successor(root,contract_path,contract,successor):
    assert successor==SUCCESSOR_ID,('Unknown reviewed successor',successor)
    reviewed=json.loads((root/SUCCESSOR_FILE).read_text())
    assert reviewed['successor']==successor
    rel=str(contract_path.relative_to(root))
    rule=reviewed['historical_contracts'][rel]
    assert sha(contract_path.read_bytes())==rule['contract_sha256'],('Historical contract changed',rel)
    exceptions=rule['reviewed_exceptions']
    assert set(exceptions)<=set(contract['sha256']),'Exception outside historical contract'
    for path,expected in contract['sha256'].items():
        current=sha((root/path).read_bytes())
        if path in exceptions:
            e=exceptions[path]
            assert e['historical_sha256']==expected,('Historical exception identity mismatch',path)
            assert current==e['successor_sha256'],('Unreviewed successor file',path)
        else:assert current==expected,('Released creature/palette prefix changed',path)
    parts=[str(p.relative_to(root))for p in sorted((root/'src/asset_data').glob('part_*.inc'))]
    assert parts==reviewed['base_asset_parts'],'Unexpected base asset chunks'
    arrays=read_base_arrays(root)
    assert set(arrays)==set(reviewed['base_arrays']),'Base asset array set changed'
    for name,value in arrays.items():
        expected=reviewed['base_arrays'][name]
        assert value['declaration']==expected['declaration'],('Base array shape/type changed',name)
        assert sha(value['initializer'].encode())==expected['successor_initializer_sha256'],('Base array changed',name)
        if name not in reviewed['reviewed_scenery_arrays']:
            assert expected['successor_initializer_sha256']==expected['historical_initializer_sha256'],('Protected array was exempted',name)
    # Only the two village bough masks may be cleared; all four other masks
    # remain the original bytes, independently of chunk or declaration layout.
    pixels=bytes(map(int,re.findall(r'\d+',arrays['foreground_canopy_data']['initializer'])))
    assert len(pixels)==6144 and not any(pixels[:2048]),'Village canopy removal differs'
    assert sha(pixels[2048:])==reviewed['preserved_canopy_tail_sha256'],'Other foreground masks changed'
    definitions=authoring_definitions(root/'assets/generate_assets.py')
    assert set(definitions)==set(reviewed['authoring_definitions']),'Authoring definition set changed'
    for name,digest in definitions.items():
        e=reviewed['authoring_definitions'][name]
        assert digest==e['successor_ast_sha256'],('Unreviewed authoring definition',name)
        if name not in ('village','main'):
            assert digest==e['historical_ast_sha256'],('Creature/primitive authoring changed',name)
    return {'baseline':contract['baseline'],'files':len(contract['sha256']),
            'unchanged':False,'reviewed_world_successor':successor,
            'reviewed_background_file_exceptions':len(exceptions),
            'protected_creature_palette_arrays_unchanged':True,
            'unchanged_historical_files':len(contract['sha256'])-len(exceptions)}

def validate_legacy_prefix(root,contract_path,successor=None):
    root=Path(root).resolve();contract_path=Path(contract_path).resolve()
    contract=json.loads(contract_path.read_text())
    if successor is not None:return validate_reviewed_successor(root,contract_path,contract,successor)
    for path,digest in contract['sha256'].items():
        assert sha((root/path).read_bytes())==digest,('Released art prefix changed',path)
    return {'baseline':contract['baseline'],'files':len(contract['sha256']),'unchanged':True}
