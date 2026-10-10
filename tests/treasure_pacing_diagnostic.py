#!/usr/bin/env python3
"""Read-only exact-session timing diagnostic from a genuine prior SRAM export.

This is a replay diagnostic, never empty-SRAM acceptance. It adds hardware,
writer/preflight, input and completed-profile observations without RAM writes.
"""
from pathlib import Path
import argparse,gzip,json,shutil,sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'tests'),str(ROOT/'tools')]
from journey_guidance_earned import StrictNative
from journey_guidance_timing import iter_rows
from player_feedback_native import sha
from magma_journey import elf_locals

def main():
 p=argparse.ArgumentParser(description=__doc__)
 for n in ('journey','bridge','output'):p.add_argument('--'+n,type=Path,required=True)
 p.add_argument('--window',required=True);a=p.parse_args()
 assert not a.output.exists()or not any(a.output.iterdir());a.output.mkdir(parents=True,exist_ok=True)
 timing=json.loads((a.journey/'timing-report.json').read_text());w=next(x for x in timing['windows']if x['id']==a.window);section=a.journey/w['section']
 rom=section/'tested.gba';symbols=section/'tested.sym';elf=section/'tested.elf'
 assert sha(rom)==timing['candidate']['rom_sha256']and sha(symbols)==timing['candidate']['symbols_sha256']and sha(elf)==timing['candidate']['elf_sha256']and sha(a.bridge)==timing['candidate']['bridge_sha256']
 sym={r[2]:int(r[0],16)for l in symbols.read_text().splitlines()if len(r:=l.split())==3};locals=elf_locals(elf,rom)
 source=w['source'];assert source['kind']=='earned_sram'and sha(source['path'])==source['sha256']
 shutil.copyfile(__file__,a.output/'treasure_pacing_diagnostic.py');shutil.copyfile(source['path'],a.output/'source.sav')
 e=StrictNative(rom,a.bridge);e.load_save(a.output/'source.sav');e.reset()
 get=lambda n,width=4:e.read(sym[n],width)
 writer_names=('META','QUEST','EQUIPMENT','ENCODE','FINISH','CHECK_SNAPSHOT','SCAN_A','SCAN_B','PREPARE','CRC','INVALIDATE','CHECK_INVALIDATE','WRITE','VERIFY','COMMIT','FINAL')
 def observe():
  r={n:get(n)for n in ('game_state','room','frame','px','py','face','keys','pressed','prev_keys','render_cycles','render_world_cycles','render_card_cycles','render_actors_cycles','save_feedback_background','save_feedback_ordinary','save_requested','save_begin_cycles','save_step_cycles','writer_status','writer_phase','writer_position','writer_progress','writer_destination','writer_preemptible','writer_preempted','writer_economy','scene_present_phase','scene_actor_pending','toast_id','toast_ticks')if n in sym}
  r['writer_phase_name']=writer_names[r['writer_phase']]if r['writer_phase']<len(writer_names)else'UNKNOWN'
  r['preflight']={n:e.read(sym['preflight']+4*i)for i,n in enumerate(('live','generation','status','phase','index','stories'))}
  r['magma_puzzle']=list(e.bytes(sym['magma_game_puzzle'],4));r['magma_grab']=e.read(locals['magma_game.c:grab'][0],1)
  r['vcount']=e.read(0x04000006,2);r['keyinput']=e.read(0x04000130,2)
  serial=get('render_profile_serial')
  if not serial&1:
   profile={n:get('render_profile_'+n)for n in ('frame','state','room','world','card','actors','save_begin','save_step','update','save','render','music','deferred_actors','vblank_cycles','vblank_start','vblank_end','commit')}
   if get('render_profile_serial')==serial:r['completed_profile']={'serial':serial,**profile}
  return r
 expected={(r['session'],r['hardware_frame']):r for r in iter_rows(section/'native-frames.jsonl.gz')if r['session']==w['session']and r['hardware_frame']<=w['sample_through']};rows=[];differences=[]
 for command in iter_rows(section/'controller-inputs.jsonl.gz'):
  if command['session']!=w['session']:continue
  if e.frame>=w['sample_through']:break
  assert e.frame==command['emulator_frame']
  for _ in range(min(command['frames'],w['sample_through']-e.frame)):
   before=get('frame');page=e.read(0x04000000,2)&16;context=observe()if e.frame>=w['sample_from']-1 else None;e.frames(1,command['keys'])
   if e.frame<w['sample_from']:continue
   r={'hardware_frame':e.frame,'controller_keys':command['keys'],'delta':(get('frame')-before)&0xffffffff,'flip':bool((e.read(0x04000000,2)&16)!=page),'before':context,'after':observe(),'faults':e.lib.eb_faults(e.ptr)}
   reference=expected[(w['session'],e.frame)];current={'room':get('room'),'state':get('game_state'),'x':get('px'),'y':get('py'),'cycles':get('render_cycles'),'delta':r['delta'],'flip':r['flip']}
   changed={k:{'expected':reference[k],'observed':v}for k,v in current.items()if reference[k]!=v}
   if changed:differences.append({'frame':e.frame,'differences':changed})
   if abs(e.frame-w['first_bad_hw'])<=2:e.screenshot(a.output/f'frame-{e.frame}.png')
   rows.append(r)
 e.close();result={'diagnostic_only':True,'acceptance_claim':False,'candidate':timing['candidate'],'origin':source,'window':w['id'],'controller_only':True,'game_ram_writes':0,'machine_state_imports':0,'exact_reference_match':not differences,'differences':differences,'phase_source':'I2 src/save5.c writer enum and src/save5_preflight.inc six-word struct; read-only inspection','helper_sha256':sha(__file__),'sampled_frames':len(rows),'update_misses':sum(r['delta']!=1 for r in rows),'flip_misses':sum(not r['flip']for r in rows),'faults':max(r['faults']for r in rows),'frames':rows}
 (a.output/'diagnostic.json').write_text(json.dumps(result,indent=2)+'\n')
 print(json.dumps({k:v for k,v in result.items()if k not in ('frames','candidate','origin')},indent=2))
 return int(bool(differences)or bool(result['faults']))
if __name__=='__main__':raise SystemExit(main())
