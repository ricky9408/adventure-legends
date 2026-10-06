#!/usr/bin/env python3
"""Validate authored source and generate the reviewed development C ROM rows."""
import json
from pathlib import Path
from validate_catalog import load_json, validate, validate_enabled
from catalog_policy import CAPABILITY_MASKS, GATE_MASKS, TRIAL_POLICY, REVISION_POLICY
ROOT = Path(__file__).resolve().parent
OUT = ROOT.parent.parent / 'src' / 'creature_data.c'

def build_tables(catalog, enabled):
    """Build bounded tables in manifest order, independent of authored row order.

    This primitive supports reviewed branching tables; production generate()
    separately enforces exact revision whitelists, with no branch enabled in r4.
    """
    def ordered(rows, key, requested, label):
        mapping={key(row):row for row in rows}
        if len(mapping)!=len(rows) or len(set(requested))!=len(requested):
            raise ValueError(label+': duplicate identity')
        if any(value not in mapping for value in requested):
            raise ValueError(label+': missing authored identity')
        return [mapping[value] for value in requested]
    forms=ordered(catalog['forms'],lambda x:x['id'],enabled['enabled_form_ids'],'forms')
    abilities=ordered(catalog['abilities'],lambda x:x['id'],enabled['enabled_ability_ids'],'abilities')
    evolutions=ordered(catalog['evolutions'],lambda x:(x['from'],x['to']),
                       [tuple(e) for e in enabled['enabled_evolutions']],'evolutions')
    form_ids={f['id'] for f in forms}
    if any(e['from'] not in form_ids or e['to'] not in form_ids for e in evolutions):
        raise ValueError('evolutions: disabled endpoint')
    if not 1<=len(forms)<=128 or len(abilities)>255 or len(evolutions)>255:
        raise ValueError('ROM table count exceeds bounded identity/offset storage')
    learns=[];layouts={}
    for f in forms:
        count=len(f['learnset']);offset=len(learns)
        indexes=[i for i,e in enumerate(evolutions) if e['from']==f['id']]
        if indexes and indexes!=list(range(indexes[0],indexes[0]+len(indexes))):
            raise ValueError('evolutions: each source requires contiguous manifest rows')
        edge_offset=indexes[0] if indexes else 0
        if not 1<=count<=min(255,catalog['limits']['max_learnset']) or len(indexes)>255:
            raise ValueError('Per-form table count exceeds bounded u8 storage')
        if offset>65535 or offset+count>65535 or edge_offset>65535:
            raise ValueError('Per-form table offset exceeds bounded u16 storage')
        for command in f['learnset']:
            if type(command['ability_id']) is not int or not 1<=command['ability_id']<=255:
                raise ValueError('Learned command exceeds byte identity storage')
        layouts[f['id']]=(offset,count,edge_offset,len(indexes))
        learns.extend(f['learnset'])
    return forms,learns,evolutions,abilities,layouts


def build_indexes(forms, abilities, evolutions):
    """ROM row-plus-one indexes; zero is exclusively the disabled/absent value."""
    def indexed(rows, key, capacity, label):
        if len(rows)>255:
            raise ValueError(label+': row-plus-one count exceeds u8 storage')
        result=[0]*(capacity+1)
        for row_number,row in enumerate(rows,1):
            id_=row[key]
            if type(id_) is not int or not 1<=id_<=capacity:
                raise ValueError(label+': identity outside index bounds')
            if result[id_]:
                raise ValueError(label+': duplicate index identity')
            result[id_]=row_number
        return result
    form_index=indexed(forms,'id',128,'form index')
    ability_index=indexed(abilities,'id',255,'ability index')
    incoming_index=indexed(evolutions,'to',128,'incoming evolution index')
    for edge in evolutions:
        source=edge['from'];target=edge['to']
        if type(source) is not int or not 1<=source<=128:
            raise ValueError('incoming evolution index: source outside index bounds')
        if not form_index[source] or not form_index[target]:
            raise ValueError('incoming evolution index: disabled endpoint')
    return form_index,ability_index,incoming_index


def emit_index(name, bound, values):
    out=['const CreatureU8 %s[%s] = {' % (name,bound)]
    out += ['    '+', '.join(map(str,values[i:i+16]))+',' for i in range(0,len(values),16)]
    return out+['};','']


def generate(catalog=None, enabled=None):
    catalog = catalog if catalog is not None else load_json(ROOT / 'catalog.json')
    errors = validate(catalog, load_json(ROOT / 'identity-lock.json'))
    if errors:
        raise ValueError('\n'.join(errors))
    enabled = enabled if enabled is not None else load_json(ROOT / 'enabled.json')
    errors = validate_enabled(catalog, enabled)
    if errors:
        raise ValueError('\n'.join(errors))
    phases = {p: i for i, p in enumerate(catalog['phase_order'])}
    caps = CAPABILITY_MASKS
    slots = {s['id']: s for s in catalog['slots']}
    forms,learns,evolutions,abilities,layouts=build_tables(catalog,enabled)
    out = ['/* Generated by assets/creatures/generate_data.py. Do not edit. */', '#include "creatures.h"', '',
           'const FormId creature_legacy_forms[CREATURE_LEGACY_COUNT] = {1, 4, 7, 10};',
           'const CreatureForm creature_forms[CREATURE_ENABLED_COUNT] = {']
    for f in forms:
        s = slots[f['id']]
        learn_offset,learn_count,edge_offset,edge_count=layouts[f['id']]
        values = [f['id'], int(s['family_id'][1:]), phases[f['phase']], int(f['polarity']=='yang'), s['tier'], int(s['rarity']=='legendary')]
        stats = ', '.join(str(f['stats'][k]) for k in ['vitality','power','guard','focus','haste'])
        out.append('    {%s, {%s}, %d, 0x%08xu, %d, %d, %d, %d, %d, 0, %d, 1},' % (
            ', '.join(map(str,values)), stats, f['signature_ability'], sum(caps[x] for x in f['field_caps']),
            f['id'],learn_offset,learn_count,edge_count,edge_offset,f['id']))
    out += ['};', '', 'const CreatureLearn creature_learnsets[CREATURE_LEARNSET_COUNT] = {']
    out += ['    {%d, %d},' % (x['level'],x['ability_id']) for x in learns]
    out += ['};', '', 'const CreatureEvolution creature_evolutions[CREATURE_EVOLUTION_COUNT] = {']
    gates = GATE_MASKS
    trials = {name:value[2] for name,value in TRIAL_POLICY.items()}
    out += ['    {%d, %d, %d, %d, %d, %d},' % (e['from'],e['to'],e['min_level'],e['min_bond'],trials[e['required_trial']],gates[e['required_gate']]) for e in evolutions]
    out += ['};', '', 'const CreatureAbility creature_abilities[CREATURE_ABILITY_COUNT] = {']
    reviewed=REVISION_POLICY[enabled['content_revision']]
    if (len(forms),len(learns),len(evolutions),len(abilities)) != (len(reviewed['forms']),reviewed['learns'],len(reviewed['edges']),len(reviewed['abilities'])):
        raise ValueError('Runtime table counts differ from the reviewed revision')
    if {x['ability_id'] for x in learns} != set(enabled['enabled_ability_ids']):
        raise ValueError('Enabled command list differs from authored learnsets')
    out += ['    {%d, %d, %d, 0x%08xu},' % (a['id'],phases[a['phase']],a['cooldown_updates'],sum(caps[x] for x in a['field_caps'])) for a in abilities]
    out += ['};', '']
    form_index,ability_index,incoming_index=build_indexes(forms,abilities,evolutions)
    out += emit_index('creature_form_index','CREATURE_FORM_CAPACITY+1',form_index)
    out += emit_index('creature_ability_index','256',ability_index)
    out += emit_index('creature_incoming_evolution_index','CREATURE_FORM_CAPACITY+1',incoming_index)
    out += ['const char *creatures_name(unsigned form_id) {', '    switch (form_id) {']
    out += ['    case %d: return %s;' % (f['id'],json.dumps(f['name'])) for f in forms]
    out += ['    default: return "Unavailable form";', '    }', '}', '', 'const char *creatures_ability_name(unsigned ability_id) {', '    switch (ability_id) {']
    out += ['    case %d: return %s;' % (a['id'],json.dumps(a['name'])) for a in abilities]
    out += ['    default: return "No command";', '    }', '}', '']
    return '\n'.join(out)

if __name__ == '__main__':
    import sys
    text = generate()
    if '--check' in sys.argv:
        if OUT.read_text() != text:
            raise SystemExit('creature_data.c differs from authored catalog; regenerate it')
        print('Validated 41 development core forms, 61 learnset pairs, 20 edges, 41 abilities and deterministic ROM data; native obtainability/art/handlers are tested separately')
    else:
        OUT.write_text(text)
        print(OUT)
