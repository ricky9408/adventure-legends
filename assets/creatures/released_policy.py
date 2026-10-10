"""Immutable released semantics permit append-only current catalog extension.

Derived offsets, row indexes and outgoing counts are intentionally NOT frozen.
A reviewed new edge may originate at a released evolved form; existing edges,
learn relationships, trial bits and identity semantics cannot disappear/change.
"""
import hashlib,json
from pathlib import Path
PATH=Path(__file__).resolve().parents[1]/'history/released-creature-relations-v4.json'
SHA256='69c6c06ad2914dbc4a3f98c07fd61d5857fc48b0d72f0f37dcef6899383999e4'

def frozen():
    blob=PATH.read_bytes()
    if hashlib.sha256(blob).hexdigest()!=SHA256:raise ValueError('Released creature relation snapshot changed')
    return json.loads(blob)

V5_PATH=PATH.with_name('released-creature-relations-v5.json')
V5_SHA256='8c0c5b7d68b3ac335054aa184f3455cd38393912c8402bff706d5fc3ecf8234b'

def frozen_v5():
    blob=V5_PATH.read_bytes()
    if hashlib.sha256(blob).hexdigest()!=V5_SHA256:raise ValueError('Released revision5 relation snapshot changed')
    return json.loads(blob)

V6_PATH=PATH.with_name('released-creature-relations-v6.json')
V6_SHA256='8524b49e7ea690dc874d02696be03743a859294aa5ca0d728c5f0f33bcff6544'

def frozen_v6():
    blob=V6_PATH.read_bytes()
    if hashlib.sha256(blob).hexdigest()!=V6_SHA256:raise ValueError('Released revision6 relation snapshot changed')
    return json.loads(blob)

V7_PATH=PATH.with_name('released-creature-relations-v7.json')
V7_SHA256='18b828c13743a70ec272bde4d1368b0eebdfca426ecba8e0f0bd0f037fbfb805'

def frozen_v7():
    blob=V7_PATH.read_bytes()
    if hashlib.sha256(blob).hexdigest()!=V7_SHA256:raise ValueError('Released revision7 relation snapshot changed')
    manifest=json.loads(blob);result={}
    for part in manifest['parts']:
        raw=V7_PATH.with_name(part['file']).read_bytes()
        if hashlib.sha256(raw).hexdigest()!=part['sha256']:raise ValueError('Released revision7 relation part changed')
        rows=json.loads(raw)
        if set(result)&set(rows):raise ValueError('Duplicate revision7 relation section')
        result.update(rows)
    canonical=(json.dumps(result,separators=(',',':'),ensure_ascii=False)+'\n').encode()
    if hashlib.sha256(canonical).hexdigest()!=manifest['semantic_sha256']:raise ValueError('Revision7 relation semantics changed')
    return result

def validate_compatibility(catalog, revision=4):
    errors=_validate_snapshot(catalog, revision, frozen())
    if revision>=5:errors+=_validate_snapshot(catalog, revision, frozen_v5())
    if revision>=6:errors+=_validate_snapshot(catalog, revision, frozen_v6())
    if revision>=7:errors+=_validate_snapshot(catalog, revision, frozen_v7())
    return sorted(set(errors))

def _validate_snapshot(catalog, revision, lock):
    errors=[]
    forms={f['id']:f for f in catalog['forms']};abilities={a['id']:a for a in catalog['abilities']}
    edges={(e['from'],e['to']):e for e in catalog['evolutions']};trials={t['trial_id']:t for t in catalog.get('trial_bindings',[])}
    released={f['id'] for f in lock['forms'] if f['introduced']<=revision}
    used_abilities=set()
    for old in lock['forms']:
        if old['id'] not in released:continue
        f=forms.get(old['id'])
        if f is None:errors.append(f'released form {old["id"]} removed');continue
        for key in ('phase','polarity','stats','stat_total','signature_ability') + (('name',) if 'name' in old else ()):
            if f.get(key)!=old[key]:errors.append(f'released form {old["id"]} changed {key}')
        if not set(old['field_caps'])<=set(f.get('field_caps',[])):errors.append(f'released form {old["id"]} lost capability')
        # Exact pairs, including minimum levels, survive. Added commands are
        # valid candidates, never implicit authority in an older bank.
        pairs={(l['level'],l['ability_id']) for l in f.get('learnset',[])}
        for l in old['learnset']:
            used_abilities.add(l['ability_id'])
            if (l['level'],l['ability_id']) not in pairs:errors.append(f'released form {old["id"]} changed learn relationship')
    for old in lock['abilities']:
        if old['id'] in used_abilities:
            a=abilities.get(old['id'])
            if a is None or any(a.get(k)!=v for k,v in old.items()):errors.append(f'released ability {old["id"]} changed')
    for old in lock['evolutions']:
        if old['from'] in released:
            new=edges.get((old['from'],old['to']))
            if new!=old:errors.append(f'released edge {old["from"]}->{old["to"]} changed')
    if catalog.get('schema_version') in (2,3):
        for old in lock['trial_bindings']:
            if old['introduced_content_revision']>revision:continue
            new=trials.get(old['trial_id'])
            if new is None or any(new.get(k)!=v for k,v in old.items() if k!='from_form_ids') or not set(old['from_form_ids'])<=set(new.get('from_form_ids',[])):
                errors.append(f'released trial {old["trial_id"]} changed')
    return errors
