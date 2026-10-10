"""Exact opt-in renderer context contract for equipment rewards I4.

No environment switch or fallback selects a successor. Original G5, I1 and I3
manifests remain independently byte-pinned, with every renderer/query retained.
"""
from __future__ import annotations
import hashlib,json,re
from pathlib import Path

PARENT_SHA256='5a69a55f4edf76367caf7365dcdbb8d7e80e19820544592941d83be5a8b37729'
PREVIOUS_SUCCESSOR_SHA256='b0dae44cc59ee7ab8e4287ae29ecc3fdd12967f649dfce5b6c3d130e5a2b6991'
I3_SUCCESSOR_SHA256='99d029ce84661506e833a07c86c2257a36dc0e943faa244afe462b781c9e763f'
SUCCESSOR_SHA256='5ea36d4d92fa7e7389e45f3dd493da037ae449481a0ce4e1da2320e34af92c0f'
FLAG='--equipment-rewards-successor'
CHANGED_CONTEXT={'src/game_shop.c','src/economy.c','src/save5_preflight.inc'}
I4_CHANGED_CONTEXT={'src/save_feedback.c'}
I4_ADDED_CONTEXT={'src/save_snapshot_copy.h'}

def digest(data:bytes)->str:return hashlib.sha256(data).hexdigest()

def query_function(text:str,name:str)->str:
    match=re.search(r'(?:COLD\s+)?(?:unsigned|int|void)\s+'+re.escape(name)+r'\([^)]*\)\s*\{',text)
    assert match,('Missing pinned query function',name)
    end=match.end();depth=1
    while depth:
        depth+=(text[end]=='{')-(text[end]=='}');end+=1
    return text[match.start():end]

def select_manifest(fixture:Path,successor:bool=False,successor_path:Path|None=None):
    original=fixture/'reference.json';raw=original.read_bytes()
    assert digest(raw)==PARENT_SHA256,'Original renderer manifest changed'
    parent=json.loads(raw)
    if not successor:
        assert successor_path is None,'A successor manifest requires explicit opt-in'
        return parent,original
    previous_raw=(fixture.parent/'render-equipment-i1/reference.json').read_bytes()
    assert digest(previous_raw)==PREVIOUS_SUCCESSOR_SHA256,'Previous equipment renderer manifest changed'
    previous=json.loads(previous_raw)
    i3_raw=(fixture.parent/'render-equipment-i3/reference.json').read_bytes()
    assert digest(i3_raw)==I3_SUCCESSOR_SHA256,'I3 equipment renderer manifest changed'
    i3=json.loads(i3_raw)
    # Preserve the complete I3 contract, including its exact ordinary slice proof.
    assert i3['parent_manifest_sha256']==PARENT_SHA256
    assert i3['previous_successor_manifest_sha256']==PREVIOUS_SUCCESSOR_SHA256
    for key in previous:
        if key!='reviewed_candidate':assert i3[key]==previous[key],('I3 changed an inherited renderer contract',key)
    change=i3['source_change']
    assert change['path']=='src/game.c'
    assert change['before_sha256']==previous['reviewed_candidate']['game_source_sha256']
    assert change['after_sha256']==i3['reviewed_candidate']['game_source_sha256']
    assert change['before_statement']=='status=save5_step(256);save_feedback_background_frames++;'
    assert change['after_statement']=='status=save5_step(192);save_feedback_background_frames++;'
    for key in ('schema','scope','baseline','fixture_files','reference_function_sha256','candidate_function_sha256','suites'):
        assert i3[key]==parent[key],('Successor changed original renderer contract',key)
    assert set(i3['context_source_pins'])==set(parent['context_source_pins'])
    assert set(i3['context_changes'])==CHANGED_CONTEXT
    for relative,old in parent['context_source_pins'].items():
        new=i3['context_source_pins'][relative]
        if relative in CHANGED_CONTEXT:
            change=i3['context_changes'][relative]
            assert change['before_sha256']==old and change['after_sha256']==new and new!=old and change['reason']
        else:assert new==old,('Unreviewed successor context',relative)
    path=successor_path or fixture.parent/'render-equipment-i4/reference.json'
    raw=path.read_bytes()
    assert digest(raw)==SUCCESSOR_SHA256,'Equipment renderer successor manifest changed'
    selected=json.loads(raw)
    assert selected['i3_successor_manifest_sha256']==I3_SUCCESSOR_SHA256
    assert set(selected)==set(i3)|{'i3_successor_manifest_sha256'}
    for key in i3:
        if key not in ('reviewed_candidate','context_source_pins','context_changes'):
            assert selected[key]==i3[key],('I4 changed an inherited renderer contract',key)
    assert selected['reviewed_candidate']['game_source_sha256']==i3['reviewed_candidate']['game_source_sha256']
    assert set(selected['context_source_pins'])==set(i3['context_source_pins'])|I4_ADDED_CONTEXT
    assert set(selected['context_changes'])==CHANGED_CONTEXT|I4_CHANGED_CONTEXT|I4_ADDED_CONTEXT
    for relative,old in i3['context_source_pins'].items():
        new=selected['context_source_pins'][relative]
        if relative in I4_CHANGED_CONTEXT:
            change=selected['context_changes'][relative]
            assert change['before_sha256']==old and change['after_sha256']==new and new!=old and change['reason']
        else:assert new==old,('Unreviewed I4 context',relative)
    for relative in CHANGED_CONTEXT:assert selected['context_changes'][relative]==i3['context_changes'][relative]
    for relative in I4_ADDED_CONTEXT:
        change=selected['context_changes'][relative]
        assert change['before_sha256'] is None and change['after_sha256']==selected['context_source_pins'][relative] and change['reason']
    return selected,path
