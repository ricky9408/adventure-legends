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
KEYWORDS={'$schema','$id','$defs','title','$ref','type','enum','const','properties','required','additionalProperties','items','minItems','maxItems','uniqueItems','minimum','maximum','minLength','maxLength','pattern'}

class CatalogError(ValueError):pass

def load_json(path):
    def pairs(items):
        d={}
        for k,v in items:
            if k in d:raise CatalogError(f'duplicate JSON key: {k}')
            d[k]=v
        return d
    def constant(value):raise CatalogError(f'non-finite JSON value: {value}')
    return json.loads(Path(path).read_text(encoding='utf-8'),object_pairs_hook=pairs,parse_constant=constant)

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
    schema=schema or load_json(ROOT/'catalog.schema.json')
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
    field=set(data['field_capabilities']); check(data['field_capabilities']==sorted(field),'field_capabilities: sort required')
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
    edges=[];targets=[]
    for e in data['evolutions']:
        a,b=e['from'],e['to'];edges.append([a,b]);targets.append(b)
        check([a,b] in planned,f'evolution {a}->{b}: not in family graph')
        check(a in F and b in F,f'evolution {a}->{b}: both forms must be designed')
        check(e['required_gate'] in G and e['required_trial'] in T,f'evolution {a}->{b}: unknown gate or trial')
        if a in F and b in F:
            check(set(F[a]['field_caps'])<=set(F[b]['field_caps']),f'evolution {a}->{b}: loses field capability')
            check(F[b]['acquisition']['kind']=='evolution',f'evolution {a}->{b}: target acquisition mismatch')
            old={x['ability_id'] for x in F[a]['learnset']};new={x['ability_id'] for x in F[b]['learnset']}
            check(old<=new,f'evolution {a}->{b}: loses inherited command')
            sig=F[b]['signature_ability'];levels=[x['level'] for x in F[b]['learnset'] if x['ability_id']==sig]
            check(not levels or levels[0]<=e['min_level'],f'evolution {a}->{b}: signature unavailable at evolution')
    check(len(edges)==len({tuple(e) for e in edges}),'evolutions: duplicate edge')
    check(len(targets)==len(set(targets)),'evolutions: merging branches is not supported')
    for id_,f in F.items():
        if f['acquisition']['kind']=='evolution':check(id_ in targets,f'form {id_}: orphan evolution acquisition')
    acyclic(S,edges,'executable evolution')
    gate_edges=[]
    for g in G.values():
        for requirement in g['requires']:check(requirement in G,f'gate {g["id"]}: unknown prerequisite');gate_edges.append([requirement,g['id']])
    acyclic(G,gate_edges,'gates')
    legends=index(data['legendary_gates'],'legendary_gates','form_id')
    for id_,rule in legends.items():
        check(id_ in F and id_ in S and S[id_]['rarity']=='legendary',f'legendary gate {id_}: missing designed legendary')
        check(rule['gate'] in G and rule['trial'] in T,f'legendary gate {id_}: unknown gate or trial')
        if id_ in F:check(F[id_]['acquisition'].get('gate')==rule['gate'],f'legendary gate {id_}: acquisition mismatch')
    for id_ in F:
        if id_ in S and S[id_]['rarity']=='legendary':check(id_ in legends,f'form {id_}: legendary gate required')
    B=data['budget'];L=data['limits'];offsets=B['save_bank_offsets'];size=B['save_bank_bytes']
    check(L=={'max_level':50,'max_bond':100,'party_slots':4,'instance_slots':160,'equipped_abilities':2,'max_learnset':8,'max_ability_id':63,'max_active_legendaries':1},'limits: version-one layout changed')
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
    """Review boundary for ROM data, independent of gameplay obtainability."""
    errors = []
    if not isinstance(enabled, dict):
        return ['enabled: expected manifest object']
    expected_ids = [1,2,4,5,7,8,10,11,13,14,16]
    expected_edges = [[1,2],[4,5],[7,8],[10,11],[13,14]]
    if type(enabled.get('content_revision')) is not int or enabled['content_revision'] != 2:
        errors.append('enabled: expected content revision 2')
    for key, expected in [('enabled_form_ids', expected_ids),
                          ('enabled_evolutions', expected_edges),
                          ('enabled_ability_ids', list(range(1,12)))]:
        # JSON canonical equality also rejects bool aliases for integer IDs.
        if json.dumps(enabled.get(key)) != json.dumps(expected):
            errors.append(f'enabled: {key} differs from reviewed core')
    forms = [f for f in data['forms'] if f['id'] in expected_ids]
    if [f['id'] for f in forms] != expected_ids:
        errors.append('enabled: every form requires an authored definition')
    if sum(len(f['learnset']) for f in forms) != 16:
        errors.append('enabled: expected exactly 16 learnset entries')
    if sorted({l['ability_id'] for f in forms for l in f['learnset']}) != list(range(1,12)):
        errors.append('enabled: learned commands differ from reviewed core')
    edges = [[e['from'],e['to']] for e in data['evolutions']
             if e['from'] in expected_ids or e['to'] in expected_ids]
    if edges != expected_edges:
        errors.append('enabled: evolution graph differs from reviewed core')
    return errors

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
    p=argparse.ArgumentParser();p.add_argument('catalog',nargs='?',type=Path,default=ROOT/'catalog.json');p.add_argument('--identity-lock',type=Path,default=ROOT/'identity-lock.json');p.add_argument('--report',type=Path);args=p.parse_args()
    try:
        data=load_json(args.catalog);errors=validate(data,load_json(args.identity_lock))
        enabled=load_json(ROOT/'enabled.json')
        if not errors: errors += validate_enabled(data, enabled)
        result={'valid':False,'errors':errors} if errors else summary(data, enabled)
    except (CatalogError,ValueError,OSError) as e:result={'valid':False,'errors':[str(e)]}
    out=json.dumps(result,ensure_ascii=False,indent=2)+'\n';print(out,end='')
    if args.report:args.report.write_text(out,encoding='utf-8')
    return 0 if result['valid'] else 1
if __name__=='__main__':sys.exit(main())
