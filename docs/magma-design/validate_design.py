#!/usr/bin/env python3
"""Read-only, design-only allocation + finite abstract puzzle checks.
No import from production code, no generator invocation and no runtime enablement.
"""
import argparse, copy, hashlib, json
from collections import deque, defaultdict
from pathlib import Path
from terminal_admission import build_policy, exhaustive_choice_order_proof
ROOT=Path(__file__).resolve().parent
EXPECTED_IDS=set(range(31,49))|set(range(95,101))
EXPECTED_FAMILIES={'F011','F012','F013','F014','F015','F016','F036','F037','F038'}
LOCK_SHA='fe553a9d963de059e7d6c0f8647ab6a3fe736c5fdf7ca8d3b18c6dedd3292969'
class DesignError(ValueError):pass
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'assets/creatures'))
from catalog_source import load_catalog

def need(x,m):
 if not x:raise DesignError(m)
def validate(p,lock,source=None):
 need(p['scope']=='DESIGN_ONLY_NOT_IN_ROM' and p['runtime_enablement'] is False,'runtime enablement forbidden')
 ids=[f['id'] for f in p['forms']]; need(len(ids)==24 and set(ids)==EXPECTED_IDS,'exact24 Magma identities')
 need(set(p['exact_new_form_ids'])==EXPECTED_IDS,'declared ID set differs')
 ls={s['id']:s for s in lock['slots']}; fs={f['id']:f for f in p['forms']}
 need(len(ls)==128 and set(ls)==set(range(1,129)),'128 locked identities')
 need(len(p['families'])==9 and {f['family_id'] for f in p['families']}==EXPECTED_FAMILIES,'nine agreed families')
 need(all(set(f['form_ids'])=={id for id in EXPECTED_IDS if ls[id]['family_id']==f['family_id']} for f in p['families']),'family allocation')
 for f in p['forms']:
  need(all(f[k]==ls[f['id']][k] for k in ('id','key','family_id','tier','rarity')),'immutable identity altered')
  need(f['runtime_enabled'] is False and f['status']=='design_only','form enabled')
  need(f['phase'] in ['wood','fire','earth','metal','water'] and f['polarity'] in ['yin','yang'],'phase/polarity explicit')
  need(sum(f['stats'].values())=={1:180,2:240,3:285}[f['tier']]==f['stat_total'],'exact tier stats')
  need(all(f[k] for k in ['silhouette','locomotion','combat_role','field_role']),'missing substantive design')
  need(1<=len(f['learnset'])<=8 and len({x['ability_id'] for x in f['learnset']})==len(f['learnset']),'learnset bounds')
  c=f['command'];need(1<=c['max_live_objects']<=3,'unbounded power objects')
  need(c['wall_checked'] and not c['player_invulnerability'] and not c['boss_control_effects'],'unsafe combat assumptions')
  need(all(0<int(x)<=180 for x in c['timing_updates'].values()),'bounded timing')
 need({f['signature_ability'] for f in p['forms']}==set(range(43,67)),'24 explicit unique commands43–66')
 need(set(p['namespace']['commands'])==set(range(43,67)),'command namespace')
 need(12 not in p['namespace']['commands'] and not EXPECTED_IDS.intersection(range(121,129)),'legendary or command12 activated')
 need(p['namespace']['new_capabilities']==[],'new capability outside design scope')
 trials={(t['family_id'],t['local_trial_key']):t for t in p['trial_bindings']}
 need(len(trials)==15==len(p['trial_bindings']),'15 distinct family-qualified trials')
 for t in trials.values():
  mask=t['wire_mask'];need(0<mask<=32768 and not mask&(mask-1),'trial mask must be u16 onehot')
  same=[x for x in trials.values() if x['family_id']==t['family_id'] and x is not t]
  need(all(x['wire_mask']!=mask for x in same),'same-family mask alias')
  need(t['local_trial_key'] in (1,2) and mask==(1<<(t['local_trial_key']-1)),'reviewed local key allocation')
  need(t['prerequisite_mask']==(1 if t['family_id'] in ['F011','F012'] and t['local_trial_key']==2 else 0),'trial prerequisite')
  need(t['same_instance_required'] and t['environmental_proof'],'personal trial proof')
 edges={(e['from'],e['to']):e for e in p['evolutions']}
 expected_edges={(31,32),(32,33),(34,35),(35,36),(37,38),(37,39),(40,41),(40,42),(43,44),(43,45),(46,47),(46,48),(95,96),(97,98),(99,100)}
 need(set(edges)==expected_edges and len(p['evolutions'])==15,'exact locked evolution edges')
 for e in edges.values():
  a,b=fs[e['from']],fs[e['to']];need(a['family_id']==b['family_id']==e['family_id'],'cross-family edge')
  need(b['tier']>a['tier'],'edge tier order')
  t=trials[(e['family_id'],e['local_trial_key'])]
  need(e['required_mask']==t['wire_mask']|t['prerequisite_mask'],'edge subset mask')
  need(set(a['field_caps'])<=set(b['field_caps']),'lost field capability')
  need(all(x in b['learnset'] for x in a['learnset']),'lost/delayed inherited command')
  need(e['min_level']==t['level_floor'] and e['min_bond']==t['bond_floor'],'trial must avoid grinding')
  need(e['explicit_target_confirmation'] and e['sanctuary'],'implicit evolution')
  need('historical_policy_isolation' in e['activation_gates'] and 'multi_trial_subset_policy' in e['activation_gates'],'missing architecture gate')
 need({x['name']:x['mask'] for x in p['contexts']}=={'MAGMA_READY':256,'CALDERA_OPEN':512},'derived context allocation')
 need(p['limits']['instance_slots']==160 and p['limits']['instance_bytes']==24 and p['limits']['wire_version']==5,'wire widened')
 need(p['limits']['save_used_bytes']==5056 and p['limits']['save_bank_bytes']==6144,'save banks changed')
 need(p['limits']['new_iwram_bytes']==0 and p['limits']['new_permanent_obj_bytes']==0,'memory contract')
 need(p['limits']['party_slots']==4 and p['limits']['rom_limit_bytes']==32*1024*1024,'hardware contract')
 admission=p.get('terminal_admission',{})
 need(admission.get('scope')=='forward_gameplay_mutations_only','missing forward admission gate')
 need((admission.get('capacity'),admission.get('full_planned_terminal_opportunities'),admission.get('extra_copy_budget'))==(160,72,88),'terminal opportunity budget')
 need(admission.get('safe_predicate')=='occupied - viable_coverage <= 88','admission invariant')
 need(admission.get('uses_obtained_or_seen_history') is False,'history cannot provide viable coverage')
 need(admission.get('bank_validation_uses_budget') is False and admission.get('legacy_normalization_or_deletion') is False,'admission must not reinterpret old saves')
 need(admission.get('legacy_overbudget_completion_guaranteed') is False,'impossible legacy recovery claim')
 need(admission.get('source_refusal_is_byte_unchanged') and admission.get('duplicate_source_retry_precedes_admission'),'atomic/idempotent admission')
 tp=build_policy(lock)
 expected_terminal_rows=[{'form_id':form,'family_id':row.family,'reachable_terminal_mask':row.terminal_mask,'terminal_form_ids':list(row.terminals)} for form,row in sorted(tp.items())]
 need(admission.get('form_terminal_masks')==expected_terminal_rows,'terminal coverage topology changed')
 need(any(g['key']=='terminal_opportunity_admission' and g['status']=='required_before_activation' for g in p['gates']),'missing activation gate')
 need(all('terminal_opportunity_admission' in e['activation_gates'] for e in p['evolutions']),'evolution admission bypass')

 milestones=p['authoritative_allocation']['milestones'];allids=[id for m in milestones for id in m['ids']]
 need(len(allids)==128 and set(allids)==set(range(1,129)),'full plan must cover128 exactly once')
 need([sum(len(m['ids']) for m in milestones[:i+1]) for i in range(6)]==[41,65,89,104,120,128],'milestone totals')
 need(len(p['baseline']['enabled_form_ids'])==41 and not EXPECTED_IDS.intersection(p['baseline']['enabled_form_ids']),'baseline collision')
 need(p['cumulative_after_acceptance']['minimum_retained_individuals_for_all_branches']==21+9+4,'minimum retained collection34')
 need({r['id'] for r in p['rooms']}==set(range(38,46)) and len(p['rooms'])==8,'exact room allocation')
 need({q['id'] for q in p['quests']}==set(range(30,38)) and len(p['quests'])==8,'exact quest allocation')
 need({q['id']:q['mask'] for q in p['quests']}==dict(zip(range(30,38),[3,3,15,7,3,3,3,7])),'exact quest masks')
 need(len([q for q in p['quests'] if q['kind']=='optional'])==5 and p['optional_discovery_commission']['global_quest_id'] is None,'side-content budget')
 need(next(q for q in p['quests'] if q['id']==32)['allowed_prefixes']==[0,1,3,7,15],'main prefix contract')
 need({q['recruit'] for q in p['quests'] if q['kind']=='teaching'}=={31,34},'guaranteed heat/weight providers')
 # Unconditional retreat to a sanctuary from each room, even with an empty party.
 graph=defaultdict(set)
 for link in p['links']:
  if not link['requires']:graph[link['from']].add(link['to'])
 for start in range(38,46):
  seen={start};todo=[start]
  while todo:
   x=todo.pop()
   for y in graph[x]-seen:seen.add(y);todo.append(y)
  need(bool({38,39}&seen),f'no unconditional retreat from{start}')
 gear=p['equipment'];need(len(gear)==6 and len({g['id'] for g in gear})==6,'six unique gear')
 need({g['source_id'] for g in gear}==set(range(25,31)),'stable new gear sources')
 need({g['source_id']:g['id'] for g in gear}=={25:20,26:37,27:53,28:67,29:85,30:5},'exact gear source relationships')
 need({g['quest_id']:g['source_id'] for g in gear}=={30:25,33:26,34:27,35:28,36:29,37:30},'exact quest gear relationships')
 need(all(not g['required_for_progression'] for g in gear),'mandatory gear gate')
 need(len(p['field_sources'])==7 and {s['bit'] for s in p['field_sources']}==set(range(7)) and all(s['region_byte']==9 for s in p['field_sources']),'seven field source bits')
 need(p['optional_discovery_commission']['discovery_byte']==19 and p['optional_discovery_commission']['allowed_prefixes']==[0,1,3,7],'discovery commission namespace')
 need(p['namespace']['discovery_byte']==19 and p['namespace']['discovery_mask']==7,'discovery mask')
 need(len(p['branch_sources'])==4 and {s['family_id'] for s in p['branch_sources']}=={'F013','F014','F015','F016'},'four real second-base sources')
 for s in p['branch_sources']:
  need(s['region_byte']==16 and s['first_receipt_retained_minimum']==2 and s['distinct_instance_ids'] and s['repeatable'] and s['no_history_cloning'],'branch acquisition semantics')
  need(s['inner_generic_reward_id']==0 and not s['subsequent_reward_credit'],'branch repeat farming')
 need([x['aid_index'] for x in p['trial_bindings']]+[x['aid_index'] for x in p['field_sources']]==list(range(40,62)),'aid allocation collision/order')
 ns=p['namespace'];all_events=ns['enemy_credit_ids']+ns['quest_credit_ids']+ns['reserved_credit_ids']
 need(len(all_events)==40 and set(all_events)==set(range(220,260)),'encounter/quest namespace')
 if source:
  need(hashlib.sha256((source/'assets/creatures/identity-lock.json').read_bytes()).hexdigest()==LOCK_SHA,'source identity lock changed')
  current=load_catalog(source/'assets/creatures/catalog.json')
  runtime=json.loads((source/'assets/creatures/enabled.json').read_text())
  need(runtime['content_revision']==4 and runtime['enabled_form_ids']==p['baseline']['enabled_form_ids'],'baseline changed; re-review before implementation')
  need(not EXPECTED_IDS.intersection(runtime['enabled_form_ids']),'design content unexpectedly enabled in inspected source')
  cf={x['id']:x for x in current['families']}
  for f in p['families']:
   need(f['shape']==cf[f['family_id']]['shape'] and f['form_ids']==cf[f['family_id']]['form_ids'],'locked topology differs')
  caps=set(current['field_capabilities'])
  need(all(set(f['field_caps'])<=caps for f in p['forms']),'capability not in existing registry')
  equipment=json.loads((source/'assets/equipment/catalog.json').read_text())
  need(not {g['id'] for g in gear}&{g['id'] for g in equipment['items']},'gear ID already allocated')
  for g in gear:
   for k,v in g['stats'].items():
    lo,hi=equipment['stat_bounds'][k];need(lo<=v<=hi,f'gear stat outside bounds:{k}')
 return {'new_forms':24,'new_families':9,'new_evolution_edges':15,'new_qualified_trials':15,'new_learnset_rows':sum(len(f['learnset']) for f in p['forms']),'cumulative_forms':65,'cumulative_minimum_individuals':34,'global_quests':8,'optional_global_quests':5,'additional_optional_discovery_commissions':1,'equipment':6,'capability_bits_added':0,'iwram_bytes_added':0}

def abstract_puzzle_proof(room):
 """Exhaustive finite micro-layout. Not a pixel collision/native ROM proof.
 A reversible grab moves one bounded prop between orthogonal floor cells.
 No prop may occupy the always-open one-cell perimeter or the reset/exit.
 Powers require the selected guaranteed companion; flags model latched proof.
 """
 width,height=7,5;floor={(x,y) for x in range(width) for y in range(height)}
 solid={(3,2)} if room==42 else {(3,1)} if room==43 else {(3,1),(3,2)}
 floor-=solid;entry=(3,4);exit=(3,4)
 # Objects are floor props in a central play space, not rails; the boundary stays clear.
 propcells=({(x,y) for x in range(1,6) for y in range(1,4)}-solid)
 initialprops=((1,2),) if room==42 else ((1,1),(5,3))
 heat=(1,2);socket=(5,2);brace=(2,2);bafflegoal=(4,3)
 goalflags=1 if room==42 else 2 if room==43 else 7
 init=(entry,initialprops,0)
 def transitions(s):
  player,props,flags=s
  for dx,dy in [(1,0),(-1,0),(0,1),(0,-1)]:
   v=(player[0]+dx,player[1]+dy)
   if v in floor and v not in props:yield(v,props,flags),'walk'
  # A+direction slides an adjacent prop one tile orthogonally. Pull is deliberately supported.
  # Its destination cannot be the player or another prop. Player stays in its safe approach cell.
  for i,pos in enumerate(props):
   if abs(player[0]-pos[0])+abs(player[1]-pos[1])!=1:continue
   for dx,dy in [(1,0),(-1,0),(0,1),(0,-1)]:
    dest=(pos[0]+dx,pos[1]+dy)
    if dest not in propcells or dest==player or dest in props:continue
    pp=list(props);pp[i]=dest;yield(player,tuple(pp),flags),'move_prop'
  if room in (42,44) and props[0]==heat and abs(player[0]-heat[0])+abs(player[1]-heat[1])==1:
   yield(player,props,flags|1),'STORE_HEAT'
  if room in (43,44) and props[1]==bafflegoal and (room==44 or props[0]==brace) and abs(player[0]-brace[0])+abs(player[1]-brace[1])==1:
   yield(player,props,flags|2),'PRESS_WEIGHT'
  if room==44 and flags&3==3 and props[0]==socket and props[1]==bafflegoal and player==(5,3):
   yield(player,props,flags|4),'ANY_WEAPON_PIN'
 def goal(s):
  _,props,flags=s
  return flags&goalflags==goalflags and (props[0]==brace if room==43 else props[0]==socket) and (room==42 or props[1]==bafflegoal)
 queue=deque([init]);visited={init:None};rev=defaultdict(list);goals=[]
 while queue:
  s=queue.popleft()
  if goal(s):goals.append(s)
  for n,action in transitions(s):
   rev[n].append(s)
   if n not in visited:visited[n]=(s,action);queue.append(n)
 need(goals,f'room{room} has no abstract solution')
 # Every reachable state can reach a solved arrangement without reset.
 can=set(goals);queue=deque(goals)
 while queue:
  for prev in rev[queue.popleft()]:
   if prev not in can:can.add(prev);queue.append(prev)
 need(len(can)==len(visited),f'room{room}: abstract prop deadlock')
 # Verify player-only escape for every unique player/prop arrangement, no power or prop changes.
 arrangements={(s[0],s[1]) for s in visited}
 for player,props in arrangements:
  seen={player};todo=[player]
  while todo:
   x,y=todo.pop()
   for dx,dy in [(1,0),(-1,0),(0,1),(0,-1)]:
    v=(x+dx,y+dy)
    if v in floor and v not in props and v not in seen:seen.add(v);todo.append(v)
  need(exit in seen,f'room{room}: trapped player approach')
 # Find witness; logical reset maps every incomplete state to init without touching completion ledger.
 end=goals[0];witness=[]
 while visited[end]:prev,action=visited[end];witness.append(action);end=prev
 witness.reverse()
 return {'room':room,'reachable_abstract_states':len(visited),'states_with_no_reset_solution':len(can),'player_prop_arrangements_with_unconditional_exit':len(arrangements),'witness_actions':witness,'scope':'finite abstract micro-layout only; final pixels, input sweeps and native cadence untested'}

def acquisition_proof(p):
 """Constructive design witness with real roster identities and sequential party swaps.
 No XP grind, history cloning or optional old companions. Assumes authored manual
 acquisition scenes and trial proofs will be implemented as specified.
 """
 forms={f['id']:f for f in p['forms']};owned={};history=set(p['baseline']['enabled_form_ids']);nextid=22;witness=[]
 for family in p['families']:
  base=family['form_ids'][0];owned[nextid]=base;history.add(base)
  witness.append({'action':'acquire','source':family['initial_source'],'instance_id':nextid,'form':base});nextid+=1
 # Guaranteed main powers can be held in a party of2 with empty remaining slots.
 need({'store_heat','press_weight'}<=set(forms[owned[22]]['field_caps']+forms[owned[23]]['field_caps']),'mandatory base capability coverage')
 for family in p['families']:
  fid=family['family_id'];slot=next(i for i,x in owned.items() if forms[x]['family_id']==fid)
  es=[e for e in p['evolutions'] if e['family_id']==fid]
  if family['shape']=='branch_three':
   e=es[0];owned[slot]=e['to'];history.add(e['to']);witness.append({'action':'trial_floor_and_confirm_evolution','instance_id':slot,'target':e['to']})
   need(owned[slot] in family['form_ids'][1:],'branch unlock evidence')
   second=nextid;nextid+=1;owned[second]=family['form_ids'][0]
   witness.append({'action':'deterministic_new_base_encounter','source':family['branch_extra_source'],'instance_id':second,'form':family['form_ids'][0]})
   e=es[1];owned[second]=e['to'];history.add(e['to']);witness.append({'action':'other_trial_floor_and_confirm_evolution','instance_id':second,'target':e['to']})
  else:
   for e in es:
    need(owned[slot]==e['from'],'linear sequence')
    owned[slot]=e['to'];history.add(e['to']);witness.append({'action':'trial_floor_and_confirm_evolution','instance_id':slot,'target':e['to']})
 need(EXPECTED_IDS<=history and len(history)==65,'all65 form history reached')
 need(len(owned)+21==34 and len(set(owned))==13,'13 real new individuals')
 return {'forms_reached_in_design':65,'new_real_individuals':13,'total_real_individuals_including_baseline':34,'max_required_party_size':2,'witness':witness,'scope':'constructive design graph witness, not controller or implementation proof'}

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--allocation',type=Path,default=ROOT/'magma_allocation.json');parser.add_argument('--source',type=Path,default=ROOT.parent/'adventure-legends-southern');parser.add_argument('--report',type=Path);args=parser.parse_args()
 p=json.loads(args.allocation.read_text());lock=json.loads((ROOT/'identity-lock.snapshot.json').read_text())
 report={'status':'DESIGN_CHECKS_PASS','runtime_enabled':False,'allocation':validate(p,lock,args.source),'abstract_puzzles':[abstract_puzzle_proof(r) for r in [42,43,44]],'acquisition':acquisition_proof(p),'all_choice_order_capacity_proof':exhaustive_choice_order_proof(),'native_gameplay_tested':False,'save_codec_implemented':False}
 if args.report:
  need(args.report.resolve().is_relative_to(ROOT),'reports must stay inside design directory')
  args.report.write_text(json.dumps(report,indent=2)+'\n')
 print(json.dumps({'status':report['status'],'allocation':report['allocation'],'abstract_state_counts':[x['reachable_abstract_states'] for x in report['abstract_puzzles']],'native_gameplay_tested':False},indent=2))
if __name__=='__main__':main()
