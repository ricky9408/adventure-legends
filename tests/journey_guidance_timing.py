#!/usr/bin/env python3
"""Compile reproducible native pacing failures from strict earned journey traces.

Observes reports and produces a derived decision. It never changes game state.
The optional replay mode is an explicitly labelled diagnostic from the exact
controller-earned cold session origin, using the original button trace.
"""
from __future__ import annotations
import argparse
from collections import Counter
import gzip
import hashlib
import json
import shutil
from pathlib import Path
import sys

sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'tests'),str(ROOT/'tools')]

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def iter_rows(path):
    with gzip.open(path,'rt') as stream:
        for line in stream:yield json.loads(line)
def rows(path):return list(iter_rows(path))
def session_origin(section,report,session):
    if session:
        eligible=[(k,v) for k,v in report['snapshots'].items() if k.endswith('-before-continue') and v['session']==session-1]
        assert eligible,('missing genuine cold origin',section,session)
        key,record=max(eligible,key=lambda kv:kv[1]['frame'])
        path=Path(record['sram_path']);assert sha(path)==record['sram_sha256']
        return {'kind':'earned_sram','snapshot':key,'path':str(path),'sha256':sha(path)}
    if section.name=='original':
        return {'kind':'blank_sram','sha256':report['provenance']['initial_sram_sha256']}
    producer=Path(report['provenance']['source_report'])
    assert sha(producer)==report['provenance']['source_report_sha256']
    p=json.loads(producer.read_text());expected=report['provenance']['source_sram_sha256']
    matching=[(k,r) for k,r in p['snapshots'].items() if r['sram_sha256']==expected]
    assert matching,('missing authenticated regional origin',producer)
    key,record=matching[-1];path=Path(record['sram_path']);assert sha(path)==expected
    return {'kind':'earned_sram','snapshot':key,'path':str(path),'sha256':expected,
            'producer':str(producer),'producer_sha256':sha(producer)}

def summarize(journey):
    sections=[];windows=[]
    for name in ('original','regions'):
        section=journey/name
        if not (section/'report.json').is_file():continue
        report=json.loads((section/'report.json').read_text())
        frame_path=section/'native-frames.jsonl.gz';input_path=section/'controller-inputs.jsonl.gz'
        frames=rows(frame_path);inputs=rows(input_path);anomalies=[];other_anomalies=[];previous=None
        for index,v in enumerate(frames):
            if previous and previous['session']==v['session'] and v['phase'] in ('journey','opening_activation'):
                if (v['delta']!=1 and not v.get('counter_reset',False)) or not v['flip'] or v['cycles']>=280896:
                    active=previous['state']==v['state']==1
                    row=dict(v,trace_index=index,before_state=previous['state'],steady_play=active)
                    (anomalies if active else other_anomalies).append(row)
            previous=v
        groups=[]
        for subset in (anomalies,other_anomalies):
            subset_groups=[]
            for row in subset:
                if not subset_groups or row['session']!=subset_groups[-1][-1]['session'] or row['room']!=subset_groups[-1][-1]['room'] or row['hardware_frame']-subset_groups[-1][-1]['hardware_frame']>90:
                    subset_groups.append([])
                subset_groups[-1].append(row)
            groups.extend(subset_groups)
        for group in groups:
            first,last=group[0],group[-1];session=first['session']
            lo=max(0,first['hardware_frame']-100);hi=last['hardware_frame']+100
            prefix=[i for i,r in enumerate(inputs) if r['session']==session and r['emulator_frame']<hi]
            local=[i for i in prefix if inputs[i]['emulator_frame']+inputs[i]['frames']>lo]
            origin=session_origin(section,report,session)
            profiles={v['completed_profile']['serial']:v['completed_profile'] for v in group if 'completed_profile' in v}
            prefix_name='' if first['steady_play'] else 'presentation-'
            windows.append({'id':prefix_name+f'{name}-session{session}-room{first["room"]}-hw{first["hardware_frame"]}',
                            'steady_play':first['steady_play'],'affected_states':sorted({r['state']for r in group}),
                            'section':name,'chapter':first['chapter'],'session':session,'room':first['room'],
                            'sample_from':lo,'sample_through':hi,'first_bad_hw':first['hardware_frame'],'last_bad_hw':last['hardware_frame'],
                            'maximum_cycles':max(r['cycles']for r in group),
                            'update_misses':sum(r['delta']!=1 and not r.get('counter_reset',False) for r in group),'flip_misses':sum(not r['flip'] for r in group),
                            'overrun_samples':sum(r['cycles']>=280896 for r in group),
                            'source':origin,'input_trace':str(input_path),'input_trace_sha256':sha(input_path),
                            'replay_input_indexes':[min(prefix),max(prefix)],'window_input_indexes':[min(local),max(local)],
                            'completed_profiles':list(profiles.values()),'anomalies':group})
        sections.append({'section':name,'report_sha256':sha(section/'report.json'),'native_frames_sha256':sha(frame_path),
                         'input_trace_sha256':sha(input_path),'hardware_frames':len(frames),'candidate':report['candidate'],
                         'active_update_misses':sum(v['delta']!=1 and not v.get('counter_reset',False) for v in anomalies),
                         'active_flip_misses':sum(not v['flip']for v in anomalies),
                         'active_overrun_samples':sum(v['cycles']>=280896 for v in anomalies),
                         'maximum_active_anomaly_cycles':max((v['cycles']for v in anomalies),default=0),
                         'presented_update_misses':sum(v['delta']!=1 and not v.get('counter_reset',False) for v in anomalies+other_anomalies),
                         'presented_flip_misses':sum(not v['flip']for v in anomalies+other_anomalies),
                         'presented_overrun_samples':sum(v['cycles']>=280896 for v in anomalies+other_anomalies),
                         'maximum_presented_anomaly_cycles':max((v['cycles']for v in anomalies+other_anomalies),default=0),
                         'anomaly_states':dict(Counter(v['state']for v in anomalies+other_anomalies)),
                         'faults':report['metrics']['faults'],'gameplay_complete':report['route_complete'],'completed_chapters':report.get('completed_chapters',[])})
    result={'suite':'journey-guidance-native-pacing-decision','candidate':sections[0]['candidate'],
            'pacing_passed':not windows,'steady_play_pacing_passed':not any(w['steady_play']for w in windows),
            'scope':'All presented journey-phase hardware observations, including PLAY, dialogue, journal, save and transaction frames; none are waived',
            'cold_boot_and_continue':'Separately labelled in source traces, excluded from steady-play budget only',
            'opening_counter_reset':'Only the first title-to-opening logical reset is recognized; its flips and cycle budget remain gated',
            'limit_cycles':280896,'sections':sections,'windows':windows}
    helper=Path(__file__).resolve();result['timing_helper_sha256']=sha(helper)
    (journey/('timing-helper-'+sha(helper)[:12]+'.py')).write_bytes(helper.read_bytes())
    (journey/'timing-report.json').write_text(json.dumps(result,indent=2)+'\n')
    summary=journey/'summary.json'
    if summary.is_file():
        data=json.loads(summary.read_text());raw=journey/'raw-gameplay-summary.json'
        if not raw.exists():raw.write_bytes(summary.read_bytes())
        data.update(gameplay_passed=data['complete_fresh_main_journey'],steady_play_pacing_passed=result['steady_play_pacing_passed'],presented_journey_pacing_passed=result['pacing_passed'],
                    accepted=data['complete_fresh_main_journey'] and result['pacing_passed'] and not data['baseline_diagnostic'] and not data.get('cross_rom_earned_sram_diagnostic',False),
                    raw_gameplay_summary_sha256=sha(raw),timing_report_sha256=sha(journey/'timing-report.json'),
                    decision_scope='Acceptance requires both complete fresh gameplay and the unwaived pacing gate for all presented journey states')
        summary.write_text(json.dumps(data,indent=2)+'\n')
    return result

def replay(journey,window_id,bridge,out,candidate=None,candidate_hashes=None):
    from journey_guidance_earned import StrictNative
    assert not out.exists() or not any(out.iterdir()),'Use a new replay output directory'
    timing=json.loads((journey/'timing-report.json').read_text())
    window=next(w for w in timing['windows']if w['id']==window_id)
    section=journey/window['section'];rom=section/'tested.gba';symbols=section/'tested.sym'
    assert sha(rom)==timing['candidate']['rom_sha256'] and sha(symbols)==timing['candidate']['symbols_sha256']
    assert sha(bridge)==timing['candidate']['bridge_sha256']
    out.mkdir(parents=True,exist_ok=True);tested=dict(timing['candidate'])
    if candidate:
        from magma_journey import elf_locals
        assert candidate_hashes and all(candidate_hashes.values()),'Prototype diagnostics require all three explicit hashes'
        for suffix,key in (('.gba','rom_sha256'),('.sym','symbols_sha256'),('.elf','elf_sha256')):
            source=candidate.with_suffix(suffix);target=out/('tested'+suffix)
            assert sha(source)==candidate_hashes[key],('prototype input changed',source)
            shutil.copyfile(source,target);assert sha(target)==candidate_hashes[key]
        rom=out/'tested.gba';symbols=out/'tested.sym'
        elf_locals(out/'tested.elf',rom)
        tested={**candidate_hashes,'bridge_sha256':sha(bridge)}
    sym={p[2]:int(p[0],16)for l in symbols.read_text().splitlines()if len(p:=l.split())==3}
    e=StrictNative(rom,bridge);source=window['source']
    if source['kind']=='earned_sram':
        assert sha(source['path'])==source['sha256'];e.load_save(source['path']);e.reset()
    else:assert hashlib.sha256(e.bytes(0x0e000000,32768)).hexdigest()==source['sha256']
    def get(n):return e.read(sym[n])
    records=[];expected={(r['session'],r['hardware_frame']):r for r in iter_rows(section/'native-frames.jsonl.gz') if r['session']==window['session'] and r['hardware_frame']<=window['sample_through']}
    matches=True;position_matches=True;differences=[];first_path_difference=None
    for command in iter_rows(section/'controller-inputs.jsonl.gz'):
        if command['session']!=window['session']:continue
        if e.frame>=window['sample_through']:break
        assert e.frame==command['emulator_frame'],('input alignment differs',e.frame,command)
        count=min(command['frames'],window['sample_through']-e.frame)
        for _ in range(count):
            before=get('frame');page=e.read(0x04000000,2)&16;e.frames(1,command['keys'])
            if first_path_difference is None:
                reference=expected.get((window['session'],e.frame))
                if reference:
                    observed={'room':get('room'),'state':get('game_state'),'x':get('px'),'y':get('py')}
                    changed={k:{'reference':reference[k],'observed':v}for k,v in observed.items()if reference[k]!=v}
                    if changed:first_path_difference={'hardware_frame':e.frame,'phase':command['phase'],'keys':command['keys'],'fields':changed}
            if e.frame<window['sample_from']:continue
            row={'hardware_frame':e.frame,'room':get('room'),'state':get('game_state'),'x':get('px'),'y':get('py'),
                 'delta':(get('frame')-before)&0xffffffff,'flip':(e.read(0x04000000,2)&16)!=page,'cycles':get('render_cycles')}
            row['runtime']={n:get(n)for n in ('scene_present_phase','save_feedback_background','save_requested','toast_id','toast_ticks','return_power_kind','return_power_time','horizons_power_kind','horizons_power_time','covenants_power_kind','covenants_power_time')if n in sym}
            serial=get('render_profile_serial')
            if not serial&1:row['profile']={n:get('render_profile_'+n)for n in ('world','card','actors','frame','state','room','update','save','render','music','deferred_actors','vblank_cycles','vblank_start','vblank_end','commit')if 'render_profile_'+n in sym}
            ref=expected.get((window['session'],e.frame))
            if ref:
                changed={k:{'reference':ref[k],'observed':row[k]}for k in ('room','state','x','y','delta','flip','cycles')if row[k]!=ref[k]}
                if changed:differences.append({'hardware_frame':e.frame,'fields':changed})
                matches &= not bool(changed)
                position_matches &= all(row[k]==ref[k]for k in ('room','state','x','y'))
            records.append(row)
    result={'diagnostic_replay':True,'cross_rom_earned_sram_diagnostic':bool(candidate),'acceptance_claim':False,
            'window':window,'candidate':tested,'reference_candidate':timing['candidate'],'controller_only':True,
            'game_ram_writes':0,'machine_state_imports':0,'matches_original_observations':matches,
            'matches_reference_scene_positions':position_matches,'first_reference_path_difference':first_path_difference,'frame_differences':differences,
            'difference_counts':dict(Counter(k for row in differences for k in row['fields'])),
            'sampled_pacing':{'frames':len(records),'update_misses':sum(r['delta']!=1 for r in records),'flip_misses':sum(not r['flip']for r in records),'overrun_samples':sum(r['cycles']>=280896 for r in records),'maximum_cycles':max((r['cycles']for r in records),default=0)},
            'faults':e.lib.eb_faults(e.ptr),'frames':records}
    e.screenshot(out/'final.png');e.close()
    (out/'replay.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items()if k not in ('window','frames','frame_differences')},indent=2))
    return result

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--journey',type=Path,required=True)
    p.add_argument('--replay-window');p.add_argument('--bridge',type=Path);p.add_argument('--output',type=Path)
    p.add_argument('--candidate',type=Path,help='explicit cross-ROM earned-SRAM diagnostic; never acceptance')
    p.add_argument('--expected-candidate-rom-sha');p.add_argument('--expected-candidate-symbols-sha');p.add_argument('--expected-candidate-elf-sha')
    a=p.parse_args();journey=a.journey.resolve()
    if a.replay_window:
        assert a.bridge and a.output
        r=replay(journey,a.replay_window,a.bridge.resolve(),a.output.resolve(),a.candidate.resolve()if a.candidate else None,{'rom_sha256':a.expected_candidate_rom_sha,'symbols_sha256':a.expected_candidate_symbols_sha,'elf_sha256':a.expected_candidate_elf_sha})
        return int(bool(r['faults']) or (not a.candidate and not r['matches_original_observations']))
    r=summarize(journey)
    print(json.dumps({'pacing_passed':r['pacing_passed'],'windows':len(r['windows']),'sections':r['sections']},indent=2))
    return 0
if __name__=='__main__':raise SystemExit(main())
