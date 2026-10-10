#!/usr/bin/env python3
"""Byte-exact old/new host state and ordered draw differential for the measured
off-center ring opening and unchanged/dirty shelter settling optimizations.
Read-only test getters are appended to temporary translation units only.
"""
from pathlib import Path
import argparse
import hashlib
import json
import subprocess

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--before', type=Path, required=True)
parser.add_argument('--output', type=Path, required=True)
args = parser.parse_args()
OUT = args.output.resolve()
OUT.mkdir(parents=True, exist_ok=True)
before = args.before.resolve()
after = ROOT / 'src/covenants_powers.c'
hook = '\nconst void *covenants_test_state(void){return &cast;}\nunsigned covenants_test_size(void){return sizeof cast;}\n'
prefix = (ROOT / 'tests/covenants_powers_host.c').read_text().split('static void invalid_contract')[0]
harness = prefix + r'''
extern const void *covenants_test_state(void);
extern unsigned covenants_test_size(void);
typedef struct {
 unsigned public_state[20];unsigned char raw_cast[240];
 int draw[25][4];unsigned char stamp_pixels[128];
} Record;
int main(void){unsigned command,direction,variant,n,i,scenario=0;Record record;
 assert(covenants_test_size()==240);
 for(command=124;command<=126;command+=2)for(direction=0;direction<4;direction++)for(variant=0;variant<10;variant++){
  snapshot_refuse=variant==8?1:variant==9?2:0;setup(command);face=(int)direction;
  if(variant>=3&&variant<=7){px=command==124?51:121;py=63;}
  if(variant==1)wall(114,98,1,5);
  if(variant==2){wall(92,84,8,1);wall(116,113,1,10);}
  if(variant>=3&&variant<=7){
   wall(0,0,5,320);wall(0,0,480,5);
   if(command==124)wall(75,27,90,74);
   else {wall(27,51,74,58);wall(139,115,46,48);}
  }
  field_count=2;targets[0][0]=px;targets[0][1]=py-24;targets[0][2]=3;
  targets[1][0]=px+16;targets[1][1]=py;targets[1][2]=3;
  assert(covenants_power(command));
  for(n=0;n<150;n++){
   if(n==17&&variant==3&&command==124){wall_count=2;wall(75,27,90,29);wall(75,72,90,29);}
   if(n==17&&variant==4){wall_count=0;revision++;covenants_powers_geometry_changed();}
   if(n==105&&variant==5)wall(px-1,py-18,3,1);
   if(n==105&&variant==6){revision++;covenants_powers_geometry_changed();}
   if(n==105&&variant==7)covenants_powers_selection_changed();
   tick();memset(&record,0,sizeof record);
   record.public_state[0]=scenario;record.public_state[1]=n;record.public_state[2]=command;
   record.public_state[3]=(unsigned)covenants_power_kind;record.public_state[4]=(unsigned)covenants_power_time;
   record.public_state[5]=(unsigned)covenants_power_form;record.public_state[6]=(unsigned)covenants_power_direction;
   record.public_state[7]=(unsigned)covenants_power_origin_x;record.public_state[8]=(unsigned)covenants_power_origin_y;
   record.public_state[9]=(unsigned)covenants_power_age;record.public_state[10]=(unsigned)covenants_power_cast_time;
   record.public_state[11]=(unsigned)ability_cd;record.public_state[12]=covenants_powers_beat();
   record.public_state[13]=covenants_powers_cast_token();record.public_state[14]=covenants_powers_caster_id();
   record.public_state[15]=covenants_powers_moving_objects();record.public_state[16]=field_accepts;
   record.public_state[17]=field_beats;record.public_state[18]=revoked;record.public_state[19]=draws;
   memcpy(record.raw_cast,covenants_test_state(),240);
   for(i=0;i<draws;i++){record.draw[i][0]=draw_x[i];record.draw[i][1]=draw_y[i];record.draw[i][2]=draw_off[i];record.draw[i][3]=draw_w[i];}
   memcpy(record.stamp_pixels,vram+GFX_OBJ_POWER_PIN,64);memcpy(record.stamp_pixels+64,vram+GFX_OBJ_WATER_DROP,64);
   assert(fwrite(&record,1,sizeof record,stdout)==sizeof record);
  }
  scenario++;
 }
 return 0;
}
'''
(OUT / 'trace_harness.c').write_text(harness)
common = ['cc', '-std=c99', '-O1', '-g', '-Wall', '-Wextra', '-Werror', '-pedantic',
          '-Wno-misleading-indentation', '-Wno-unused-function', '-Wno-unused-const-variable',
          '-ffunction-sections', '-fdata-sections', '-Wl,--gc-sections', '-Isrc']
support = ['src/covenants_power_art.c', 'src/creatures.c', 'src/creature_data.c',
           'src/gear_runtime.c', 'src/combat_rules.c', 'src/north_art.c', 'src/south_art.c']
executables = []
for name, path in [('before', before), ('after', after)]:
    source = OUT / (name + '_with_readonly_hook.c')
    source.write_text(path.read_text() + hook)
    executable = OUT / name
    subprocess.run([*common, str(OUT/'trace_harness.c'), str(source), *support, '-o', str(executable)], cwd=ROOT, check=True)
    executables.append(executable)
processes = [subprocess.Popen([str(p)], stdout=subprocess.PIPE, stderr=subprocess.PIPE) for p in executables]
digest = hashlib.sha256()
count = 0
while True:
    left = processes[0].stdout.read(65536)
    right = processes[1].stdout.read(65536)
    if left != right:
        offset = next((i for i, (a, b) in enumerate(zip(left, right)) if a != b), min(len(left), len(right)))
        raise AssertionError(('state/draw mismatch', count+offset, left[offset:offset+32].hex(), right[offset:offset+32].hex()))
    if not left:
        break
    digest.update(left)
    count += len(left)
for process in processes:
    assert process.wait() == 0, process.stderr.read().decode()
report = {'scope': __doc__, 'commands': [124, 126], 'directions': 4, 'geometry_variants': 10,
          'scenarios': 80, 'active_and_expired_steps': 12000, 'compared_bytes': count,
          'trace_sha256': digest.hexdigest(), 'all_bytes_equal': True,
          'covered': ['all240 cast bytes including flags/order/count/beat/fields/owner/revocation',
                      'age/timers/cooldown/expiry and emitted ordered draws plus stamp pixels',
                      'actual51,63 ring23-to24 opening; actual121,63 shelter settling',
                      'all four rotations; new blocker/removal; geometry dirty exactly at shelter settle',
                      'selection invalidation exactly at settle; partial and over-capacity snapshots'],
          'before_sha256': hashlib.sha256(before.read_bytes()).hexdigest(),
          'after_sha256': hashlib.sha256(after.read_bytes()).hexdigest(),
          'helper_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
(OUT / 'report.json').write_text(json.dumps(report, indent=2)+'\n')
print(json.dumps(report, indent=2))
