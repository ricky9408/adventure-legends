#!/usr/bin/env python3
"""Read-only diagnostic replay of a retained failed controller input trace."""
import argparse,hashlib,json,struct
from pathlib import Path
from horizons_journey import HorizonsEmulator
from observe_covenants_stack import symbols

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser();p.add_argument('--report',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--from-frame',type=int,default=19550);a=p.parse_args()
 source=json.loads(a.report.read_text());root=a.report.parent
 assert source['controller_only'] and not source['game_ram_writes'] and not source['machine_state_loads']
 assert sha(root/'tested.gba')==source['rom_sha256'] and sha(root/'tested.sym')==source['symbols_sha256']
 assert sha(root/'source-earned.sav')==source['provenance']['sram_sha256']
 a.output.mkdir(parents=True,exist_ok=False);sym=symbols(root/'tested.sym');e=HorizonsEmulator(root/'tested.gba');e.load_save(root/'source-earned.sav');e.reset();rows=[]
 def get(n):return e.read(sym[n])
 def observe(keys):
  return {'hardware_frame':e.frame,'keys':keys,**{n:get(n) for n in ('frame','game_state','px','py','hero_hp_q4','invuln','guard_invuln','roll_ticks','stone_guard','kills','deaths')},
   'enemies':[{'index':i,'x':getx[0],'y':getx[1],'hp':getx[2],'kind':getx[4],'hp_q4':e.read(sym['enemy_hp_q4']+i*4)} for i in range(6) for getx in [struct.unpack('<5i',e.bytes(sym['enemies']+20*i,20))]],
   'shots':[{'index':i,'x':v[0],'y':v[1],'dx':v[2],'dy':v[3],'life':v[4],'owner':v[5]} for i in range(12) for v in [struct.unpack('<6i',e.bytes(sym['shots']+24*i,24))] if v[4]>0]}
 try:
  for batch in source['inputs']:
   assert e.frame==batch['frame'],'This diagnostic expects the failed route before any cold reset'
   if e.frame+batch['frames']<a.from_frame:e.frames(batch['frames'],batch['keys']);continue
   for _ in range(batch['frames']):
    before=observe(batch['keys']);e.frames(1,batch['keys']);after=observe(batch['keys']);rows.append({'before':before,'after':after})
    if before['hero_hp_q4']!=after['hero_hp_q4'] or after['game_state']==4:
     e.screenshot(a.output/f'frame-{e.frame}.png')
    if after['game_state']==4:break
   if get('game_state')==4:break
  e.save(a.output/'terminal-native.sav')
  result={'suite':'retained-controller-death-replay','diagnostic_only':True,'release_acceptance':False,'controller_only':True,'game_ram_writes':0,'machine_state_loads':0,'producer_report_sha256':sha(a.report),'rom_sha256':source['rom_sha256'],'rows':rows,'terminal_sram_sha256':sha(a.output/'terminal-native.sav')}
  (a.output/'death-replay.json').write_text(json.dumps(result,indent=2)+'\n')
  for r in rows:
   if r['before']['hero_hp_q4']!=r['after']['hero_hp_q4']:print(json.dumps(r),flush=True)
 finally:e.close()
if __name__=='__main__':main()
