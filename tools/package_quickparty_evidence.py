#!/usr/bin/env python3
"""Collect bounded, hash-checked evidence for the quick-companion candidate.

Run after make test, the inherited expedition regression and quickparty-video.
Raw traces and paired machine-state/SRAM files remain in ignored build/.
"""
from pathlib import Path
import hashlib,json,shutil
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'docs/quickparty'
REPORTS={
 'first-chapter':'build/qa/playthrough.json',
 'review':'build/review/review-tests.json',
 'exploration':'build/exploration/exploration-tests.json',
 'campaign-minimal':'build/campaign-qa/campaign-report.json',
 'campaign-optional':'build/campaign-optional/campaign-report.json',
 'fullscreen':'build/fullscreen-qa/fullscreen-report.json',
 'evolution-eight':'build/evolution-qa/evolution-report.json',
 'evolution-six':'build/evolution-six-hearts/evolution-report.json',
 'evolution-migrated':'build/evolution-migrated/evolution-report.json',
 'advanced-powers':'build/advanced-power-qa/advanced-power-report.json',
 'quickparty':'build/quickparty-qa/quickparty-report.json',
 'quickparty-evolved':'build/quickparty-evolved-qa/quickparty-report.json',
 'expeditions':'build/expedition-qa/expedition-report.json',
}
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def write(name,value):
 data=json.dumps(value,ensure_ascii=False,indent=2)+'\n'
 assert len(data.encode())<32000,(name,len(data.encode()))
 (OUT/name).write_text(data)
def chunks(name,rows):
 part=[];n=0
 for row in rows:
  if len(json.dumps(part+[row],ensure_ascii=False).encode())>22000:
   write(f'{name}-{n:02}.json',part);n+=1;part=[]
  part.append(row)
 if part:write(f'{name}-{n:02}.json',part)
def load_report(path,rom):
 r=json.loads((ROOT/path).read_text())
 assert r.get('rom_sha256',r.get('candidate',{}).get('rom_sha256'))==rom,(path,'wrong ROM')
 assert not r.get('failures'),(path,r.get('failures'))
 return r

def main():
 OUT.mkdir(exist_ok=True)
 for p in OUT.glob('assertions-*.json'):p.unlink()
 rom=sha(ROOT/'build/emberbond.gba');sym=sha(ROOT/'build/emberbond.sym')
 summary={'schema':1,'rom_sha256':rom,'symbols_sha256':sym,'rom_bytes':(ROOT/'build/emberbond.gba').stat().st_size,'save5_revision':1,'normal_game_ram_writes':0,'suites':{},'native_assertions':0,'timing':{},'limits':['Representative mGBA 0.10.5 measurements; physical hardware is unverified','Cold Continue checkpoint decoding remains a separately documented blocking transition','Raw source-contract and synthetic fault checks are not native-controller gameplay evidence']}
 for name,path in REPORTS.items():
  r=load_report(path,rom);passes=r.get('passes',[])
  summary['suites'][name]={'report':path,'report_sha256':sha(ROOT/path),'passes':len(passes),'failures':len(r.get('failures',[]))}
  summary['native_assertions']+=len(passes);chunks('assertions-'+name,passes)
  timings=r.get('performance',r.get('timing',[]))
  if timings:
   rows=[{k:v for k,v in scene.items() if k not in ('initial','final','samples','input_trace') and not isinstance(v,(dict,list))} for scene in timings]
   chunks('cadence-'+name,rows)
   summary['timing'][name]={'windows':len(rows),'hardware_frames':sum(s.get('hardware_frames',0) for s in rows),'maximum_cycles':max(s.get('maximum_cycles',s.get('peak_cycles',0)) for s in rows)}
 for name in ('minimal','optional'):
  path=f'build/campaign-performance-{name}/campaign-performance.json';r=load_report(path,rom)
  assert r['full_strict_60hz_pass']
  summary['timing']['campaign-'+name]={'strict_pass':True,'report_sha256':sha(ROOT/path),'coverage':r['coverage']}
  rows=[{k:v for k,v in scene.items() if k not in ('initial','final','samples') and not isinstance(v,(dict,list))} for scene in r['scenes']+r['transitions']]
  chunks('cadence-campaign-'+name,rows)
 fault=load_report('build/quickparty-synthetic-qa/quickparty-report.json',rom)
 summary['synthetic_faults']={'faults':fault['synthetic_faults'],'game_ram_writes':fault['synthetic_game_ram_writes'],'separate_from_native_assertion_total':True}
 capture=json.loads((ROOT/'build/quickparty-demo/capture.json').read_text());assert capture['rom_sha256']==rom
 write('player-demo.json',capture)
 fault_host=json.loads((ROOT/'build/party-assignment-fault.log').read_text());assert fault_host['passed']
 write('save-failure-host.json',fault_host)
 summary['host_modal_assignment_failure']={'passed':True,'native_gameplay':False,'verified_glyph_pixels':fault_host['verified_glyph_pixels'],'paused_wait_updates':fault_host['paused_updates_before_close']}
 for name in ('opening-picker-native.png','opening-party-native.png','opening-field-native.png'):
  shutil.copyfile(ROOT/'build/quickparty-demo'/name,OUT/name)
 summary['player_demo']={'seconds':capture['seconds'],'video_sha256':capture['video_sha256'],'scope':capture['scope']}
 write('summary.json',summary)
 print(json.dumps(summary,indent=2))
if __name__=='__main__':main()
