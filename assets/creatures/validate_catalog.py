#!/usr/bin/env python3
"""Deterministic, dependency-free structural and semantic catalog validation.
Only supports the explicit JSON Schema subset used by catalog.schema.json;
unknown validation keywords are a schema error, never silently ignored.
"""
import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent
PHASES=['wood','fire','earth','metal','water']
GENERATION=list(zip(PHASES,PHASES[1:]+PHASES[:1]))
CONTROL=[('wood','earth'),('earth','water'),('water','fire'),('fire','metal'),('metal','wood')]
from catalog_policy import (LEGACY_FIELD_CAPABILITIES, FIELD_CAPABILITIES,
                            REVISION_POLICY, TRIAL_POLICY, TRIAL_PREREQUISITES, GATE_MASKS,
                            CURRENT_POLARITY_OVERRIDES, HORIZONS_SIGNATURES,
                            HORIZONS_INHERITED_COMMANDS, HORIZONS_EDGES,
                            COVENANT_FORMS, COVENANT_SIGNATURES, COVENANT_SUPPORT_COMMANDS,
                            COVENANT_GATE_NAMES, COVENANT_PRESERVATION_SHA256)
KEYWORDS={'$schema','$id','$defs','title','$ref','type','enum','const','properties','required','additionalProperties','items','minItems','maxItems','uniqueItems','minimum','maximum','minLength','maxLength','pattern'}

from catalog_source import CatalogError, load_json

def structure(value,schema,root,path='$'):
    errors=[]
    unknown=set(schema)-KEYWORDS
    if unknown:raise CatalogError(f'unsupported schema keywords: {sorted(unknown)}')
    if '$ref' in schema:
        key=schema['$ref'].removeprefix('#/$defs/')
        if schema['$ref']!='#/$defs/'+key or key not in root['$defs']:raise CatalogError('unsupported schema reference')
        return structure(value,root['$defs'][key],root,path)
    types={'integer':lambda x:type(x) is int,'string':lambda x:isinstance(x,str),'array':lambda x:isinstance(x,list),'object':lambda x:isinstance(x,dict),'boolean':lambda x:type(x) is bool,'null':lambda x:x is None}
    if 'type' in schema and not types[schema['type']](value):return [f'{path}: expected {schema["type"]}']
    if 'const' in schema and (type(value)!=type(schema['const']) or value!=schema['const']):errors.append(f'{path}: incorrect fixed value')
    if 'enum' in schema and not any(type(value)==type(x) and value==x for x in schema['enum']):errors.append(f'{path}: invalid enum value')
    if type(value) is int:
        if value<schema.get('minimum',value):errors.append(f'{path}: below minimum')
        if value>schema.get('maximum',value):errors.append(f'{path}: above maximum')
    if isinstance(value,str):
        if len(value)<schema.get('minLength',0) or len(value)>schema.get('maxLength',len(value)):errors.append(f'{path}: invalid string length')
        if 'pattern' in schema and not re.search(schema['pattern'],value):errors.append(f'{path}: invalid string pattern')
    if isinstance(value,list):
        if len(value)<schema.get('minItems',0) or len(value)>schema.get('maxItems',len(value)):errors.append(f'{path}: invalid array count')
        if schema.get('uniqueItems') and len({json.dumps(v,sort_keys=True) for v in value})!=len(value):errors.append(f'{path}: duplicate array value')
        if 'items' in schema:
            for i,item in enumerate(value):errors+=structure(item,schema['items'],root,f'{path}[{i}]')
    if isinstance(value,dict):
        for k in schema.get('required',[]):
            if k not in value:errors.append(f'{path}.{k}: required')
        for k in sorted(value):
            if k in schema.get('properties',{}):errors+=structure(value[k],schema['properties'][k],root,f'{path}.{k}')
            elif schema.get('additionalProperties') is False:errors.append(f'{path}.{k}: unknown property')
    return errors

def validate(data,identity=None,schema=None):
    version=data.get('schema_version') if isinstance(data,dict) else None
    if type(version) is not int or version not in (1,2,3):
        return ['schema_version: unsupported authoring revision']
    schema=schema or load_json(ROOT/{1:'catalog.v1.schema.json',2:'catalog.schema.json',3:'catalog.v3.schema.json'}[version])
    errors=structure(data,schema,schema)
    if errors:return sorted(errors)
    def check(test,msg):
        if not test:errors.append(msg)
    def index(items,label,key='id'):
        result={v[key]:v for v in items}
        check(len(result)==len(items),f'{label}: duplicate IDs')
        check([v[key] for v in items]==sorted(result),f'{label}: IDs must be sorted and unique')
        return result
    def acyclic(nodes,edges,label):
        adj={n:[] for n in nodes}; indegree={n:0 for n in nodes}
        for a,b in edges:
            if a not in adj or b not in adj:check(False,f'{label}: unknown graph endpoint');continue
            adj[a].append(b);indegree[b]+=1
        ready=sorted(n for n,v in indegree.items() if v==0);count=0
        while ready:
            a=ready.pop(0);count+=1
            for b in sorted(adj[a]):
                indegree[b]-=1
                if indegree[b]==0:ready.append(b);ready.sort()
        check(count==len(nodes),f'{label}: cycle detected')
    S=index(data['slots'],'slots');F=index(data['forms'],'forms');A=index(data['abilities'],'abilities');families=index(data['families'],'families');G=index(data['gates'],'gates');T=index(data['trials'],'trials')
    check(list(S)==list(range(1,129)),'slots: exact IDs 1..128 required')
    check(data['phase_order']==PHASES,'phase_order: incorrect five phases')
    check(data['generation_cycle']==[list(e) for e in GENERATION],'generation_cycle: incorrect order')
    check(data['control_cycle']==[list(e) for e in CONTROL],'control_cycle: incorrect order')
    check(data['polarity_values']==['yin','yang'],'polarity_values: incorrect values')
    if identity is not None:
        stable=[{k:s[k] for k in ('id','key','family_id','tier','rarity')} for s in data['slots']]
        check(isinstance(identity,dict) and identity.get('schema_version')==1 and stable==identity.get('slots'),'identity-lock: stable identity changed')
    planned=[];members=[]
    for family in data['families']:
        ids=family['form_ids'];members+=ids;edges=family['planned_edges'];planned+=edges
        shape=family['shape'];required={'linear_three':3,'branch_three':3,'linear_two':2,'single':1,'legendary_single':1}[shape]
        check(len(ids)==required,f'{family["id"]}: shape size mismatch')
        for i,id_ in enumerate(ids):
            if id_ not in S:check(False,f'{family["id"]}: unknown slot');continue
            check(S[id_]['family_id']==family['id'],f'{family["id"]}: wrong family owner')
            tier=1 if i==0 else 2 if shape=='branch_three' else i+1
            check(S[id_]['tier']==tier,f'{family["id"]}: wrong tier')
            check((S[id_]['rarity']=='legendary')==(shape=='legendary_single'),f'{family["id"]}: wrong rarity')
        if len(ids)==required:
            expected=[] if required==1 else [[ids[0],ids[1]]] if required==2 else [[ids[0],ids[1]],[ids[0] if shape=='branch_three' else ids[1],ids[2]]]
            check(edges==expected,f'{family["id"]}: graph does not match reserved shape')
    check(sorted(members)==list(range(1,129)),'families: every slot must belong exactly once')
    check([s['id'] for s in data['slots'] if s['rarity']=='legendary']==list(range(121,129)),'slots: legendary IDs must be 121..128')
    acyclic(S,planned,'planned evolution')
    for s in data['slots']:
        check((s['status']!='reserved')==(s['id'] in F),f'form {s["id"]}: content status mismatch')
        check(s['key']==f'FORM_{s["id"]:03d}',f'form {s["id"]}: stable key mismatch')
    field=set(data['field_capabilities']); check(data['field_capabilities']==(LEGACY_FIELD_CAPABILITIES if version==1 else FIELD_CAPABILITIES),'field_capabilities: reviewed append-only bit order required')
    check(len({a['handler'] for a in A.values()})==len(A),'abilities: handler identity must be unique')
    for a in A.values():check(set(a['field_caps'])<=field,f'ability {a["id"]}: unknown field capability')
    check(len({f['name'] for f in F.values()})==len(F),'forms: names must be distinct')
    check(len({f['silhouette'] for f in F.values()})==len(F),'forms: silhouette descriptions must be distinct')
    signatures=[];legacy=[]
    for id_,f in F.items():
        if id_ not in S:continue
        s=S[id_]; signature=f['signature_ability']; signatures.append(signature)
        check(signature in A,f'form {id_}: missing signature ability')
        if signature in A:
            check(A[signature]['phase']==f['phase'],f'form {id_}: signature phase mismatch')
            check(set(f['field_caps'])<=set(A[signature]['field_caps']),f'form {id_}: signature cannot preserve field capabilities')
        check(set(f['field_caps'])<=field,f'form {id_}: unknown field capability')
        key='legendary' if s['rarity']=='legendary' else f'tier_{s["tier"]}'
        total=sum(f['stats'].values());check(total==f['stat_total']==data['stat_budgets'][key],f'form {id_}: stat budget mismatch')
        learn=f['learnset'];ids=[x['ability_id'] for x in learn]
        check(len(ids)==len(set(ids)),f'form {id_}: duplicate learnset ability')
        check(learn==sorted(learn,key=lambda x:(x['level'],x['ability_id'])),f'form {id_}: learnset must be sorted')
        check(any(x['level']==1 for x in learn),f'form {id_}: level-one command required')
        check(signature in ids,f'form {id_}: signature missing from learnset')
        for item in learn:check(item['ability_id'] in A,f'form {id_}: unknown learnset ability')
        acq=f['acquisition']
        if acq['kind']!='evolution':check(acq.get('gate') in G,f'form {id_}: missing acquisition gate')
        if 'legacy_spirit_index' in f:legacy.append((f['legacy_spirit_index'],id_));check(s['status']=='legacy_reference',f'form {id_}: legacy status required')
        if s['rarity']=='legendary':check(acq['kind']=='legendary_trial' and not acq['repeatable'],f'form {id_}: legendary acquisition must be unique trial')
    check(len(signatures)==len(set(signatures)),'forms: signature abilities must be distinct')
    check(sorted(legacy)==[(0,1),(1,4),(2,7),(3,10)],'legacy: exact companion mapping required')
    check(data['implemented_legacy_form_ids']==[1,4,7,10],'legacy: exact implemented list required')
    # Trial identity is family-local. Numeric bits may repeat across families only.
    bindings={}; family_keys=set(); family_bits=set(); allowed_masks={}
    if version>=2:
        authored_bindings=data['trial_bindings']
        check(authored_bindings==sorted(authored_bindings,key=lambda x:(x['family_id'],x['local_trial_id'])), 'trial_bindings: family/key order required')
        for t in authored_bindings:
            name,family,key,mask=t['trial_id'],t['family_id'],t['local_trial_id'],t['wire_mask']
            check(name in T,f'trial binding {name}: unknown trial')
            check(family in families,f'trial binding {name}: unknown family')
            check(name not in bindings,f'trial binding {name}: duplicate trial name')
            check((family,key) not in family_keys,f'trial binding {name}: duplicate same-family local key')
            check((family,mask) not in family_bits,f'trial binding {name}: duplicate same-family wire mask')
            check(mask & (mask-1)==0,f'trial binding {name}: wire mask must be one-hot u16')
            check(not (t['prerequisite_trial_mask'] & mask),f'trial binding {name}: self prerequisite')
            check(t['from_form_ids']==sorted(t['from_form_ids']),f'trial binding {name}: source order required')
            for source in t['from_form_ids']:
                check(source in F and source in S and S[source]['family_id']==family,f'trial binding {name}: source family mismatch or undesigned source')
            bindings[name]=t;family_keys.add((family,key));family_bits.add((family,mask))
            allowed_masks[family]=allowed_masks.get(family,0)|mask
        for t in authored_bindings:
            check(t['prerequisite_trial_mask'] & ~allowed_masks.get(t['family_id'],0)==0,f'trial binding {t["trial_id"]}: unknown prerequisite mask')
        trial_edges=[]
        for t in authored_bindings:
            for prerequisite in authored_bindings:
                if prerequisite['family_id']==t['family_id'] and prerequisite['wire_mask'] & t['prerequisite_trial_mask']:
                    trial_edges.append([prerequisite['trial_id'],t['trial_id']])
                    check(prerequisite['introduced_content_revision']<=t['introduced_content_revision'],f'trial binding {t["trial_id"]}: prerequisite introduced later')
        acyclic(bindings,trial_edges,'trial prerequisites')
    edges=[];targets=[];sources={}
    for e in data['evolutions']:
        a,b=e['from'],e['to'];edges.append([a,b]);targets.append(b);sources.setdefault(a,[]).append(b)
        check([a,b] in planned,f'evolution {a}->{b}: not in family graph')
        check(a in F and b in F,f'evolution {a}->{b}: both forms must be designed')
        check(e['required_gate'] in G and e['required_trial'] in T,f'evolution {a}->{b}: unknown gate or trial')
        if a in S and b in S:
            check(S[a]['family_id']==S[b]['family_id'],f'evolution {a}->{b}: cross-family edge')
            check(S[b]['tier']==S[a]['tier']+1,f'evolution {a}->{b}: tier must increase by one')
        if version>=2:
            t=bindings.get(e['required_trial'])
            check(t is not None,f'evolution {a}->{b}: missing family-qualified trial binding')
            if t is not None and a in S:
                check(t['family_id']==S[a]['family_id'] and a in t['from_form_ids'],f'evolution {a}->{b}: trial source/family mismatch')
        if a in F and b in F:
            check(F[a]['phase']==F[b]['phase'],f'evolution {a}->{b}: phase changed within family')
            check(set(F[a]['field_caps'])<=set(F[b]['field_caps']),f'evolution {a}->{b}: loses field capability')
            check(F[b]['acquisition']['kind']=='evolution',f'evolution {a}->{b}: target acquisition mismatch')
            old={x['ability_id'] for x in F[a]['learnset']};new={x['ability_id'] for x in F[b]['learnset']}
            check(old<=new,f'evolution {a}->{b}: loses inherited command')
            new_levels={x['ability_id']:x['level'] for x in F[b]['learnset']}
            for command in F[a]['learnset']:
                check(new_levels.get(command['ability_id'],51)<=command['level'],f'evolution {a}->{b}: delays inherited command')
            sig=F[b]['signature_ability'];levels=[x['level'] for x in F[b]['learnset'] if x['ability_id']==sig]
            check(not levels or levels[0]<=e['min_level'],f'evolution {a}->{b}: signature unavailable at evolution')
    for source, dests in sources.items():
        family=families.get(S[source]['family_id']) if source in S else None
        if len(dests)>1:
            check(family is not None and family['shape']=='branch_three' and len(dests)==2
                  and sorted([[source,d] for d in dests])==sorted(family['planned_edges']),
                  f'evolution {source}: repeated source requires exact reviewed branch topology')
    check(len(edges)==len({tuple(e) for e in edges}),'evolutions: duplicate edge')
    check(len(targets)==len(set(targets)),'evolutions: merging branches is not supported')
    for id_,f in F.items():
        if f['acquisition']['kind']=='evolution':check(id_ in targets,f'form {id_}: orphan evolution acquisition')
    acyclic(S,edges,'executable evolution')
    gate_edges=[]
    for g in G.values():
        for requirement in g['requires']:check(requirement in G,f'gate {g["id"]}: unknown prerequisite');gate_edges.append([requirement,g['id']])
    acyclic(G,gate_edges,'gates')
    legend_section='covenant_gates' if version==3 else 'legendary_gates'
    legends=index(data[legend_section],legend_section,'form_id')
    for id_,rule in legends.items():
        check(id_ in F and id_ in S and S[id_]['rarity']=='legendary',f'legendary gate {id_}: missing designed legendary')
        check(rule['gate'] in G and rule['trial'] in T,f'legendary gate {id_}: unknown gate or trial')
        if id_ in F:check(F[id_]['acquisition'].get('gate')==rule['gate'],f'legendary gate {id_}: acquisition mismatch')
        if version==3:
            i=id_-121
            expected=dict(form_id=id_,family_id=f'F{id_-68:03d}',gate=COVENANT_GATE_NAMES[i],
                trial=COVENANT_GATE_NAMES[i],area=70+i,source_namespace='CovenantRequest.UNIQUE_INVITE',
                source_token=i+1,covenant_index=22,covenant_bit=1<<i,receipt_index=23,receipt_bit=1<<i,
                objective_quest=61 if i<4 else 62,objective_bit=1<<(i%4),requires_quest_claim=60 if i<4 else 61,
                grant_level=36,grant_bond=60,grant_trial_flags=0,required_support_commands=COVENANT_SUPPORT_COMMANDS[i],
                serial_station_reassignment=True,required_phase_count=5 if i==0 else 0,
                opposite_polarity_switches=2 if i==0 else 0,repeatable=False,requires_confirmation=True)
            check(rule==expected,f'covenant gate {id_}: exact source, objective and support contract required')
            check(rule['family_id']==S[id_]['family_id'],f'covenant gate {id_}: family mismatch')
            check(G.get(rule['gate'],{}).get('requires')==['covenants_lower_ready' if i<4 else 'covenants_upper_ready'],
                  f'covenant gate {id_}: prerequisite mismatch')
    for id_ in F:
        if id_ in S and S[id_]['rarity']=='legendary':check(id_ in legends,f'form {id_}: legendary gate required')
    B=data['budget'];L=data['limits'];offsets=B['save_bank_offsets'];size=B['save_bank_bytes']
    check(L=={'max_level':50,'max_bond':100,'party_slots':4,'instance_slots':160,'equipped_abilities':2,'max_learnset':8,'max_ability_id':63 if version==1 else 255,'max_active_legendaries':1},'limits: authoring revision layout changed')
    check(B['instance_bytes']==24,'budget: instance record must remain 24 bytes')
    check(B['save_blocks']['instances']==L['instance_slots']*B['instance_bytes'],'budget: instance allocation mismatch')
    check(sum(B['save_blocks'].values())<=size,'budget: save payload exceeds bank')
    check(offsets==sorted(offsets) and offsets[0]>=256 and offsets[0]+size<=offsets[1] and offsets[1]+size<=B['sram_limit_bytes'],'budget: banks overlap legacy, each other, or SRAM limit')
    check(B['baseline_rom_bytes']+B['incremental_rom_cap_bytes']<=B['rom_limit_bytes'],'budget: ROM overflow')
    check(B['baseline_ewram_bytes']+B['incremental_ewram_cap_bytes']<=B['ewram_limit_bytes'],'budget: EWRAM overflow')
    check(B['baseline_iwram_bytes']+B['incremental_iwram_cap_bytes']<=B['iwram_code_limit_bytes'],'budget: IWRAM stack collision')
    sprite_bytes=128*B['sprite_w']*B['sprite_h']*B['sprite_bpp']//8*B['sprite_directions']*B['sprite_frames_per_direction']
    tables=128*B['form_rom_record_bytes']+L['max_ability_id']*B['ability_rom_record_bytes']+128*L['max_learnset']*B['learnset_pair_bytes']
    check(sprite_bytes+tables<=B['incremental_rom_cap_bytes'],'budget: graphics and tables exceed ROM allowance')
    return sorted(set(errors))

def validate_enabled(data, enabled):
    """Exact revision whitelist, separate from wider design/branch authoring support."""
    errors=[]
    if not isinstance(enabled,dict):return ['enabled: expected manifest object']
    revision=enabled.get('content_revision')
    if type(revision) is not int or revision not in REVISION_POLICY:
        return ['enabled: unsupported content revision']
    policy=REVISION_POLICY[revision]
    if revision>=4 and data['schema_version'] not in (2,3):
        errors.append('enabled: current content revision requires authoring schema 2 or 3')
    if revision==9 and data['schema_version']!=3:
        errors.append('enabled: Covenants requires authoring schema 3')
    for key,expected in [('enabled_form_ids',policy['forms']),('enabled_evolutions',policy['edges']),('enabled_ability_ids',policy['abilities'])]:
        if json.dumps(enabled.get(key))!=json.dumps(expected):
            errors.append(f'enabled: {key} differs from reviewed core table order')
    forms={f['id']:f for f in data['forms']}; abilities={a['id']:a for a in data['abilities']}
    if not set(policy['forms'])<=set(forms):errors.append('enabled: every form requires an authored definition')
    if not set(policy['abilities'])<=set(abilities):errors.append('enabled: every command requires an authored definition')
    selected=[forms[id_] for id_ in policy['forms'] if id_ in forms]
    if sum(len(f['learnset']) for f in selected)!=policy['learns']:
        errors.append(f'enabled: expected exactly {policy["learns"]} learnset entries')
    if sorted({l['ability_id'] for f in selected for l in f['learnset']})!=sorted(policy['abilities']):
        errors.append('enabled: learned commands differ from reviewed core')
    if revision>=9:
        for id_,signature in COVENANT_SIGNATURES.items():
            f=forms.get(id_)
            learns=([dict(level=1,ability_id=9),dict(level=30,ability_id=12)] if id_==121
                    else [dict(level=1,ability_id=signature)])
            if not f or f['signature_ability']!=signature or f['learnset']!=learns:
                errors.append(f'enabled: Covenant form {id_} command ownership differs')
        preserved={key:data[key] for key in ('families','evolutions','trial_bindings','field_capabilities')}
        # Authored edge order is deliberately independent of ROM manifest order.
        preserved['evolutions']=sorted(data['evolutions'],key=lambda e:(e['from'],e['to']))
        preserved.update(forms=[f for f in data['forms'] if f['id']<=120],
            abilities=[a for a in data['abilities'] if a['id']<=121],stilltide=forms.get(121),
            gates=[g for g in data['gates'] if g['id'] not in COVENANT_GATE_NAMES and not g['id'].startswith('covenants_')],
            trials=[t for t in data['trials'] if t['id'] not in COVENANT_GATE_NAMES])
        for key,value in preserved.items():
            digest=hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()
            if digest!=COVENANT_PRESERVATION_SHA256[key]:
                errors.append(f'enabled: accepted Shared Horizons or disabled Stilltide {key} changed')
    if revision>=8:
        for f in selected:
            signature=HORIZONS_SIGNATURES.get(f['id'])
            if signature is not None:
                inherited=HORIZONS_INHERITED_COMMANDS.get(f['id'])
                learns=([{'level':1,'ability_id':inherited},
                         {'level':34,'ability_id':signature}] if inherited is not None
                        else [{'level':1,'ability_id':signature}])
                if f['signature_ability']!=signature or f['learnset']!=learns:
                    errors.append(f'enabled: Shared Horizons form {f["id"]} command ownership differs')
            elif any(l['ability_id'] in HORIZONS_SIGNATURES.values() for l in f['learnset']):
                errors.append(f'enabled: Shared Horizons command assigned to prior form {f["id"]}')
        for e in data['evolutions']:
            if [e['from'],e['to']] in HORIZONS_EDGES and (
                    e['min_level']!=34 or e['min_bond']!=60 or
                    e['required_gate']!='horizons_ready'):
                errors.append('enabled: Shared Horizons evolution floors or gate differ')
    # A current append may start at a released evolved form. Older manifests
    # ignore only explicitly reviewed future edges, never arbitrary extras.
    future_edges={tuple(edge) for rev,p in REVISION_POLICY.items() if rev>revision
                  for edge in p['edges'] if edge not in policy['edges']}
    edges=[[e['from'],e['to']] for e in data['evolutions']
           if (e['from'] in policy['forms'] or e['to'] in policy['forms'])
           and (e['from'],e['to']) not in future_edges]
    if sorted(edges)!=sorted(policy['edges']):errors.append('enabled: evolution graph differs from reviewed core')
    # Generating current ROMs uses reviewed wire maps, not arbitrary authored bits.
    for e in data['evolutions']:
        if [e['from'],e['to']] in policy['edges']:
            if e['required_gate'] not in GATE_MASKS:errors.append('enabled: unreviewed evolution gate')
            trial=TRIAL_POLICY.get(e['required_trial'])
            if trial is None or e['from'] not in trial[4] or trial[3]>revision:
                errors.append('enabled: unreviewed family-qualified evolution trial')
    if data['schema_version']>=2:
        enabled_families={s['family_id'] for s in data['slots'] if s['id'] in policy['forms']}
        expected={name:value for name,value in TRIAL_POLICY.items() if value[3]<=revision}
        actual={t['trial_id']:t for t in data['trial_bindings']
                if t['family_id'] in enabled_families
                and TRIAL_POLICY.get(t['trial_id'], ('',0,0,0,()))[3]<=revision}
        if set(actual)!=set(expected):errors.append('enabled: trial bindings differ from reviewed revision')
        for name,value in expected.items():
            t=actual.get(name)
            if t is None:continue
            got=(t['family_id'],t['local_trial_id'],t['wire_mask'],t['introduced_content_revision'],tuple(t['from_form_ids']))
            if got!=value or t['prerequisite_trial_mask']!=TRIAL_PREREQUISITES.get(name,0):
                errors.append(f'enabled: trial binding {name} differs from reviewed revision')
    # Current family identity is stable except these two individually authored
    # branch targets. A broad family exception would silently admit other flips.
    slots={s['id']:s for s in data['slots']}
    roots={f['id']:min(f['form_ids']) for f in data['families']}
    for f in selected:
        root=forms.get(roots[slots[f['id']]['family_id']])
        expected=CURRENT_POLARITY_OVERRIDES.get(f['id'],root['polarity'] if root else None)
        if f['polarity']!=expected:errors.append(f'enabled: unreviewed per-form polarity {f["id"]}')
    from released_policy import validate_compatibility
    errors += validate_compatibility(data, revision)
    return sorted(set(errors))

def summary(data, enabled=None):
    b=data['budget'];canonical=json.dumps(data,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()
    enabled = enabled or load_json(ROOT/'enabled.json')
    return {'valid':True,'scope':'Authored design catalog and separately reviewed native core data; not a gameplay acceptance result',
            'original_authoring_scope':data['scope'],'reserved_identities':len(data['slots']),
            'authored_designs':len(data['forms']),'enabled_native_core_forms':len(enabled['enabled_form_ids']),
            'enabled_form_ids':enabled['enabled_form_ids'],'enabled_abilities':len(enabled['enabled_ability_ids']),
            'enabled_evolution_edges':len(enabled['enabled_evolutions']),
            'native_obtainability':'Must be verified by separate native acquisition, art, ability and UI tests',
            'disabled_authored_forms':sorted(set(f['id'] for f in data['forms'])-set(enabled['enabled_form_ids'])),
            'reserved_only_forms':sum(s['status']=='reserved' for s in data['slots']),
            'families':len(data['families']),'authored_evolutions':len(data['evolutions']),
            'save_payload_bytes':sum(b['save_blocks'].values()),'save_bank_bytes':b['save_bank_bytes'],
            'catalog_sha256':hashlib.sha256(canonical).hexdigest()}

def main():
    p=argparse.ArgumentParser();p.add_argument('catalog',nargs='?',type=Path,default=ROOT/'catalog.json');p.add_argument('--identity-lock',type=Path,default=ROOT/'identity-lock.json');p.add_argument('--report',type=Path);p.add_argument('--enabled',type=Path,default=ROOT/'enabled.json');p.add_argument('--catalog-only',action='store_true',help='Validate archived authoring data without a runtime enablement manifest');args=p.parse_args()
    try:
        data=load_json(args.catalog);errors=validate(data,load_json(args.identity_lock))
        enabled=load_json(args.enabled) if not args.catalog_only else None
        if not errors and enabled is not None:errors += validate_enabled(data, enabled)
        result={'valid':False,'errors':errors} if errors else ({'valid':True,'schema_version':data['schema_version'],'authored_designs':len(data['forms']),'scope':'Catalog-only validation; no runtime enablement or native acceptance claim'} if args.catalog_only else summary(data,enabled))
    except (CatalogError,ValueError,OSError) as e:result={'valid':False,'errors':[str(e)]}
    out=json.dumps(result,ensure_ascii=False,indent=2)+'\n';print(out,end='')
    if args.report:args.report.write_text(out,encoding='utf-8')
    return 0 if result['valid'] else 1
if __name__=='__main__':sys.exit(main())
