#ifndef EMBERBOND_MUSIC_COPY_H
#define EMBERBOND_MUSIC_COPY_H
/* Copy an exact periodic stream without alignment padding. Caller supplies a
 * nonempty track, cursor < length and a separate destination. Bounded byte
 * copies also cover an odd-length period crossing within a 512-byte refill. */
static inline unsigned music_copy_periodic(signed char *dst,
 const signed char *src, unsigned length, unsigned cursor, unsigned count,
 volatile unsigned *loops) {
    while(count) {
        unsigned span=length-cursor, i;
        if(span>count)span=count;
        for(i=0;i<span;i++)dst[i]=src[cursor+i];
        dst+=span;cursor+=span;count-=span;
        if(cursor==length){cursor=0;(*loops)++;}
    }
    return cursor;
}
#endif
