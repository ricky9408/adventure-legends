#!/usr/bin/env python3
"""Reproduce frozen v1-v7 save policy without reading the current catalog.

The reviewed snapshot digest is deliberate: extending history requires adding a
new versioned snapshot, never regenerating old policy from live authored rows.
"""
import argparse, hashlib, json, re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SNAPSHOT=ROOT/'assets/history/creatures-v1-v4.json'
PIN='ee516adadbad9e26cd18a5ccaa26fed9ead82e5ad0311eb736a1d3b47d17ac51'
START='/* BEGIN GENERATED IMMUTABLE CREATURE HISTORY */'
END='/* END GENERATED IMMUTABLE CREATURE HISTORY */'

def render(data):
    if data['schema'] != 1:raise ValueError('Unknown frozen creature schema')
    forms=data['forms'];ids=set();learns=[];rows=[]
    for f in forms:
        id_=f['id'];learn=f['learn']
        if not 1<=id_<=128 or id_ in ids or not 1<=f['family']<=60:raise ValueError('Invalid frozen identity')
        ids.add(id_)
        if not 1<=f['revision_bits']<=15 or f['polarity'] not in (0,1) or not 1<=f['min_level']<=50 or not 0<=f['trial_mask']<=65535:raise ValueError('Invalid frozen policy')
        if not 1<=len(learn)<=8 or len({x[1] for x in learn})!=len(learn) or any(not 1<=l<=50 or not 1<=a<=255 for l,a in learn):raise ValueError('Invalid frozen learn relationship')
        rows.append((id_,f['family'],f['polarity'],len(learn),f['min_level'],f['revision_bits'],f['trial_mask'],len(learns)))
        learns.extend(learn)
    out=[START,'/* Generated only from assets/history/creatures-v1-v4.json. */','static const CreatureRevisionPolicy revision_policy[] = {']
    out += ['    {'+', '.join(map(str,r))+'},' for r in rows]
    out += ['};','static const CreatureLearn revision_learnsets[] = {']
    out += ['    {%d, %d},'%tuple(r) for r in learns]
    out += ['};','static const CreatureU8 revision_policy_index[4][129] = {']
    for revision in range(4):
        indexes=[0]*129
        for n,f in enumerate(forms,1):
            if f['revision_bits'] & (1<<revision):indexes[f['id']]=n
        out.append('    {')
        out += ['        '+', '.join(map(str,indexes[i:i+16]))+',' for i in range(0,129,16)]
        out.append('    },')
    return '\n'.join(out+['};',END])

V5_SNAPSHOT=ROOT/'assets/history/creatures-v5.json'
V5_PIN='477d264b8b05328c1c5016101758cdbd41ac323ab1c2c143ba774d274d412b30'
def render_v5(data):
    if data['schema'] != 1: raise ValueError('Unknown frozen revision5 schema')
    learns=[]; rows=[]; indexes=[0]*129
    for n,f in enumerate(data['forms'],1):
        if not 1<=f['id']<=128 or indexes[f['id']] or f['revision_bits']!=16: raise ValueError('Invalid revision5 identity')
        indexes[f['id']]=n
        rows.append((f['id'],f['family'],f['polarity'],len(f['learn']),f['min_level'],16,f['trial_mask'],len(learns)))
        learns.extend(f['learn'])
    out=['/* Generated only from immutable assets/history/creatures-v5.json. */',
         'static const CreatureRevisionPolicy revision5_policy[] = {']
    out += ['    {'+', '.join(map(str,r))+'},' for r in rows]
    out += ['};','static const CreatureLearn revision5_learnsets[] = {']
    out += ['    {%d, %d},'%tuple(r) for r in learns]
    out += ['};','static const CreatureU8 revision5_policy_index[129] = {']
    out += ['    '+', '.join(map(str,indexes[i:i+16]))+',' for i in range(0,129,16)]
    out += ['};','typedef struct CreatureRevisionTrialDependency {',
            '    CreatureU16 family, mask, prerequisite;',
            '} CreatureRevisionTrialDependency;',
            'static const CreatureRevisionTrialDependency revision5_trial_dependencies[] = {']
    out += ['    {%d, %d, %d},'%(d['family'],d['mask'],d['prerequisite']) for d in data['trial_dependencies']]
    return '\n'.join(out+['};',''])

V6_SNAPSHOT=ROOT/'assets/history/creatures-v6.json'
V6_PIN='e3b11543c657f7d9d9cd504fde4289e1c7e2c7d01185ec0857dbee0e7a7f20e5'
def render_v6(data):
    if data['schema'] != 2 or data['content_revision'] != 6: raise ValueError('Unknown frozen revision6 schema')
    compatible=dict(data, schema=1)
    compatible['forms']=[dict(f,revision_bits=16) for f in data['forms']]
    base=render_v5(compatible).replace('revision5','revision6').replace('creatures-v5','creatures-v6')
    # Reuse the frozen common shape but retain the extra r6 terminal contract.
    for f in data['forms']:
        old='    {'+', '.join(map(str,(f['id'],f['family'],f['polarity'],len(f['learn']),f['min_level'],16,f['trial_mask'])))+', '
        new='    {'+', '.join(map(str,(f['id'],f['family'],f['polarity'],len(f['learn']),f['min_level'],32,f['trial_mask'])))+', '
        base=base.replace(old,new)
    base=base.replace('typedef struct CreatureRevisionTrialDependency {\n    CreatureU16 family, mask, prerequisite;\n} CreatureRevisionTrialDependency;\n','')
    rows=['typedef struct CreatureRevision6Constraint { CreatureU8 min_bond; CreatureU16 required_trial; } CreatureRevision6Constraint;',
          'static const CreatureRevision6Constraint revision6_constraints[] = {']
    rows += ['    {%d, %d},'%(f['min_bond'],f['required_trial']) for f in data['forms']]
    return base+'\n'+'\n'.join(rows+['};',''])

V7_SNAPSHOT=ROOT/'assets/history/creatures-v7.json'
V7_PIN='fae9677ff1475dca61e40069a5c9236d82c76eecd851a8246ea6af90cdbc31b7'
def render_v7(data):
    if data['schema'] != 2 or data['content_revision'] != 7: raise ValueError('Unknown frozen revision7 schema')
    compatible=dict(data, content_revision=6)
    result=render_v6(compatible).replace('revision6','revision7').replace('creatures-v6','creatures-v7').replace('CreatureRevision6Constraint','CreatureRevision7Constraint')
    for f in data['forms']:
        prefix='    {'+', '.join(map(str,(f['id'],f['family'],f['polarity'],len(f['learn']),f['min_level'])))+', '
        result=result.replace(prefix+'32, ',prefix+'64, ')
    return result

V8_SNAPSHOT=ROOT/'assets/history/creatures-v8.json'
V8_PIN='8a4fb5f0bffde511e21f9b45a9a721d7747f53a569de09790bc20dccc0642471'
def render_v8(data):
    if data['schema'] != 2 or data['content_revision'] != 8: raise ValueError('Unknown frozen revision8 schema')
    result=render_v7(dict(data,content_revision=7)).replace('revision7','revision8').replace('creatures-v7','creatures-v8').replace('CreatureRevision7Constraint','CreatureRevision8Constraint')
    for f in data['forms']:
        prefix='    {'+', '.join(map(str,(f['id'],f['family'],f['polarity'],len(f['learn']),f['min_level'])))+', '
        result=result.replace(prefix+'64, ',prefix+'128, ')
    return result

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--check',action='store_true');args=ap.parse_args()
    blob=SNAPSHOT.read_bytes()
    if hashlib.sha256(blob).hexdigest()!=PIN:raise ValueError('Immutable v1-v4 snapshot changed; add a new version instead')
    rendered=render(json.loads(blob));source=ROOT/'src/creatures.c';old=source.read_text()
    begin=old.index(START);end=old.index(END,begin)+len(END)
    new=old[:begin]+rendered+old[end:]
    if args.check:
        if new!=old:raise ValueError('Generated creature history drifted; run tools/generate_creature_history.py')
    else:source.write_text(new)
    blob=V5_SNAPSHOT.read_bytes()
    if hashlib.sha256(blob).hexdigest()!=V5_PIN: raise ValueError('Immutable revision5 snapshot changed; add a new version instead')
    rendered=render_v5(json.loads(blob)); source=ROOT/'src/creature_history_v5.inc'
    if args.check:
        if not source.exists() or source.read_text()!=rendered: raise ValueError('Generated revision5 history drifted')
    else: source.write_text(rendered)
    blob=V6_SNAPSHOT.read_bytes()
    if hashlib.sha256(blob).hexdigest()!=V6_PIN: raise ValueError('Immutable revision6 snapshot changed; add a new version instead')
    rendered=render_v6(json.loads(blob)); source=ROOT/'src/creature_history_v6.inc'
    if args.check:
        if not source.exists() or source.read_text()!=rendered: raise ValueError('Generated revision6 history drifted')
    else: source.write_text(rendered)
    blob=V7_SNAPSHOT.read_bytes()
    if hashlib.sha256(blob).hexdigest()!=V7_PIN: raise ValueError('Immutable revision7 snapshot changed; add a new version instead')
    rendered=render_v7(json.loads(blob)); source=ROOT/'src/creature_history_v7.inc'
    if args.check:
        if not source.exists() or source.read_text()!=rendered: raise ValueError('Generated revision7 history drifted')
    else: source.write_text(rendered)
    blob=V8_SNAPSHOT.read_bytes()
    if hashlib.sha256(blob).hexdigest()!=V8_PIN: raise ValueError('Immutable revision8 snapshot changed; add a new version instead')
    rendered=render_v8(json.loads(blob)); source=ROOT/'src/creature_history_v8.inc'
    if args.check:
        if not source.exists() or source.read_text()!=rendered: raise ValueError('Generated revision8 history drifted')
    else: source.write_text(rendered)
    print('Frozen revisions1–8 verified unchanged, including exact H and C constraints')
if __name__=='__main__':main()
