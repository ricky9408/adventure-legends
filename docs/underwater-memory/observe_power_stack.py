#!/usr/bin/env python3
"""Extra stack-only B coverage: all 16 genuinely retained Underwater forms.
Uses controller selection/casts and read-only canary observations. No state load.
"""
from pathlib import Path
import hashlib,json
import observe_stack as stack
ROOT=stack.ROOT;sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
stack.DIAG=ROOT/'build/underwater-memory-diagnostic-b/build'
source=ROOT/'build/underwater-b-debug03/underwater-journey.json';data=json.loads(source.read_text());snap=data['snapshots']['11-all89-earned-town'];save=Path(snap['sram_path'])
assert data['rom_sha256']=='e02c410824086957a9ee472185a384360e3f6c144b1693b875c05873d6603923' and data['controller_only'] and data['game_ram_writes']==0
assert sha(save)=='3481201401c7a5541f332aedc4689b444cbba2b32f38a434399facc466ed3992'==snap['sram_sha256']
receipt=json.loads((stack.DIAG.parent/'build-receipt.json').read_text());assert receipt['candidate_rom_sha256']==data['rom_sha256'] and receipt['diagnostic_rom_sha256']==sha(stack.DIAG/'emberbond.gba')
r=stack.ObservedJourney(stack.DIAG/'emberbond.gba',stack.DIAG/'emberbond.sym',ROOT/'build/underwater-memory-b-all16-powers',sha(stack.DIAG/'emberbond.gba'),sha(stack.DIAG/'emberbond.sym'),source_manifest=stack.DIAG/'source-hashes.json')
r.stack_observations=[];r.stack_pairing={'source_report':str(source),'source_report_sha256':sha(source),'source_rom_sha256':data['rom_sha256'],'snapshot':'11-all89-earned-town','sram_sha256':sha(save),'expected_individuals':50,'expected_history':89,'power_observer_script_sha256':sha(Path(__file__))}
r.provenance={**r.stack_pairing,'cross_rom_machine_state_loaded':False,'import_method':'cold authenticated SRAM only'}
try:
 r.e.load_save(save);r.e.reset();r.step(150);r.tap('START',2,50);r.settle()
 r.check(len(r.live())==50 and len(r.collection())==89,'all16 power probe cold imports actual50/89')
 forms=sorted(c.form_id for c in r.live() if 49<=c.form_id<=72)
 r.check(forms==[f for f in range(49,73) if (f-49)%3],'all16 retained evolved forms were genuinely earned')
 for form in forms:
  r.cast_position(form,176,184,1,67+form-49,'diagnostic-real-cast-'+str(form));r.observe('actual-field-cast-'+str(form))
 r.snapshot('diagnostic-all16-finished')
except Exception as exc:
 r.failures.append({'error':str(exc),'status':r.status()});r.observe('failure');raise
finally:r.report();r.stack_report();r.e.close()
