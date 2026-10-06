"""Generate developer cards from canonical compact design JSON, never player media."""
import json
from pathlib import Path
P=Path(__file__).resolve().parent
r=lambda n:json.loads((P/n).read_text())
forms=r('creature_forms.json');powers={x['form_id']:x for x in r('ability_contracts.json')};delta=r('catalog_delta.json');abilities={x['id']:x for x in delta['abilities']};trials={x['target_form_id']:x for x in r('trial_contracts.json')};sources={x['base_form_id']:x for x in r('acquisition_contracts.json')}
contrasts=[
 'Compare existing Skimkip79/Sailskip80 and Dewmedusa100: a mantled cuttlefish with forward living arms and lateral fin waves, not fish fins or a tasselled umbrella.',
 'Compare Coalcoil31 and Shellwaddle83: two opening chalk valves, hinge face and muscular foot, not a coiled gastropod shell or sideways walking claws.',
 'Compare Tangleaper25 and Swaylemur87: upright prehensile-tail body with small continuous fin motion, no quadruped/gecko or mammal limb silhouette.',
 'Compare Shellwaddle83 and Clipmantis85: low continuous U rim with six small feet and tail, then open portal/perforated stamp branches; never pincer crab or upright mantis recoloring.',
 'Compare Dripurchin99/Dewmedusa100 and Coalcoil31: tubular flexible body, visible face and separate warm crown; no rigid radial spines, umbrella ribs or external snail shell.',
 'Compare Midori4 and Dripurchin99: jointless soft arms plant and fold around a lifted face; gaps and changing asymmetry, no floating leaf body or spiny round body.',
 'Compare Runnelribbon42 and Quillstride94: legless continuous eel musculature inside separated metal collars, then a hinged elbow or two unequal body loops; not a flat sponge skirt or spiny mammal.',
 'Compare Dewmedusa100 and Chalklung40: transparent axial comb bands and short feeding lobes, then diagonal/triangular silhouettes; no umbrella cap, tube-foot tassels, sponge chimney or three-foot walk.'
]
lines=['# Underwater creature and command cards','', 'Developer-only proposal.24 forms, not implemented. Each native sprite is16×16; portraits32×32. Written shape distinctions are art acceptance criteria, not inspected pixels. All damage figures are base Q4 before existing phase/combat rules. Existing five-phase cycles remain unchanged.','']
for form in forms:
 fid=form['id'];fi=(fid-49)//3;base=49+fi*3;fam=17+fi;p=powers[fid];a=abilities[p['ability_id']]
 lines += [f"## {fid} {form['name']} · F{fam:03} · tier{1 if fid==base else 2}",'',f"{form['phase'].title()} / {form['polarity'].title()} · stats V/P/G/F/H: "+'/'.join(str(x) for x in form['stats'].values())+f" = {form['stat_total']}", '', '**Living form:** '+form['silhouette'], '', '**Locomotion:** '+form['motion'],'','**Existing-form distinction:** '+contrasts[fi], '',f"**Command{a['id']}: {a['name']}**",'',p['geometry'], '', '**Control:** '+p['control'], '',f"Startup{p['startup_updates']} updates; active{p['active_updates']}; lifetime≤{p['lifetime_updates']}; cooldown{p['cooldown_updates']}; target damage≤{p['damage_q4_per_target_max']}Q4. At most{p['max_moving_objects']} moving entities, six enemy slots with spawn-generation receipts.",'',f"**Versus existing commands{','.join(map(str,p['nearest_existing_ability_ids']))}:** {p['difference']}",'','**Field utility:** '+', '.join(form['field_caps'])+'. Exact tagged targets and actual cast proof only.','']
 if fid==base:
  lines+=['**Acquisition:** '+sources[fid]['first_flow'],'','**Second individual:** '+sources[fid]['repeat_flow'],'',f"**Branches:** {base+1} or {base+2}; both are tier2, each needs its own same-individual trial. This base command is inherited by both branches.",'']
 else:
  t=trials[fid]
  lines += [f"**Evolution:** {base}→{fid}; level28, bond45, underwater_ready, sanctuary and explicit target confirmation. Qualified trialF{fam:03}/key{t['local_trial_id']}, wire bit{t['wire_mask']}, no other branch prerequisite.",'','**Personal trial:** '+t['description'],'','**Pass condition:** '+t['success_predicate'],'','**Hint:** '+t['player_hint'],'','**Alternative path:** choosing this terminal does not unlock or mark the other; invite another real base and personally train it.','']
text='\n'.join(lines)+'\n';assert len(text.encode())<90000;(P/'CREATURE_CARDS.md').write_text(text)
lines=['# Underwater trials and repeat encounters','','Developer-only solutions. None are implemented. Trial source selection, geometry and per-instance receipts must be verified by actual native controls.','']
for source in r('acquisition_contracts.json'):
 fam=source['family_id'];base=source['base_form_id']
 lines += [f'## {fam}: base{base}, branches{base+1}/{base+2}','',f"First source {source['token']} in area{source['area']} at {source['position']}: {source['first_flow']}",'','Repeat invitation: '+source['repeat_flow'],'',source['repeat_transaction'],'']
 for t in r('trial_contracts.json'):
  if t['family_id']!=fam:continue
  lines += [f"### Key{t['local_trial_id']}: {t['id']} → form{t['target_form_id']}",'',f"Area{t['area']} at {t['position']}; exact base command{t['required_command']}; field aid{t['field_aid_index']} / event{t['xp_event_id']}",'',t['description'],'','Success: '+t['success_predicate'],'','Reset: '+t['reset'],'']
text='\n'.join(lines)+'\n';assert len(text.encode())<90000;(P/'TRIALS_AND_ACQUISITION.md').write_text(text)
