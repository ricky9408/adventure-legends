/* Original 23-cue regional soundtrack, 16,384 Hz signed PCM through Direct Sound A.
 * DMA1 reads only the bounded EWRAM ring. Timer0 clocks samples; cascading
 * Timer1 rewinds DMA every 8192 samples. Timers2/3 and PSG1 SFX stay independent.
 */
#include "music.h"
#include "music_data.h"
#include "music_copy.h"
typedef unsigned int u32;
typedef unsigned short u16;
#define R16(a) (*(volatile u16 *)(a))
#define R32(a) (*(volatile u32 *)(a))
#define RING 8192u
#define RELOAD (65536u-RING)
#define BLOCK 512u
#define GUARD 256u
#define HOT __attribute__((section(".iwram.text.music"),noinline))

signed char music_ring[RING+GUARD] __attribute__((aligned(4)));
volatile u32 music_epoch, music_irq_count, music_irq_late_max, music_faults;
volatile u32 music_stopped, music_recoveries;
volatile u32 music_produced, music_consumed, music_source_cursor;
volatile u32 music_track, music_requested, music_loops, music_transitions;
static unsigned fade_in;
static unsigned recovery_blocks;
#include "music_catalog.h"

/* BIOS invokes this ARM function with r0-r3/r12/lr already saved. Never enable
 * nested IRQs. Max graphics DMA is 9600 words; the duplicate 256-byte guard
 * covers 262144 cycles, greater than that entire DMA plus IRQ entry. */
HOT void music_irq(void) {
    unsigned pending=R16(0x04000202)&R16(0x04000200);
    if(pending&16) {
        unsigned late=R16(0x04000104)-RELOAD;
        unsigned available;
        music_epoch+=RING;
        music_irq_count++;
        if(late>music_irq_late_max)music_irq_late_max=late;
        available=music_produced-music_epoch;
        if(late>=GUARD-48 || available<BLOCK || available>RING) {
            /* Fail closed on an impossible deadline or sustained producer
             * starvation: stop FIFO DMA before it could leave audio storage. */
            R16(0x04000102)=0;
            R32(0x040000c4)=0;
            R16(0x04000082)=0x0802;
            music_faults++;music_stopped=1;
        } else {
            /* DMA prefetched 32 samples. At each 16-sample boundary it fills
             * the FIFO back to 32. Avoid the boundary during reprogramming. */
            do {late=R16(0x04000104)-RELOAD;} while((late&15u)>=14u);
            R32(0x040000c4)=0;
            R32(0x040000bc)=(u32)(music_ring+(late&~15u)+32u);
            R32(0x040000c4)=0xb6400000u;
        }
    }
    R16(0x04000202)=pending;
    R16(0x03007ff8)|=pending;
}

static u32 consumed_now(void) {
    u32 epoch, count, pending;
    unsigned ime=R16(0x04000208);
    /* Snapshot the software epoch and hardware counter together. Only this
     * tiny read is atomic; never copy audio or render with IRQs disabled. */
    R16(0x04000208)=0;
    epoch=music_epoch;
    pending=R16(0x04000202)&16u;
    count=R16(0x04000104)-RELOAD;
    if(!pending&&(R16(0x04000202)&16u)) {
        pending=16;
        count=R16(0x04000104)-RELOAD;
    }
    R16(0x04000208)=ime;
    return epoch+count+(pending?RING:0);
}

static HOT void copy_block(unsigned offset) {
    signed char *dst=music_ring+offset;
    unsigned i=0, cursor=music_source_cursor, track=music_track;
    unsigned change=music_requested!=track;
    unsigned ramp=change||fade_in;
    if(ramp) {
        for(;i<BLOCK;i++) {
            int sample=tracks[track][cursor++];
            sample=sample*(int)(change?BLOCK-1-i:i)/(int)BLOCK;
            dst[i]=(signed char)sample;
            if(cursor==lengths[track]){cursor=0;music_loops++;}
        }
    } else {
        /* Exact sample period, including odd-length loops. No ROM alignment
         * bytes are played, and loop seams never trigger the scene fade. */
        cursor=music_copy_periodic(dst,tracks[track],lengths[track],cursor,
                                   BLOCK,&music_loops);
    }
    if(change){music_track=music_requested;music_source_cursor=0;fade_in=1;music_transitions++;}
    else {music_source_cursor=cursor;fade_in=0;}
    if(offset==0) {
        const u32 *src=(const u32 *)music_ring;
        u32 *out=(u32 *)(music_ring+RING);
        for(i=0;i<GUARD/4;i++)out[i]=src[i];
    }
    music_produced+=BLOCK;
}

/* Every shipped room has an explicit cue. Unknown IDs fail safely to HOME;
 * cue identity, rather than room identity, controls the existing scene fade. */
unsigned music_theme_for_room(unsigned room) {
    return room<MUSIC_ROOM_COUNT?room_themes[room]:MUSIC_HOME;
}

void music_update(unsigned room,unsigned state) {
    u32 free_samples;
    /* Menus, dialogue, save notices and death preserve the current musical
     * phrase. Pausing gameplay keeps music running; no score state is saved. */
    music_requested=(state==0||state==9)?MUSIC_HOME:music_theme_for_room(room);
    if(music_stopped)return;
    music_consumed=consumed_now();
    free_samples=music_consumed+RING-music_produced;
    if(free_samples>=RING-BLOCK){music_faults++;music_stopped=1;R16(0x04000102)=0;R32(0x040000c4)=0;R16(0x04000082)=0x0802;return;}
}

static void start_output(void) {
    unsigned i;
    R16(0x04000102)=0;R16(0x04000106)=0;R32(0x040000c4)=0;
    R16(0x04000082)=0x0b02;
    for(i=0;i<8;i++)R32(0x040000a0)=((const u32 *)music_ring)[i];
    R32(0x040000bc)=(u32)(music_ring+32);R32(0x040000c0)=0x040000a0;
    R32(0x040000c4)=0xb6400000;
    R16(0x04000202)=16;
    R16(0x04000104)=RELOAD;R16(0x04000106)=0xc4;
    R16(0x04000100)=0xfc00;R16(0x04000102)=0x80;
}

/* The caller charges refilling to this frame only if measured gameplay work
 * leaves 20896 cycles, plus the normal OAM/presentation margin. An 8 KiB queue
 * lets an isolated expensive UI/save frame defer without breaking the score. */
void music_service(void) {
    if(music_stopped) {
        /* Rebuild the queue in bounded blocks after budget returns. Start
         * from silence with a fresh fade; effects continue throughout. */
        if(!recovery_blocks) {
            music_epoch=music_produced=music_consumed=music_source_cursor=0;
            music_track=music_requested;fade_in=1;
        }
        copy_block(recovery_blocks*BLOCK);
        if(++recovery_blocks==RING/BLOCK) {
            recovery_blocks=0;music_stopped=0;music_recoveries++;
            start_output();
        }
    } else if(music_consumed+RING-music_produced>=BLOCK)
        copy_block(music_produced&(RING-1));
}

void music_init(void) {
    unsigned i;
    R16(0x04000208)=0;
    R16(0x04000102)=0;R16(0x04000106)=0;R32(0x040000c4)=0;
    music_epoch=music_irq_count=music_irq_late_max=music_faults=0;
    music_stopped=music_recoveries=recovery_blocks=0;
    music_produced=music_consumed=music_source_cursor=0;
    music_track=music_requested=music_loops=music_transitions=0;fade_in=1;
    for(i=0;i<RING;i+=BLOCK)copy_block(i);
    R16(0x04000084)=0x80;
    /* PSG1 only, original SFX envelope and gain. Music peaks at 88/128 and
     * Direct Sound uses 50% gain, leaving headroom when an effect overlaps. */
    R16(0x04000080)=0x1177;
    R32(0x03007ffc)=(u32)music_irq;
    R16(0x04000200)=16;start_output();
    R16(0x04000208)=1;
}
