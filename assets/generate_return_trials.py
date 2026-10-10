#!/usr/bin/env python3
"""Generate exact Return personal-workspace rows from local editable contracts."""
from pathlib import Path
import json
P=Path(__file__).resolve().parents[1];rows=json.loads((P/'assets/return_region/geometry.json').read_text())['rooms'];design=json.loads((P/'assets/return_region/trial_contracts.json').read_text());tr={t['index']:t for r in rows for t in r['trial_workspaces']};out=['/* Authored local workspaces, no central projection and no collision override. */\n','typedef struct {unsigned char area,form,family,key,command[2],count;short lectern[2],manual[2],target[3][2],walk[2];} TrialDef;\n','static const TrialDef trials[13]={\n']
for i,d in enumerate(design):
 t=tr[i];cmd=d['allowed_predecessor_commands']+[0];targets=t['targets']+[[0,0]]*3;out.append(' {%d,%d,%d,%d,{%d,%d},%d,{%s},{%s},{%s},{%s}},\n'%(d['area'],d['from_form'],d['family'],d['key'],cmd[0],cmd[1],len(t['targets']),','.join(map(str,t['lectern'])),','.join(map(str,t['manual'][0])),','.join('{'+','.join(map(str,p))+'}'for p in targets[:3]),','.join(map(str,t['walk'][0]))))
out.append('};\n');out.append('static const int trial_names[13]={'+','.join('TX_RT_TRIAL'+str(i)for i in range(13))+'};\n');out.append('static const int trial_clues[13][2]={'+','.join('{TX_RT_TRIAL%dA,TX_RT_TRIAL%dB}'%(i,i)for i in range(13))+'};\n');(P/'src/return_trials_data.inc').write_text(''.join(out))
