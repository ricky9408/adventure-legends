#!/usr/bin/env python3
"""Read-only cold-SRAM diagnostic for the retained Underwater preview case.

Imports authenticated prior-candidate SRAM only, never its machine state.
This is a cross-ROM persistence/UI diagnostic, not current-ROM acquisition.
"""
import argparse,hashlib,json,sys,traceback
from pathlib import Path
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('source','helpers','producer','output'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();a.source=a.source.resolve();a.helpers=a.helpers.resolve();a.output=a.output.resolve();a.output.mkdir(parents=True,exist_ok=False)
    source=json.loads(a.producer.read_text())
    assert source['controller_only'] and source['game_ram_writes']==0 and not source['failures'] and all(c['passed'] for c in source['checks'])
    assert source['rom_sha256']=='d9e08d5e45f9df259305503f4f10be0ba56dc5db0e1265613aee630ab7a25cb3'
    rec=source['snapshots']['09-main-cleared-town'];sram=Path(rec['sram_path']);assert sha(sram)==rec['sram_sha256'] and len(rec['owned_form_ids'])==12
    rom=a.source/'build/emberbond.gba';sym=rom.with_suffix('.sym');manifest=a.source/'build/source-hashes.json';runtime=json.loads(manifest.read_text())
    assert all(sha(a.source/k)==v for k,v in runtime.items())
    sys.path.insert(0,str(a.helpers/'tests'))
    from underwater_journey import UnderwaterJourney,ReadOnlyGameEmulator
    from northern_journey import newest_bank
    assert int.from_bytes(newest_bank(sram.read_bytes())[12:14],'little')==7
    helper_names=('tests/underwater_journey.py','tests/magma_journey.py','tests/southern_journey.py','tests/region_journey.py','tests/northern_journey.py','tools/mgba_runner.py','tools/mgba_bridge.so')
    helpers={name:sha(a.helpers/name) for name in helper_names}
    class ColdOnly(ReadOnlyGameEmulator):
        def __init__(self,*args,**kwargs):
            super().__init__(*args,**kwargs);self.original_state=self.lib.eb_state
            def state(ptr,path,load):
                assert not load,'Cross-ROM diagnostics never load machine states'
                return self.original_state(ptr,path,0)
            self.lib.eb_state=state
        def state(self,path,load=False):
            assert not load,'Cross-ROM diagnostics never load machine states'
            return super().state(path,False)
    class Probe(UnderwaterJourney):
        def __init__(self):
            self.rows=None
            super().__init__(rom,sym,a.output/'engine',sha(rom),sha(sym),fixture=a.helpers/'tests/fixtures/v5-revision5-minimal/magma-minimal10-town.sav',source_manifest=manifest)
            self.e.close();self.e=ColdOnly(self.rom);self.e.load_save(sram);self.e.reset()
            self.provenance={'scope':'Authenticated D minimum12 SRAM cold-loaded for E UI diagnostic; no E acquisition claim','source_rom_sha256':source['rom_sha256'],'source_report_sha256':sha(a.producer),'source_sram_sha256':sha(sram),'cross_rom_machine_state_loaded':False}
        def step(self,n,keys=0):
            if self.rows is None:return super().step(n,keys)
            for _ in range(n):
                before=self.get('frame');page=self.e.read(0x04000000,2)&16
                super().step(1,keys);after=self.get('frame')
                self.rows.append({'hardware_frame':self.e.frame,'update_delta':(after-before)&0xffffffff,'page_flip':(self.e.read(0x04000000,2)&16)!=page,'cycles':self.get('render_cycles'),'state':self.get('game_state'),'room':self.get('room'),'keys':keys})
    result={'scope':'Cross-ROM SRAM-only native diagnostic; not E acquisition','rom_sha256':sha(rom),'symbols_sha256':sha(sym),'source_manifest_sha256':sha(manifest),'producer_report_sha256':sha(a.producer),'source_sram_sha256':sha(sram),'helper_sha256':helpers,'diagnostic_source_sha256':sha(__file__),'game_ram_writes':0,'machine_state_loads':0,'result':'RUNNING'}
    r=None
    try:
        r=Probe();r.step(150);r.tap('START',2,50);r.settle();assert r.get('room')==46 and len(r.live())==12
        r.target(120,72);r.target(340,72);r.owned_select(49);before=bytes(r.state());r.rows=[]
        r.open_tab(3);r.tap('SELECT',2,4);r.wait_evolution(require_ready=False)
        result['trace']=r.rows;r.rows=None
        result['bad_frames']=[x for x in result['trace'] if x['update_delta']!=1 or not x['page_flip'] or x['cycles']>=280896]
        result['maximum_render_cycles']=max(x['cycles'] for x in result['trace'])
        assert r.get('game_state')==7 and r.get('progression_evolution_reason')!=0
        r.e.screenshot(a.output/'ineligible-preview.png');r.tap('B',2,4);r.close_menu();assert bytes(r.state())==before
        assert not result['bad_frames'],result['bad_frames']
        result['result']='PASS'
    except Exception as exc:result.update(result='FAIL',error=str(exc),traceback=traceback.format_exc());print(result['traceback'])
    finally:
        result['runtime_and_helpers_unchanged']=all(sha(a.source/k)==v for k,v in runtime.items()) and all(sha(a.helpers/k)==v for k,v in helpers.items())
        if r:r.e.close()
        (a.output/'preview-diagnostic.json').write_text(json.dumps(result,indent=2)+'\n')
    print(result['result'],result.get('maximum_render_cycles'),len(result.get('bad_frames',[])))
    return int(result['result']!='PASS' or not result['runtime_and_helpers_unchanged'])
if __name__=='__main__':raise SystemExit(main())
