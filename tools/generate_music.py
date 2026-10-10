#!/usr/bin/env python3
"""Import hash-pinned original regional PCM without resampling or padding.

Only Python's standard library is required. Exact track sizes are declared in
C; alignment between symbols is never part of the playable period.
"""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'src/music_data'
def main():
    manifest=json.loads((ROOT/'assets/music/regional/catalog.json').read_text())
    cues=manifest['cues']
    assert len(cues)==23 and len({c['id'] for c in cues})==23
    # Validate the entire input set before touching generated output.
    inputs=[]
    for c in cues:
        path=ROOT/c['raw_path'];raw=path.read_bytes()
        assert len(raw)==c['sample_count']>512
        assert c['sample_rate']==16384
        assert hashlib.sha256(raw).hexdigest()==c['raw_sha256'],c['id']
        if c['id']=='HOME':
            assert len(raw)==907421 and c['raw_sha256']=='a9ada6ff0b3ef068dc8ab9bfabd02f69521c6ef252420157b9646636e98e4838'
        inputs.append((c,raw))
    plan=json.loads((ROOT/'assets/music/regional/room-plan.json').read_text())
    assert [c['id'] for c in cues]==[c['id'] for c in plan['cues']]
    assert [v['room_id'] for v in plan['rooms']]==list(range(78))
    expected={room:c['id'] for c in cues for room in c['room_ids']}
    assert len(expected)==78 and sum(len(c['room_ids']) for c in cues)==78
    assert all(expected[v['room_id']]==v['cue'] for v in plan['rooms'])
    table=['/* Generated soundtrack IDs and exact-sized immutable cartridge tables. */','#ifndef EMBERBOND_MUSIC_CATALOG_H','#define EMBERBOND_MUSIC_CATALOG_H','enum {']
    table += ['    MUSIC_'+c['id']+' = '+str(i)+',' for i,c in enumerate(cues)]
    table += ['    MUSIC_TRACK_COUNT = 23, MUSIC_ROOM_COUNT = 78','};','static const signed char *const tracks[MUSIC_TRACK_COUNT] = {']
    table += ['    music_'+c['id'].lower()+',' for c in cues]
    table += ['};','static const u32 lengths[MUSIC_TRACK_COUNT] = {']
    table += ['    sizeof music_'+c['id'].lower()+',' for c in cues]
    table += ['};','static const unsigned char room_themes[MUSIC_ROOM_COUNT] = {']
    table += ['    MUSIC_'+v['cue']+', /* '+str(v['room_id'])+' */' for v in plan['rooms']]
    table += ['};','#endif','']
    (ROOT/'src/music_catalog.h').write_text('\n'.join(table))
    OUT.mkdir(exist_ok=True)
    for path in OUT.glob('*.inc'):path.unlink()
    declarations=['/* Generated original regional soundtrack; exact unpadded periods. */','#include "music_data.h"']
    header=['#ifndef EMBERBOND_MUSIC_DATA_H','#define EMBERBOND_MUSIC_DATA_H']
    report=[]
    for c,raw in inputs:
        slug=c['id'].lower();length=len(raw)
        declarations.append(f'const signed char music_{slug}[{length}] __attribute__((aligned(4))) = {{')
        for part,offset in enumerate(range(0,length,16384)):
            name=f'{slug}_{part:03d}.inc';values=[v if v<128 else v-256 for v in raw[offset:offset+16384]]
            (OUT/name).write_text(''.join(','.join(map(str,values[j:j+32]))+',\n' for j in range(0,len(values),32)))
            declarations.append('#include "music_data/'+name+'"')
        declarations.append('};');header.append(f'extern const signed char music_{slug}[{length}];')
        report.append(dict(track=c['id'],samples=length,sample_rate=16384,seconds=length/16384,pcm_sha256=c['raw_sha256']))
    header+=['#endif','']
    (ROOT/'src/music_data.h').write_text('\n'.join(header))
    (ROOT/'src/music_data.c').write_text('\n'.join(declarations)+'\n')
    (ROOT/'docs/music-conversion.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))
if __name__=='__main__':main()
