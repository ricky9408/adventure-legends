#!/usr/bin/env python3
"""Synthetic full160/48 save, real room44 geometry and controller prop pushes.

Only canonical room/spawn are changed through the actual host codec. Native
play has no RAM writes or geometry overrides. An actual43→44 room entry starts
ordinary background saving before the authored prop-push sequence.
"""
from pathlib import Path
import argparse,ctypes as C,gzip,json,shutil,subprocess,sys,traceback
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'tests'),str(ROOT/'tools')]
from treasure_save_budget_probe import ProbeJourney
from journey_guidance_earned import StrictNative
from treasure_player_flow import Save,sha

def prepare(source,out):
 names=('save4.c','save5.c','creatures.c','creature_data.c','equipment.c','equipment_data.c','economy.c');so=out/'codec.so'
 subprocess.run(['cc','-std=c99','-O2','-Wall','-Wextra','-Werror','-ffreestanding','-fno-builtin','-DSAVE4_HOST_TEST','-DSAVE5_HOST_TEST','-shared','-fPIC',*[str(ROOT/'src'/n)for n in names],'-o',str(so)],check=True)
 l=C.CDLL(str(so));ram=(C.c_ubyte*32768).in_dll(l,'save5_test_sram');ram[:]=source.read_bytes()
 for n in ('save5_load','save5_store','save5_validate'):getattr(l,n).argtypes=[C.POINTER(Save)]
 s=Save();assert l.save5_load(C.byref(s))==1;before=Save.from_buffer_copy(bytes(s))
 assert sum(bool(c.flags&1)for c in s.roster.instances)==160 and sum(bool(g.item_id)for g in s.equipment.bag)==48
 s.campaign.room=43;s.campaign.spawn=0;assert l.save5_validate(C.byref(s))==1
 assert bytes(s.roster)==bytes(before.roster)and bytes(s.equipment)==bytes(before.equipment)and bytes(s.quests)==bytes(before.quests)and bytes(s.economy)==bytes(before.economy)
 assert l.save5_store(C.byref(s))==1;save=out/'synthetic-full160-gear48-room43.sav';save.write_bytes(bytes(ram));loaded=Save();assert l.save5_load(C.byref(loaded))==1
 assert bytes(loaded.roster)==bytes(before.roster)and bytes(loaded.equipment)==bytes(before.equipment)
 receipt={'synthetic':True,'source_sram':str(source),'source_sha256':sha(source),'output_sram':str(save),'output_sha256':sha(save),'host_codec_sha256':sha(so),'codec_translation_units':{n:sha(ROOT/'src'/n)for n in names},'edits':[{'field':'campaign.room','before':before.campaign.room,'after':43},{'field':'campaign.spawn','before':before.campaign.spawn,'after':0}],'roster_gear_quests_economy_bytes_preserved':True,'full_companions':160,'full_equipment':48,'codec_validated_before_and_after':True,'native_geometry_override':False}
 (out/'prepared-provenance.json').write_text(json.dumps(receipt,indent=2)+'\n');return save,receipt

class FullPush(ProbeJourney):
 def report(self):
  super().report();p=self.out/'report.json'
  if p.is_file()and hasattr(self,'synthetic_origin'):
   d=json.loads(p.read_text());d.update(controller_only=False,synthetic_prepared_state=True,synthetic_origin=self.synthetic_origin,scope='Synthetic full-capacity canonical save; real native controller push coverage. Not earned acquisition or release acceptance.')
   p.write_text(json.dumps(d,indent=2)+'\n')

def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--probe','--candidate',dest='probe',type=Path,required=True)
 for n in ('origin-report','full-save','bridge','output'):p.add_argument('--'+n,type=Path,required=True)
 a=p.parse_args();assert not a.output.exists()or not any(a.output.iterdir());a.output.mkdir(parents=True,exist_ok=True)
 helpers={}
 for d,pattern in (('tests','*.py'),('tools','mgba_runner.py')):
  for f in (ROOT/d).glob(pattern):
   target=a.output/'helper-source'/d/f.name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(f,target);helpers[str(f.relative_to(ROOT))]=sha(target)
 (a.output/'helper-source-hashes.json').write_text(json.dumps(helpers,indent=2)+'\n')
 prepared,receipt=prepare(a.full_save,a.output)
 manifest_file=a.probe/('probe.json'if(a.probe/'probe.json').exists()else'candidate.json');manifest=json.loads(manifest_file.read_text());expected=manifest['candidate']if isinstance(manifest.get('candidate'),dict)else{k:v['sha256']for k,v in manifest['files'].items()};a.rom=(a.probe/'emberbond.gba').resolve();a.symbols=(a.probe/'emberbond.sym').resolve();a.source_root=ROOT
 for n in ('emberbond.gba','emberbond.sym','emberbond.elf'):assert sha(a.probe/n)==expected[n]
 a.expected_rom_sha=sha(a.rom);a.expected_symbols_sha=sha(a.symbols);a.candidate={'rom_sha256':sha(a.rom),'symbols_sha256':sha(a.symbols),'elf_sha256':sha(a.rom.with_suffix('.elf')),'source_manifest_sha256':sha(a.probe/'source-hashes.json')if(a.probe/'source-hashes.json').exists()else sha(manifest_file),'source_manifest_kind':'source-complete frozen manifest'if(a.probe/'source-hashes.json').exists()else'diagnostic linked-object manifest','bridge_sha256':sha(a.bridge)}
 a.baseline=False;a.cross_rom_diagnostic=True;a.diagnostic_boundary_report=a.origin_report;a.stop_after='magma'
 source=Path(json.loads(a.origin_report.read_text())['snapshots']['south-south-main-before-continue']['sram_path']);r=None
 try:
  r=FullPush(a,source,a.origin_report);r.e.close();r.session+=1;r.e=StrictNative(r.rom,r.bridge);r.e.load_save(prepared);r.e.reset();r.synthetic_origin=receipt;r.provenance.update(synthetic_prepared_state=True,synthetic_origin=receipt,source_scope='Generated full-capacity canonical room43 save; no native geometry/RAM overrides')
  r.mode='cold_continue';r.raw_step(160);r.check(r.get('game_state')==0 and r.get('has_save')==1,'native title recognizes the codec-prepared full-capacity save');r.tap('A',4,4)
  for _ in range(1500):
   if r.get('game_state')==1 and r.get('frame')>0:break
   r.raw_step(1)
  r.settle();r.drain_background();r.mode='journey';r.chapter='magma-full-capacity';r.main_only=True;r.room44_rows=[]
  r.check(r.get('room')==43,'prepared save cold-loads canonical room43');r.check(sum(bool(c.flags&1)for c in r.state().roster.instances)==160 and sum(bool(g.item_id)for g in r.state().equipment.bag)==48,'native state really fills160 companion and48 gear records')
  r.equip_item(0,1);r.entry(44);r.clear_enemies();before=r.state();r.check(r.get('room')==44,'actual road reaches authored room44');r.slide(0,['DOWN','DOWN']+['RIGHT']*6+['UP','UP']);r.slide(1,['LEFT']+['UP']*3,side=2)
  r.check(list(r.e.bytes(r.sym['magma_game_puzzle'],2))==[20,4],'real controller pushes complete both authored prop sequences');r.drain_background();after=r.state()
  r.check(bytes(after.roster.instances)==bytes(before.roster.instances)and bytes(after.equipment.bag)==bytes(before.equipment.bag),'push/save preserves every companion and gear record')
  r.check(any(x['save_background']and x['grab']!=255 and x['keys']in ('RIGHT','LEFT','UP','DOWN')for x in r.room44_rows),'real prop movement overlaps ordinary background saving')
  r.history=['synthetic-full-capacity-room44'];r.route_complete=True;r.snapshot('full-capacity-push-finished')
 except Exception as ex:
  traceback.print_exc()
  if r:r.failures.append({'error':repr(ex),'status':r.status()});r.e.screenshot(r.out/'failure.png')
 finally:
  if r:
   result=r.diagnostic_report();result.update(controller_only=False,synthetic_prepared_state=True,synthetic_origin=receipt,scope='Full160/48 canonical synthetic save; actual43→44 entry, enemies, prop geometry and controller push sequence; no RAM writes or geometry overrides.')
   (a.output/'diagnostic.json').write_text(json.dumps(result,indent=2)+'\n');r.close();print(json.dumps({k:v for k,v in result['room44'].items()if k!='rows'},indent=2))
 if not r:return 1
 return int(not result['route_complete']or bool(result['failures'])or any(result['room44'][k]for k in ('missed_updates','missed_flips','cycle_overruns')))
if __name__=='__main__':raise SystemExit(main())
