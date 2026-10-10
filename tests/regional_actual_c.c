/* Independent tests of the production helper AND actual copy_block body.
 * Host code does not invoke any memory-mapped hardware function. */
#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "music.c"
#include "expected_routes.h"

static unsigned cases, blocks, random_state=0x1a73;
static unsigned random32(void) {
    random_state=random_state*1664525u+1013904223u;
    return random_state;
}
static void helper_case(unsigned length,unsigned cursor,unsigned count) {
    unsigned sa=cases%4, da=(cases/4)%4;
    signed char *source=malloc(length+sa), *src=source+sa, *storage=malloc(count+48), *dst=storage+16+da;
    volatile unsigned loops=7;
    unsigned i, got;
    assert(src&&storage&&cursor<length);
    for(i=0;i<length;i++)src[i]=(signed char)((i*73u+19u)&255u);
    memset(storage,0x55,count+48);
    got=music_copy_periodic(dst,src,length,cursor,count,&loops);
    assert(got==(cursor+count)%length);
    assert(loops==7+(cursor+count)/length);
    for(i=0;i<count;i++)assert(dst[i]==src[(cursor+i)%length]);
    for(i=0;i<16+da;i++)assert(storage[i]==0x55);
    for(i=count+16+da;i<count+48;i++)assert(storage[i]==0x55);
    free(storage);free(source);cases++;
}
static void block_case(unsigned track,unsigned cursor,unsigned offset,unsigned fade,unsigned change) {
    signed char expected[RING+GUARD];
    unsigned i, end=(cursor+BLOCK)%lengths[track], crossings=(cursor+BLOCK)/lengths[track];
    memset(music_ring,0x55,sizeof music_ring);memset(expected,0x55,sizeof expected);
    music_track=track;music_requested=change?(track+1)%MUSIC_TRACK_COUNT:track;music_source_cursor=cursor;
    music_loops=7;music_transitions=3;music_produced=0xfffffe00u;fade_in=fade;
    for(i=0;i<BLOCK;i++) {
        int sample=tracks[track][(cursor+i)%lengths[track]];
        if(fade||change)sample=sample*(int)(change?BLOCK-1-i:i)/(int)BLOCK;
        expected[offset+i]=(signed char)sample;
    }
    if(!offset)memcpy(expected+RING,expected,GUARD);
    copy_block(offset);
    assert(!memcmp(expected,music_ring,sizeof expected));
    assert(music_source_cursor==(change?0:end));
    assert(music_track==(change?(track+1)%MUSIC_TRACK_COUNT:track));
    assert(music_requested==music_track);
    assert(music_loops==7+crossings);
    assert(music_transitions==3+change);
    assert(music_produced==0); /* uint32 publication wraps without overflow UB. */
    assert(fade_in==(change?1:0));blocks++;
}
static void continuous(unsigned track) {
    unsigned i,j,position=0,n=(3*lengths[track]+BLOCK-1)/BLOCK;
    music_track=music_requested=track;music_source_cursor=music_loops=music_produced=0;fade_in=0;
    for(i=0;i<n;i++) {
        unsigned offset=(i*BLOCK)&(RING-1);
        copy_block(offset);
        for(j=0;j<BLOCK;j++)assert(music_ring[offset+j]==tracks[track][(position+j)%lengths[track]]);
        position+=BLOCK;
        assert(music_source_cursor==position%lengths[track]);
        assert(music_loops==position/lengths[track]);
        assert(!memcmp(music_ring+RING,music_ring,GUARD));
        blocks++;
    }
}
static void routes(void) {
    unsigned room,state,track;
    const unsigned invalid[]={78,79,255,256,65535,0x7fffffff,0x80000000,0xffffffff};
    for(track=0;track<MUSIC_TRACK_COUNT;track++){assert(tracks[track]==expected_tracks[track]);assert(lengths[track]==expected_lengths[track]);}
    music_stopped=1;
    for(room=0;room<78;room++) {
        assert(music_theme_for_room(room)==expected_routes[room]);
        assert(expected_routes[room]<MUSIC_TRACK_COUNT);
        for(state=0;state<=12;state++) {
            music_update(room,state);
            assert(music_requested==((state==0||state==9)?MUSIC_HOME:expected_routes[room]));
        }
    }
    for(room=0;room<sizeof invalid/sizeof *invalid;room++) {
        assert(music_theme_for_room(invalid[room])==MUSIC_HOME);
        music_update(invalid[room],1);assert(music_requested==MUSIC_HOME);
    }
    /* All 529 cue-pair transitions, using the actual C update and copy code. */
    for(track=0;track<MUSIC_TRACK_COUNT;track++)for(room=0;room<78;room++) {
        unsigned next=expected_routes[room], old=lengths[track]-3;
        music_track=music_requested=track;music_source_cursor=old;
        music_loops=music_transitions=music_produced=fade_in=0;
        music_update(room,1);copy_block(0);
        assert(music_track==next&&music_transitions==(next!=track));
        assert(music_source_cursor==(next==track?509:0));
        assert(music_loops==1);
        copy_block(BLOCK);
        assert(music_track==next&&music_transitions==(next!=track));
        assert(music_source_cursor==(next==track?1021:512));
        assert(!fade_in);
    }
    puts("PASS: independent plan oracle 78 routes, 8 invalid IDs, title/modal states, all 529 cue pairs and same-cue continuity");
}
int main(void) {
    unsigned l,c,n,t,o,f,k;
    routes();
    const unsigned lengths_to_test[]={1,2,3,4,7,15,16,17,31,255,256,257,511,512,513};
    const unsigned counts[]={0,1,2,3,15,16,17,255,256,511,512,513,1024,4097};
    for(l=0;l<sizeof lengths_to_test/sizeof *lengths_to_test;l++)
        for(c=0;c<lengths_to_test[l];c++)
            for(n=0;n<sizeof counts/sizeof *counts;n++)helper_case(lengths_to_test[l],c,counts[n]);
    for(n=0;n<12000;n++) {l=1+random32()%4096;c=random32()%l;helper_case(l,c,random32()%2049);}
    for(t=0;t<MUSIC_TRACK_COUNT;t++) {
        for(c=0;c<=513;c++)
            for(o=0;o<RING;o+=BLOCK)
                for(f=0;f<3;f++)block_case(t,lengths[t]-1-c,o,f==1,f==2);
        continuous(t);
    }
    /* Remaining uncommon low, odd and aligned cursors across every offset. */
    for(k=0;k<4096;k++)block_case(k%MUSIC_TRACK_COUNT,random32()%lengths[k%MUSIC_TRACK_COUNT],(k%16)*BLOCK,0,0);
    printf("PASS: %u helper cases; %u actual copy_block checks; exact bytes/cursors/loops, canaries, fades, track switches, guard and uint32 publication verified.\n",cases,blocks);
    return 0;
}
