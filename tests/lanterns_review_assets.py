#!/usr/bin/env python3
"""Independent byte provenance, generation and packaging checks in temp roots.

No production sources, receipts or distributables are modified. Pass the exact
accepted v23 source archive explicitly for the immutable regression comparison.
"""
import argparse, hashlib, importlib.util, json, shutil, subprocess, sys, tempfile, zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SHA=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
RAW='assets/music/lanterns/lanterns-gba-16384-s8.raw'
EXPECTED_RAW='a9ada6ff0b3ef068dc8ab9bfabd02f69521c6ef252420157b9646636e98e4838'
EXPECTED_BASE='2cd80e3272a988d9bdce019d0e81e4265838f50009c0c1db9a8e11e2177b1088'
def pcm(slug):
    values=[int(v) for p in sorted((ROOT/'src/music_data').glob(slug+'_*.inc')) for v in p.read_text().replace('\n','').split(',') if v]
    assert all(-128<=v<=127 for v in values)
    return bytes(v&255 for v in values)
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--baseline',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);a=ap.parse_args()
    assert SHA(a.baseline)==EXPECTED_BASE
    result={'review_scope':'Independent audio delta and asset/build-input integrity; not native timing or artistic listening approval','baseline_zip_sha256':SHA(a.baseline),'checks':{}}
    village=pcm('village');dungeon=pcm('dungeon');raw=(ROOT/RAW).read_bytes()
    assert len(raw)==907421 and hashlib.sha256(raw).hexdigest()==EXPECTED_RAW and village==raw
    assert len(dungeon)==655360 and hashlib.sha256(dungeon).hexdigest()=='73976cb3133ebee5a83443810bc5e2de0654546524293c13356680451ed8985a'
    result['checks']['exact_pcm']={'village_samples':len(village),'village_sha256':hashlib.sha256(village).hexdigest(),'dungeon_samples':len(dungeon),'dungeon_sha256':hashlib.sha256(dungeon).hexdigest(),'rom_alignment_padding_in_array':False}
    with zipfile.ZipFile(a.baseline) as z:
        changed=[];n=0;prefix='Adventure-Legends-Emberbond/'
        for name in z.namelist():
            rel=name.removeprefix(prefix)
            if not(rel.startswith('src/') or rel in ('Makefile','linker.ld')) or name.endswith('/'):continue
            n+=1;p=ROOT/rel;assert p.is_file(),rel
            if p.read_bytes()!=z.read(name):changed.append(rel)
        expected=['src/music.c','src/music_data.c','src/music_data.h']+[f'src/music_data/village_{i:03}.inc' for i in range(52)]
        assert sorted(changed)==sorted(expected),changed
        old_dungeon=json.loads(z.read(prefix+'docs/music-conversion.json'))[1]
        assert old_dungeon==json.loads((ROOT/'docs/music-conversion.json').read_text())[1]
        names={x.removeprefix(prefix) for x in z.namelist()}
        added=sorted(str(p.relative_to(ROOT)) for p in (ROOT/'src').rglob('*') if p.is_file() and str(p.relative_to(ROOT)) not in names)
        assert added==sorted(['src/music_copy.h']+[f'src/music_data/village_{i:03}.inc' for i in range(52,56)]),added
    result['checks']['accepted_runtime_scope']={'baseline_inputs_compared':n,'changed_existing_runtime_files':changed,'new_runtime_files':added,'gameplay_routing_save_font_and_dungeon_unchanged':True}
    with tempfile.TemporaryDirectory(prefix='lanterns-review-') as temp:
        temp=Path(temp);g=temp/'generate'
        for rel in ['tools/generate_music.py',RAW,'assets/music/original-v2/dungeon_gba_synthetic_v2.wav']:
            dest=g/rel;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/rel,dest)
        (g/'src').mkdir();(g/'docs').mkdir()
        subprocess.run([sys.executable,str(g/'tools/generate_music.py')],check=True,capture_output=True)
        generated=[p for p in g.rglob('*') if p.is_file() and (p.is_relative_to(g/'src') or p.is_relative_to(g/'docs'))]
        for p in generated:assert p.read_bytes()==(ROOT/p.relative_to(g)).read_bytes(),str(p)
        result['checks']['independent_regeneration']={'exact_generated_files':len(generated),'all_byte_identical':True}
        spec=importlib.util.spec_from_file_location('package_under_review',ROOT/'tools/package_source.py');pack=importlib.util.module_from_spec(spec);spec.loader.exec_module(pack)
        p=temp/'pack';p.mkdir();pack.ROOT=p;pack.OUT=p/'dist'
        for rel in pack.ROOT_FILES:
            dest=p/rel;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/rel,dest)
        for rel in pack.SOURCE_ROOTS:(p/rel).mkdir(exist_ok=True)
        (p/'docs/evidence').mkdir()
        for rel in pack.MUSIC_INPUTS:
            dest=p/rel;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/rel,dest)
        for rel in ['assets/music/lanterns/unapproved.raw','assets/music/lanterns/unapproved.mid','assets/music/lanterns/unapproved.musicxml','tools/unapproved.so','assets/music/lanterns/audition.wav','assets/music/lanterns/audition.m4a','build/unapproved.c','dist/unapproved.json','assets/music/lanterns/unapproved.sav']:
            dest=p/rel;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(b'unapproved')
        included={x.relative_to(p).as_posix() for x in pack.source_files()}
        assert set(pack.MUSIC_INPUTS)<=included
        assert all('unapproved' not in x and 'audition' not in x for x in included),included
        raw_path=p/RAW;raw_path.write_bytes(b'wrong approved asset')
        try:pack.source_files()
        except AssertionError as e:assert str(e)=='Unreviewed music input'
        else:raise AssertionError('Modified approved PCM was accepted')
        shutil.copyfile(ROOT/RAW,raw_path)
        pack.main();first=SHA(pack.OUT/'Adventure-Legends-Emberbond-source.zip');manifest=(pack.OUT/'source-manifest-campaign.json').read_bytes()
        pack.main();assert first==SHA(pack.OUT/'Adventure-Legends-Emberbond-source.zip') and manifest==(pack.OUT/'source-manifest-campaign.json').read_bytes()
        result['checks']['packaging']={'exact_approved_assets_included':len(pack.MUSIC_INPUTS),'unapproved_media_and_binaries_excluded':True,'modified_approved_pcm_rejected':True,'fixture_repeated_zip_and_manifest_byte_identical':True}
    result['verdict']='PASS for independent host/integrity checks'
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='checks'},indent=2))
if __name__=='__main__':main()
