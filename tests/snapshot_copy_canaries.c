/* Isolated host byte/alignment/same-pointer audit; not native timing evidence. */
#include "save_snapshot_copy.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
static unsigned next_value(unsigned *seed) {
    *seed = *seed * 1664525u + 1013904223u;
    return *seed;
}
int main(void) {
    unsigned alignment, pattern, i, seed = 5011;
    const size_t length = sizeof(Save5State), reserve = sizeof(Save5State) + 96;
    unsigned char *input = malloc(reserve), *output = malloc(reserve);
    unsigned char *expected = malloc(length);
    assert(input && output && expected);
    assert(length == 4976 && length % 32 == 16); /* Actual four-word tail. */
    for (alignment = 0; alignment < 8; ++alignment) {
        unsigned offset = 32 + 4 * alignment;
        Save5State *src = (Save5State *)(input + offset);
        Save5State *dst = (Save5State *)(output + 60 - 4 * alignment);
        for (pattern = 0; pattern < 260; ++pattern) {
            memset(input, 0xa5, reserve); memset(output, 0x5a, reserve);
            for (i = 0; i < length; ++i)
                expected[i] = pattern < 256 ? (unsigned char)pattern :
                    (unsigned char)(next_value(&seed) >> 16);
            memcpy(src, expected, length);
            save_snapshot_copy(dst, src);
            assert(memcmp(src, expected, length) == 0);
            assert(memcmp(dst, expected, length) == 0);
            save_snapshot_copy(dst, dst);
            assert(memcmp(dst, expected, length) == 0);
            for (i = 0; i < reserve; ++i) {
                if (i < offset || i >= offset + length) assert(input[i] == 0xa5);
                if (i < 60 - 4 * alignment || i >= 60 - 4 * alignment + length)
                    assert(output[i] == 0x5a);
            }
        }
    }
    free(input); free(output); free(expected);
    puts("PASS: 2,080 full-byte copies + self-copies; all natural alignment offsets; both canaries; four-word tail");
    return 0;
}
