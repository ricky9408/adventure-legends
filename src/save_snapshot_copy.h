#ifndef EMBERBOND_SAVE_SNAPSHOT_COPY_H
#define EMBERBOND_SAVE_SNAPSHOT_COPY_H
#include "save5.h"

typedef Save4U32 SaveSnapshotWord __attribute__((__may_alias__));
typedef char save_snapshot_word_width[(sizeof(SaveSnapshotWord) == 4) ? 1 : -1];
typedef char save_snapshot_word_size[(sizeof(Save5State) % 4 == 0) ? 1 : -1];
typedef char save_snapshot_word_alignment[(__alignof__(Save5State) >= 4) ? 1 : -1];

/* Complete, naturally aligned runtime states; distinct objects or self-copy.
 * The eight-word unroll reduces ROM loop overhead without DMA, extra storage,
 * or interrupt masking. The remaining words include any future size change.
 * This never serializes a raw struct: SRAM still goes through encode_*(). */
static inline void save_snapshot_copy(Save5State *dst, const Save5State *src) {
    SaveSnapshotWord *d = (SaveSnapshotWord *)dst;
    const SaveSnapshotWord *s = (const SaveSnapshotWord *)src;
    unsigned words = sizeof(*dst) / sizeof(*d);
    while (words >= 8) {
        d[0] = s[0]; d[1] = s[1]; d[2] = s[2]; d[3] = s[3];
        d[4] = s[4]; d[5] = s[5]; d[6] = s[6]; d[7] = s[7];
        d += 8; s += 8; words -= 8;
    }
    while (words--) *d++ = *s++;
}
#endif
