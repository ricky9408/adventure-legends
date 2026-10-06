#!/usr/bin/env python3
"""Validate proposed data against actual schemas and numeric reference sources."""
import copy,hashlib,importlib.util,json,re,sys
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parent;BASE=ROOT.parents[2]/'adventure-legends-magma'
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'assets/creatures'))
from catalog_source import load_catalog

def read(name):return json.loads((ROOT/name).read_text())
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def require(test,msg):
 if not test:raise AssertionError(msg)
def load_reference_validator():
 sys.path.insert(0,str(BASE/'assets/creatures'))
 spec=importlib.util.spec_from_file_location('uw_reference_validator',BASE/'assets/creatures/validate_catalog.py')
 mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);return mod

def validate():
 from jsonschema import Draft202012Validator
 a=read('underwater_allocation.json');d=read('catalog_delta.json');f=read('creature_forms.json');w=read('world_plan.json');t=read('trial_contracts.json');s=read('acquisition_contracts.json');powers=read('ability_contracts.json');road=read('completion_roadmap.json')
 Draft202012Validator(read('allocation.schema.json')).validate(a)
 old=load_catalog(BASE/'assets/creatures/catalog.json');merged=copy.deepcopy(old)
 merged['forms']+=f
 for key in ['abilities','evolutions','gates','trials','trial_bindings']:merged[key]+=d[key]
 merged['field_capabilities']+=d['new_field_capabilities']
 for sl in merged['slots']:
  if sl['id'] in d['new_form_ids']:sl['status']='proposed'
 for key in ['forms','abilities','gates','trials']:merged[key].sort(key=lambda x:x['id'])
 merged['evolutions'].sort(key=lambda x:(x['from'],x['to']))
 merged['trial_bindings'].sort(key=lambda x:(x['family_id'],x['local_trial_id']))
 b=a['budgets']
 merged['budget'].update({'baseline_rom_bytes':b['baseline_rom_bytes'],'baseline_ewram_bytes':b['baseline_ewram_data_bytes']+b['baseline_ewram_bss_bytes'],
  'baseline_iwram_bytes':b['baseline_iwram_code_bytes'],'incremental_rom_cap_bytes':b['incremental_rom_cap_bytes'],
  'incremental_ewram_cap_bytes':b['incremental_ewram_cap_bytes'],'incremental_iwram_cap_bytes':b['incremental_iwram_cap_bytes']})
 schema=json.loads((BASE/'assets/creatures/catalog.schema.json').read_text())
 Draft202012Validator(schema).validate(merged)
 identity=json.loads((BASE/'assets/creatures/identity-lock.json').read_text())
 validator=load_reference_validator()
 # In-memory proposed policy only; no reference module/file is rewritten.
 validator.FIELD_CAPABILITIES=merged['field_capabilities'][:]
 errors=validator.validate(merged,identity,schema);require(not errors,'catalog semantics: '+str(errors))
 original_policy=copy.deepcopy(validator.REVISION_POLICY)
 old_enabled=json.loads((BASE/'assets/creatures/enabled.json').read_text())
 new_enabled={'content_revision':6,'enabled_form_ids':old_enabled['enabled_form_ids']+list(range(49,73)),
 'enabled_ability_ids':old_enabled['enabled_ability_ids']+list(range(67,91)),
 'enabled_evolutions':old_enabled['enabled_evolutions']+[[e['from'],e['to']] for e in d['evolutions']]}
 validator.REVISION_POLICY=copy.deepcopy(validator.REVISION_POLICY)
 validator.REVISION_POLICY[6]={'forms':new_enabled['enabled_form_ids'],'abilities':new_enabled['enabled_ability_ids'],'edges':new_enabled['enabled_evolutions'],'learns':142}
 validator.TRIAL_POLICY=copy.deepcopy(validator.TRIAL_POLICY)
 for binding in d['trial_bindings']:
  validator.TRIAL_POLICY[binding['trial_id']]=(binding['family_id'],binding['local_trial_id'],binding['wire_mask'],6,tuple(binding['from_form_ids']))
 validator.GATE_MASKS=copy.deepcopy(validator.GATE_MASKS);validator.GATE_MASKS.update({'underwater_ready':1024,'palinode_open':2048})
 validator.CURRENT_POLARITY_OVERRIDES=copy.deepcopy(validator.CURRENT_POLARITY_OVERRIDES)
 for form in f:validator.CURRENT_POLARITY_OVERRIDES[form['id']]=form['polarity']
 errors=validator.validate_enabled(merged,new_enabled);require(not errors,'proposed enabled policy: '+str(errors))
 require({k:v for k,v in validator.REVISION_POLICY.items() if k<=5}==original_policy,'historical revision policy mutation')
 for key in ['forms','abilities','evolutions','gates','trials','trial_bindings']:
  for row in old[key]:require(row in merged[key],f'old {key} row changed')
 require(merged['families']==old['families'] and merged['slots'][:48]==old['slots'][:48],'identity/topology changed')
 require(set(new_enabled['enabled_form_ids']).isdisjoint(range(121,129)),'legendary enabled')
 require(12 not in new_enabled['enabled_ability_ids'],'legendary command12 enabled')
 for key in ['form_ids','ability_ids','area_ids','quest_ids','equipment_ids','equipment_reward_sources']:
  require(set(a['append'][key]).isdisjoint(a['existing_namespaces'][key]),f'{key} collision')
 require(len(a['append']['form_ids'])==24 and len(s)==8 and len(t)==16,'finite counts')
 require({x['family_id'] for x in t}==set(a['append']['family_ids']),'trial families')
 for fi in range(8):
  base=49+fi*3;fam=f'F{17+fi:03}'
  rows=[x for x in t if x['family_id']==fam]
  require({x['local_trial_id'] for x in rows}=={1,2} and {x['wire_mask'] for x in rows}=={1,2},'qualified local keys')
  require(all(x['from_form_id']==base and x['prerequisite_trial_mask']==0 for x in rows),'branch is not two independent paths')
  family=next(x for x in merged['families'] if x['id']==fam)
  require(family['shape']=='branch_three' and family['planned_edges']==[[base,base+1],[base,base+2]],'topology mutation')
  require(s[fi]['base_form_id']==base and s[fi]['repeat_first_extra_receipt']=={'byte':17,'bit':1<<fi},'repeat source mapping')
 require(len({p['primitive'] for p in powers})==24,'repeated geometry primitive')
 require(len({p['geometry'] for p in powers})==24,'repeated geometry contract')
 old_commands=set(old_enabled['enabled_ability_ids'])
 for p in powers:
  require(set(p['nearest_existing_ability_ids'])<=old_commands,'comparison to disabled/nonexistent old command')
  require(p['lifetime_updates']<p['cooldown_updates'] and p['damage_q4_per_target_max']<=24,'combat ceiling')
  require(p['max_moving_objects']<=3 and p['max_enemy_slots']==6,'bounded runtime')
 require({x['phase'] for x in f}==set(old['phase_order']),'missing phase')
 require({x['polarity'] for x in f}=={'yin','yang'},'missing polarity')
 ordinary=[]
 for e in a['append']['encounter_events']:ordinary+=range(e['first'],e['first']+e['count'])
 ordinary+=a['append']['quest_xp_event_ids']
 require(len(ordinary)==len(set(ordinary)),'new ordinary event collision')
 require(not set(ordinary)&set(a['existing_namespaces']['ordinary_events']),'old ordinary event collision')
 require(max(ordinary)<384,'ordinary/field event overlap')
 aids=a['append']['trial_field_aid_indices']+a['append']['source_field_aid_indices']
 require(len(aids)==len(set(aids)) and min(aids)==62 and max(aids)==83,'aid allocation')
 require(not set(aids)&set(a['existing_namespaces']['field_aid_indices_conservatively_reserved']),'old aid collision')
 require(max(384+x for x in aids)<512,'event capacity')
 oldbytes={int(x) for x in a['existing_namespaces']['region_flag_masks']}
 require(not oldbytes&{x['byte'] for x in a['append']['region_flags']},'region flag collision')
 require(max(x['byte'] for x in a['append']['region_flags'])<32,'region capacity')
 require({x['byte']:x['mask'] for x in a['append']['region_flags']}=={4:255,10:63,17:255,20:3,21:7},'exact region allocation')
 require(a['append']['anchor']['byte'] not in a['existing_namespaces']['anchor_bytes'],'anchor collision')
 require(max(a['append']['quest_ids'])<64 and max(a['append']['equipment_reward_sources'])<64,'quest/reward capacity')
 require(a['result_after_real_acceptance']['gear']<=48,'gear bag')
 require({x['reward_source']:x['item']['id'] for x in w['equipment']}=={31:6,32:13,33:38,34:54,35:68,36:86},'exact gear source mapping')
 require({x['id']:x['objective_mask'] for x in w['quests']}=={38:3,39:3,40:15,41:7,42:3,43:3,44:3,45:7},'exact quest masks')
 require(max(c['key'] for c in a['append']['capabilities'])<=32 and len(set(c['mask'] for c in a['append']['capabilities']))==4,'capability width')
 for c in a['append']['capabilities']:require(c['mask']==1<<(c['key']-1),'capability key/bit mismatch')
 require(sum(b['rom_line_items'].values())<=b['incremental_rom_cap_bytes'],'ROM design sum')
 require(sum(b['ewram_line_items'].values())<=b['incremental_ewram_cap_bytes'],'RAM design sum')
 require(b['baseline_rom_bytes']+b['incremental_rom_cap_bytes']<=b['rom_limit_bytes'],'ROM cap')
 require(b['baseline_iwram_code_bytes']+b['incremental_iwram_cap_bytes']<=b['iwram_code_limit_bytes'],'IWRAM stack collision')
 require(b['baseline_ewram_data_bytes']+b['baseline_ewram_bss_bytes']+b['incremental_ewram_cap_bytes']<=b['ewram_limit_bytes'],'EWRAM cap')
 require(b['obj_vram_used_end']+b['new_obj_vram_bytes']<=b['obj_vram_capacity'] and b['new_obj_vram_bytes']==0,'OBJ overflow')
 require(b['underwater_oam_hard_budget']<b['oam_engine_drop_threshold'],'OAM drops')
 lim=a['limits'];off=lim['save_bank_offsets'];size=lim['save_bank_bytes']
 require(off==[512,6656] and off[0]+size<=off[1] and off[1]+size<=32768,'SRAM overlap')
 require(lim['used_save_payload_bytes']+lim['reserved_tail_bytes']==size and size==6144 and lim['instance_wire_bytes']==24,'save layout change')
 maincaps=set().union(*(set(x['field_caps']) for x in f if x['id'] in [49,52]))
 require(all(set(p['required_caps'])<=maincaps for p in w['puzzles']),'main route needs optional companion')
 require(w['route_contract']['required_gear_ids']==[1] and not w['route_contract']['requires_evolution'],'main-route requirements')
 areas={x['id']:x for x in w['areas']}
 path=w['route_contract']['main_path']
 require(all(y in areas[x]['neighbors'] for x,y in zip(path,path[1:])),'main adjacency')
 reachable={46}
 while True:
  fresh=reachable|set(y for x in reachable for y in areas[x]['neighbors'])
  if fresh==reachable:break
  reachable=fresh
 require(reachable==set(range(46,54)),'isolated arena/area')
 require({x['id']:x['entry_objective_prefix'] for x in w['areas'] if x['id']>=50}=={50:0,51:1,52:3,53:7},'main-room prefix gates')
 for area in areas.values():
  for other in area['neighbors']:require(other in areas,'unknown portal area')
 for p in w['puzzles']:
  require(p['quest'] in [38,39,40] and p['objective_bit']>0 and not p['objective_bit']&(p['objective_bit']-1),'puzzle evidence identity')
 for q in w['quests']:
  require(q['id'] in a['append']['quest_ids'] and q['objective_mask'] in [3,7,15],'quest masks')
  require(q['xp_event_id']==280+q['id']-38,'quest/event independent explicit map')
 rforms=[x for milestone in road['milestones'] for x in milestone['new_form_ids']]
 require(len(rforms)==len(set(rforms)) and set(rforms)|set(old_enabled['enabled_form_ids'])==set(range(1,129)),'roadmap misses/duplicates identities')
 require(not set(rforms)&set(old_enabled['enabled_form_ids']),'roadmap repeats old enabled form')
 require(road['milestones'][-1]['retained']==72 and road['milestones'][-1]['cumulative_gear']==48,'completion reserve')
 rq=[x for milestone in road['milestones'] for x in milestone['quest_ids']]
 require(rq==list(range(38,64)),'finite quest roadmap')
 ra=[x for milestone in road['milestones'] for x in milestone['field_aid_indices']]
 require(ra==list(range(62,117)),'finite aid roadmap')
 # Re-audit concrete reference expressions, not only handwritten allocation arrays.
 events=(BASE/'src/progression_events.c').read_text()
 require('{39,220,5}' in events and '{45,231,1}' in events and 'if(area<=29)return area*6+slot;' in events,'encounter namespace changed')
 require('240+q-30' in (BASE/'src/magma_game.c').read_text(),'quest event namespace changed')
 require('40+i*2+key-1' in (BASE/'src/magma_quests.c').read_text(),'trial aid namespace changed')
 for name,h in a['source_hashes'].items():require(digest(BASE/name)==h,f'baseline changed: {name}; re-audit before implementation')
 for p in ROOT.iterdir():
  if p.is_file() and p.suffix in ['.json','.md','.txt','.py']:require(p.stat().st_size<90000,'file/chunk exceeds90KB: '+p.name)
 return {'status':'PASS','scope':'Static schema, semantic, namespace, topology and resource-budget design checks only. No Underwater native content exists.',
  'forms_added':24,'commands_added':24,'families':8,'qualified_trial_paths':16,'repeat_flows':8,'areas':8,'quests':8,'gear':6,
  'total_forms_after_acceptance':89,'retained_after_acceptance':50,'merged_catalog_schema':'catalog.schema.json schema2','merged_design_rows_including_disabled_121':len(merged['forms']),
  'proposed_revision6_enabled_learns':142,'rom_estimate_bytes':sum(b['rom_line_items'].values()),'rom_cap_bytes':b['incremental_rom_cap_bytes'],
  'baseline_iwram_bytes':b['baseline_iwram_code_bytes'],'iwram_increment_cap':b['incremental_iwram_cap_bytes'],
  'player_controller_acceptance':'NOT RUN: design only','pixel_art_review':'NOT RUN: design only','native_performance':'NOT RUN: design only',
  'baseline_sha256':digest(BASE/'build/emberbond.gba')}
if __name__=='__main__':
 report=validate();(ROOT/'validation_report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
