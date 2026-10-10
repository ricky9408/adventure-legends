#!/usr/bin/env python3
"""Native fence/overlay cache differential on one pinned connected-roads ROM.

The test starts a new game normally, then explicitly prepares toast or reward
presentation fields and restores same-ROM machine states for cached/reference
branches. The reference invalidates both bitmap caches before every frame.
This proves rendering equivalence, not reward acquisition or gameplay cadence.
"""
from pathlib import Path
import argparse,hashlib,json,re,shutil,sys
from PIL import ImageChops
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'tests'),str(ROOT/'tools')]
from player_feedback_native import Native,sha


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('rom','symbols','bridge','output','source-manifest'):
        parser.add_argument('--'+name,type=Path,required=True)
    for name in ('expected-rom-sha','expected-symbols-sha'):
        parser.add_argument('--'+name,required=True)
    parser.add_argument('--reference-uncached-notices',action='store_true')
    args=parser.parse_args()
    assert sha(args.rom)==args.expected_rom_sha,'ROM pin mismatch'
    assert sha(args.symbols)==args.expected_symbols_sha,'symbol pin mismatch'
    source_map=json.loads(args.source_manifest.read_text())
    assert all(sha(ROOT/name)==value for name,value in source_map.items()),'source changed after build receipt'
    out=args.output.resolve();out.mkdir(parents=True,exist_ok=False)
    inputs_to_copy=[(args.rom,'tested.gba'),(args.symbols,'tested.sym'),
                    (args.bridge,'bridge.so'),(args.source_manifest,'source-hashes.json'),
                    (Path(__file__),'helper.py')]
    for source,name in inputs_to_copy:shutil.copyfile(source,out/name)
    for name in ('tests/player_feedback_native.py','tests/player_feedback_campaign.py','tools/mgba_runner.py'):
        target=out/'test-source'/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/name,target)
    assert sha(out/'tested.gba')==args.expected_rom_sha and sha(out/'tested.sym')==args.expected_symbols_sha
    sym={p[2]:int(p[0],16)for line in(out/'tested.sym').read_text().splitlines()if len(p:=line.split())==3}
    text_ids=list(dict.fromkeys(re.findall(r'\bTX_[A-Z0-9_]+\b',(ROOT/'src/ui.h').read_text())))
    e=Native(out/'tested.gba',out/'bridge.so');writes=[];inputs=[];phase='boot';restores=0;results=[]
    def get(name):return e.read(sym[name])
    def put(name,value,offset=0,reason='reference cache invalidation'):
        writes.append({'phase':phase,'hardware_frame':e.frame,'symbol':name,'offset':offset,'value':value,'reason':reason})
        e.write(sym[name]+offset,value,4)
    def step(count,keys=0,full=False):
        inputs.append({'phase':phase,'hardware_frame':e.frame,'frames':count,'keys':keys,'forced_full_redraw':full})
        for _ in range(count):
            if full:put('cache_valid',0);put('cache_valid',0,4)
            e.frames(1,keys)
    def tap(keys):step(2,keys);step(4)
    try:
        step(160);tap('A')
        for _ in range(200):
            if get('game_state')==2:tap('A')
            elif get('game_state')in(6,10,12):step(10)
            else:break
        step(160)
        assert get('game_state')==1 and get('room')==0 and not get('chapter_flags')
        quiescent=out/'quiescent.state';e.state(quiescent)
        for case in ('toast','reward'):
            e.state(quiescent,load=True);restores+=1;phase=case+'-prepare'
            if case=='toast':
                put('toast_id',text_ids.index('TX_PF_ROUTE_LATER'),reason='presentation-only closed-road hint; no route/gate mutation')
                put('toast_ticks',20,reason='presentation-only toast lifetime')
            else:
                for name,value in [('reward_ticks',20),('game_shop_reward_xp',180),('game_shop_reward_gold',6),('game_shop_revision',get('game_shop_revision')+1)]:
                    put(name,value,reason='presentation-only reward setup; no earned money/EXP mutation')
            put('cache_valid',0);put('cache_valid',0,4);step(2)
            baseline=out/(case+'.state');e.state(baseline);samples=[]
            for full in (False,True):
                phase=case+('-full'if full else'-cached');e.state(baseline,load=True);restores+=1
                if full and args.reference_uncached_notices:put('play_notice_cache_disabled',1,reason='original uncached toast/hint reference')
                step(22,full=full);views={}
                for _ in range(2):
                    step(1,full=full);page=int(bool(e.read(0x04000000,2)&16))
                    im=e.screenshot();im.save(out/f'{phase}-page{page}.png')
                    views[page]={'image':im,'oam':e.bytes(0x07000000,1024)}
                assert set(views)=={0,1},'both bitmap parities were not sampled'
                assert get('toast_ticks')==0 and get('reward_ticks')==0,'overlay did not expire'
                samples.append(views)
            for page in (0,1):
                a,b=samples[0][page],samples[1][page];delta=ImageChops.difference(a['image'],b['image']);bounds=delta.getbbox()
                rgb=delta.convert('RGB').tobytes();different=sum(any(rgb[i:i+3])for i in range(0,len(rgb),3))
                if bounds is not None:delta.save(out/f'{case}-difference-page{page}.png')
                results.append({'case':case,'page':page,'passed':bounds is None and a['oam']==b['oam'],
                                'difference_bounds':bounds,'different_pixels':different,'oam_equal':a['oam']==b['oam'],
                                'cached_rgb_sha256':hashlib.sha256(a['image'].tobytes()).hexdigest(),
                                'full_rgb_sha256':hashlib.sha256(b['image'].tobytes()).hexdigest()})
        faults=e.lib.eb_faults(e.ptr)
        unchanged=all(sha(ROOT/name)==value for name,value in source_map.items())
        report={'scope':__doc__,'passed':all(row['passed']for row in results)and faults==0 and unchanged,
                'candidate':{name:sha(out/name)for _,name in inputs_to_copy},'expected_rom_sha256':args.expected_rom_sha,
                'expected_symbols_sha256':args.expected_symbols_sha,'source_unchanged_during_run':unchanged,
                'same_rom_state_restores':restores,'reference_uncached_notices':args.reference_uncached_notices,'cases':results,'faults':faults,'writes':writes,'inputs':inputs}
        (out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
        print(json.dumps({key:report[key]for key in ('passed','candidate','cases','faults')},indent=2))
        return 0 if report['passed']else 1
    finally:e.close()

if __name__=='__main__':raise SystemExit(main())
