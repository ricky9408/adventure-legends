#!/usr/bin/env python3
from pathlib import Path
import ctypes as C,subprocess,tempfile,json
ROOT=Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory() as temp:
 p=Path(temp)/'field.so';subprocess.run(['cc','-std=c99','-O2','-Wno-misleading-indentation','-ffunction-sections','-fdata-sections','-Wl,--gc-sections','-Isrc','-Itests','tests/horizons_field_feasibility.c',*[f'src/{s}.c'for s in ('horizons_powers','horizons_power_art','horizons_art','creatures','creature_data','equipment','equipment_data','gear_runtime','combat_rules','north_art','south_art')],'-o',str(p)],cwd=ROOT,check=True)
 cases=[
 ('lintail repeat',106,62,384,176,2,352,176,352,176,0,1),
 ('talus repeat',110,66,24,240,3,48,240,48,240,0,1),
 ('gleam repeat',112,68,176,136,1,176,112,176,112,0,1),
 ('rivet repeat',114,63,48,88,1,48,64,48,64,0,1),
 ('shelter repeat',115,64,200,128,1,200,104,200,104,0,1),
 ('root repeat',120,62,320,264,1,320,240,320,240,0,1),
 ('warm main',108,67,300,208,2,288,208,312,208,12,9),
 ('warm repeat',108,63,404,96,2,392,96,416,96,12,9),
 ('rear wick',116,65,384,232,1,384,256,384,256,0,1),
 ('weight hold',117,67,64,166,1,64,144,64,144,0,1),
 ('short long',118,69,196,88,1,192,64,216,64,0,9),
 ('split bowls',119,66,52,180,1,48,160,72,160,0,9),
 ('vane fan',121,68,80,120,1,80,88,80,88,0,1),
 ('corner exhibit',107,63,336,54,0,336,64,368,96,0,9),
 ('warm exhibit',109,67,268,208,3,288,208,312,208,12,9),
 ('weight exhibit',111,66,132,256,3,144,248,176,248,0,9),
 ('glint exhibit',113,68,64,94,3,80,88,116,102,0,9)]
 result=[]
 for name,*args,want in cases:
  got=int(subprocess.check_output([str(p),*map(str,args)],text=True));result.append({'name':name,'command':args[0],'area':args[1],'origin':args[2:4],'direction':args[4],'targets':[args[5:7],args[7:9]],'release_age':args[9],'wanted_bits':want,'actual_bits':got,'passed':got&want==want})
 print(json.dumps(result,indent=1));(ROOT/'assets/horizons_region/field_feasibility.json').write_text(json.dumps(result,indent=1)+'\n')
 if not all(x['passed']for x in result):raise SystemExit(1)
