#!/usr/bin/env python3
"""Compile the authored world's exact work/actor coordinates, never save data."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
data=json.loads((ROOT/'assets/covenants_world/geometry.json').read_text())
lines=['/* Generated from the exact original room geometry; no reward state. */\n']
lines.append('typedef struct {short x,y;unsigned char command,station,beat,radius;} StationTarget;\n')
lines.append('static const StationTarget station_targets[8][8]={\n')
counts=[]
for room in data['rooms']:
    rows=[]
    for index,station in enumerate(room['stations']):
        for target in station['targets']:
            x,y=target['center'];rows.append(f'{{{x},{y},{station["command"]},{index},{target["required_beat"]},{target["radius"]}}}')
    assert len(rows)<=8
    counts.append(len(rows));lines.append('{'+','.join(rows)+'},\n')
lines.append('};\nstatic const unsigned char station_counts[8]={'+','.join(map(str,counts))+'};\n')
lines.append('static const short manual_points[8][2][2]={\n')
for room in data['rooms']:
    rows=room['manual'];assert len(rows)<=2
    lines.append('{'+','.join('{%d,%d}'%tuple(p) for p in rows)+'},\n')
lines.append('};\nstatic const unsigned char manual_counts[8]={'+','.join(str(len(r['manual'])) for r in data['rooms'])+'};\n')
lines.append('typedef struct {unsigned char sprite;short x,y;} ResidentDef;\nstatic const ResidentDef residents[8][4]={\n')
for room in data['rooms']:
    rows=room['humans'];assert len(rows)<=4
    lines.append('{'+','.join('{COVENANTS_SPR_%s,%d,%d}'%tuple(p) for p in rows)+'},\n')
lines.append('};\nstatic const unsigned char resident_counts[8]={'+','.join(str(len(r['humans'])) for r in data['rooms'])+'};\n')
lines.append('typedef struct {short origin[2],target[2][2];unsigned char command,count,face;} PracticeDef;\nstatic const PracticeDef practices[8]={\n')
for room in data['rooms']:
    p=room['practice'];targets=p['targets'];assert 1<=len(targets)<=2
    lines.append('{{%d,%d},{%s},%d,%d,%d},\n'%(*p['start_xy'],','.join('{%d,%d}'%tuple(t['center']) for t in targets),p['command'],len(targets),p['face']))
lines.append('};\n')
text=''.join(lines);assert len(text.encode())<30000
(ROOT/'src/covenants_work_data.inc').write_text(text)
print('Covenants work targets:',sum(counts),'rooms:',len(counts),'bytes:',len(text.encode()))
