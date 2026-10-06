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

def validate_compatibility(catalog, revision=4):
    lock=frozen();errors=[]
    forms={f['id']:f for f in catalog['forms']};abilities={a['id']:a for a in catalog['abilities']}
    edges={(e['from'],e['to']):e for e in catalog['evolutions']};trials={t['trial_id']:t for t in catalog.get('trial_bindings',[])}
    released={f['id'] for f in lock['forms'] if f['introduced']<=revision}
    used_abilities=set()
    for old in lock['forms']:
        if old['id'] not in released:continue
        f=forms.get(old['id'])
        if f is None:errors.append(f'released form {old["id"]} removed');continue
        for key in ('phase','polarity','stats','stat_total','signature_ability'):
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
    if catalog.get('schema_version')==2:
        for old in lock['trial_bindings']:
            if old['introduced_content_revision']>revision:continue
            new=trials.get(old['trial_id'])
            if new is None or any(new.get(k)!=v for k,v in old.items() if k!='from_form_ids') or not set(old['from_form_ids'])<=set(new.get('from_form_ids',[])):
                errors.append(f'released trial {old["trial_id"]} changed')
    return errors
