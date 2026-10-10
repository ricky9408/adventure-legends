#include "creatures.h"

/* Natural layout is deliberately checked, never used as a save wire format. */
typedef char CreatureInstanceMustBe24Bytes[(sizeof(CreatureInstance) == 24) ? 1 : -1];
typedef char CreatureFormMustBe32Bytes[(sizeof(CreatureForm) == 32) ? 1 : -1];
typedef char CreatureU32MustBe4Bytes[(sizeof(CreatureU32) == 4) ? 1 : -1];
#define U32_MAX_VALUE 0xffffffffu
#if defined(__GNUC__) || defined(__clang__)
#define CREATURE_INLINE static inline __attribute__((always_inline))
#else
#define CREATURE_INLINE static inline
#endif

/* Runtime CreatureInstance objects are naturally word-aligned and exactly24
 * bytes (asserted above). GCC/Clang may_alias permits six complete word reads
 * without violating effective-type aliasing. This is never a wire decoder.
 * A fieldwise fallback covers every byte on other compilers: the field sizes
 * sum to24, so the asserted struct size leaves no implicit padding. */
#if defined(__GNUC__) || defined(__clang__)
typedef CreatureU32 CreatureAliasU32 __attribute__((__may_alias__));
#endif
static int instance_is_zero(const CreatureInstance *c) {
#if defined(__GNUC__) || defined(__clang__)
    const CreatureAliasU32 *words = (const CreatureAliasU32 *)(const void *)c;
    return !(words[0] | words[1] | words[2] | words[3] | words[4] | words[5]);
#else
    return !(c->form_id | c->flags | c->level | c->bond | c->xp |
             c->instance_id | c->nickname_id | c->trial_flags |
             c->equipped[0] | c->equipped[1] | c->polarity |
             c->selected_command | c->cosmetic_seed);
#endif
}

static void clear_bytes(void *p, unsigned n) {
    CreatureU8 *b = (CreatureU8 *)p;
    while (n--) *b++ = 0;
}
static int bit_get(const CreatureU8 *bits, unsigned n) {
    return (bits[n >> 3] >> (n & 7)) & 1;
}
static void bit_set(CreatureU8 *bits, unsigned n) {
    bits[n >> 3] |= (CreatureU8)(1u << (n & 7));
}
/* Reviewed identity policy is separate from generated authored data. It keeps
 * malformed historical rows invalid and does not assume alternating pairs. */
typedef struct CreatureFormPolicy {
    CreatureU8 id, family, tier, signature;
    CreatureU16 learn_offset;
    CreatureU8 learn_count, edge_offset, edge_count, polarity;
    CreatureU16 trial_mask; /* current per-form attainable/retained trial union */
    CreatureU32 field_caps;
} CreatureFormPolicy;
typedef struct CreatureFamilyPolicy {
    CreatureU8 id, phase, polarity;
    CreatureU16 trial;
    CreatureU32 base_caps, added_caps;
} CreatureFamilyPolicy;
typedef struct CreatureAbilityPolicy {
    CreatureU8 id;
    CreatureU16 cooldown;
} CreatureAbilityPolicy;
static const CreatureFormPolicy form_policy[CREATURE_ENABLED_COUNT] = {
    {1, 1, 1, 1, 0, 1, 0, 1, 1, 1, 0x00001222u},
    {2, 1, 2, 5, 1, 2, 51, 1, 1, 1025, 0x00001222u},
    {4, 2, 1, 2, 3, 1, 1, 1, 0, 2, 0x00100c00u},
    {5, 2, 2, 6, 4, 2, 52, 1, 0, 1026, 0x00100c00u},
    {7, 3, 1, 3, 6, 1, 2, 1, 1, 4, 0x000a0088u},
    {8, 3, 2, 7, 7, 2, 53, 1, 1, 1028, 0x000a0088u},
    {10, 4, 1, 4, 9, 1, 3, 1, 0, 8, 0x00044051u},
    {11, 4, 2, 8, 10, 2, 54, 1, 0, 1032, 0x00044051u},
    {13, 5, 1, 9, 12, 1, 4, 1, 0, 16, 0x00008100u},
    {14, 5, 2, 10, 13, 2, 55, 1, 0, 1040, 0x0000a100u},
    {16, 6, 1, 11, 15, 1, 56, 1, 1, 1024, 0x00010004u},
    {19, 7, 1, 13, 16, 1, 5, 1, 0, 32, 0x00200000u},
    {20, 7, 2, 14, 17, 2, 58, 1, 0, 1056, 0x00200000u},
    {22, 8, 1, 15, 19, 1, 6, 1, 0, 64, 0x00400000u},
    {23, 8, 2, 16, 20, 2, 59, 1, 0, 1088, 0x00400000u},
    {73, 25, 1, 17, 22, 1, 7, 1, 1, 128, 0x00800000u},
    {74, 25, 2, 18, 23, 2, 0, 0, 1, 128, 0x00800000u},
    {75, 26, 1, 19, 25, 1, 8, 1, 1, 256, 0x00004000u},
    {76, 26, 2, 20, 26, 2, 0, 0, 1, 256, 0x00004000u},
    {77, 27, 1, 21, 28, 1, 9, 1, 0, 512, 0x01000000u},
    {78, 27, 2, 22, 29, 2, 0, 0, 0, 512, 0x01000000u},
    {25, 9, 1, 23, 31, 1, 10, 1, 1, 1, 0x00000800u},
    {26, 9, 2, 24, 32, 2, 60, 1, 1, 1025, 0x00000c00u},
    {28, 10, 1, 25, 34, 1, 11, 1, 0, 1, 0x00040000u},
    {29, 10, 2, 26, 35, 2, 61, 1, 0, 1025, 0x00040000u},
    {79, 28, 1, 27, 37, 1, 12, 1, 1, 1, 0x02000000u},
    {80, 28, 2, 28, 38, 2, 0, 0, 1, 1, 0x02000000u},
    {81, 29, 1, 29, 40, 1, 13, 1, 0, 1, 0x00400000u},
    {82, 29, 2, 30, 41, 2, 0, 0, 0, 1, 0x00400000u},
    {83, 30, 1, 31, 43, 1, 14, 1, 1, 1, 0x00004000u},
    {84, 30, 2, 32, 44, 2, 0, 0, 1, 1, 0x00004000u},
    {85, 31, 1, 33, 46, 1, 15, 1, 1, 1, 0x00010000u},
    {86, 31, 2, 34, 47, 2, 0, 0, 1, 1, 0x00010000u},
    {87, 32, 1, 35, 49, 1, 16, 1, 0, 1, 0x00200000u},
    {88, 32, 2, 36, 50, 2, 0, 0, 0, 1, 0x00200000u},
    {89, 33, 1, 37, 52, 1, 17, 1, 0, 1, 0x00008100u},
    {90, 33, 2, 38, 53, 2, 0, 0, 0, 1, 0x00008100u},
    {91, 34, 1, 39, 55, 1, 18, 1, 1, 1, 0x00001000u},
    {92, 34, 2, 40, 56, 2, 0, 0, 1, 1, 0x00001000u},
    {93, 35, 1, 41, 58, 1, 19, 1, 0, 1, 0x00000004u},
    {94, 35, 2, 42, 59, 2, 0, 0, 0, 1, 0x00000004u},
    {31, 11, 1, 43, 61, 1, 20, 1, 0, 1, 0x00400000u},
    {32, 11, 2, 44, 62, 2, 21, 1, 0, 3, 0x00400000u},
    {33, 11, 3, 45, 64, 3, 0, 0, 0, 3, 0x00401000u},
    {34, 12, 1, 46, 67, 1, 22, 1, 1, 1, 0x00004000u},
    {35, 12, 2, 47, 68, 2, 23, 1, 1, 3, 0x00004001u},
    {36, 12, 3, 48, 70, 3, 0, 0, 1, 3, 0x00004001u},
    {37, 13, 1, 49, 73, 1, 24, 2, 0, 3, 0x00000800u},
    {38, 13, 2, 50, 74, 2, 0, 0, 0, 3, 0x00000800u},
    {39, 13, 2, 51, 76, 2, 0, 0, 1, 3, 0x00000800u},
    {40, 14, 1, 52, 78, 1, 26, 2, 1, 3, 0x00008100u},
    {41, 14, 2, 53, 79, 2, 0, 0, 1, 3, 0x00008100u},
    {42, 14, 2, 54, 81, 2, 0, 0, 1, 3, 0x00008100u},
    {43, 15, 1, 55, 83, 1, 28, 2, 0, 3, 0x00000004u},
    {44, 15, 2, 56, 84, 2, 0, 0, 0, 3, 0x00000004u},
    {45, 15, 2, 57, 86, 2, 0, 0, 0, 3, 0x00000004u},
    {46, 16, 1, 58, 88, 1, 30, 2, 1, 3, 0x00020000u},
    {47, 16, 2, 59, 89, 2, 0, 0, 1, 3, 0x00020000u},
    {48, 16, 2, 60, 91, 2, 0, 0, 0, 3, 0x00020000u},
    {95, 36, 1, 61, 93, 1, 32, 1, 0, 1, 0x00040000u},
    {96, 36, 2, 62, 94, 2, 0, 0, 0, 1, 0x00040000u},
    {97, 37, 1, 63, 96, 1, 33, 1, 1, 1, 0x00200000u},
    {98, 37, 2, 64, 97, 2, 0, 0, 1, 1, 0x00200000u},
    {99, 38, 1, 65, 99, 1, 34, 1, 0, 1, 0x00010000u},
    {100, 38, 2, 66, 100, 2, 0, 0, 0, 1, 0x00010000u},
    {49, 17, 1, 67, 102, 1, 35, 2, 0, 3, 0x04000000u},
    {50, 17, 2, 68, 103, 2, 0, 0, 0, 3, 0x04000000u},
    {51, 17, 2, 69, 105, 2, 0, 0, 1, 3, 0x04000000u},
    {52, 18, 1, 70, 107, 1, 37, 2, 1, 3, 0x08000000u},
    {53, 18, 2, 71, 108, 2, 0, 0, 0, 3, 0x08000000u},
    {54, 18, 2, 72, 110, 2, 0, 0, 1, 3, 0x08000000u},
    {55, 19, 1, 73, 112, 1, 39, 2, 1, 3, 0x10000800u},
    {56, 19, 2, 74, 113, 2, 0, 0, 1, 3, 0x10000800u},
    {57, 19, 2, 75, 115, 2, 0, 0, 0, 3, 0x10000800u},
    {58, 20, 1, 76, 117, 1, 41, 2, 0, 3, 0x21000004u},
    {59, 20, 2, 77, 118, 2, 0, 0, 0, 3, 0x21000004u},
    {60, 20, 2, 78, 120, 2, 0, 0, 1, 3, 0x21000004u},
    {61, 21, 1, 79, 122, 1, 43, 2, 1, 3, 0x00401000u},
    {62, 21, 2, 80, 123, 2, 0, 0, 0, 3, 0x00401000u},
    {63, 21, 2, 81, 125, 2, 0, 0, 1, 3, 0x00401000u},
    {64, 22, 1, 82, 127, 1, 45, 2, 0, 3, 0x10000400u},
    {65, 22, 2, 83, 128, 2, 0, 0, 0, 3, 0x10000400u},
    {66, 22, 2, 84, 130, 2, 0, 0, 1, 3, 0x10000400u},
    {67, 23, 1, 85, 132, 1, 47, 2, 1, 3, 0x01010000u},
    {68, 23, 2, 86, 133, 2, 0, 0, 1, 3, 0x01010000u},
    {69, 23, 2, 87, 135, 2, 0, 0, 0, 3, 0x01010000u},
    {70, 24, 1, 88, 137, 1, 49, 2, 0, 3, 0x06000000u},
    {71, 24, 2, 89, 138, 2, 0, 0, 0, 3, 0x06000000u},
    {72, 24, 2, 90, 140, 2, 0, 0, 1, 3, 0x06000000u},
    {3, 1, 3, 91, 142, 3, 0, 0, 1, 1025, 0x00001222u},
    {6, 2, 3, 92, 145, 3, 0, 0, 0, 1026, 0x00100c00u},
    {9, 3, 3, 93, 148, 3, 0, 0, 1, 1028, 0x000a0088u},
    {12, 4, 3, 94, 151, 3, 0, 0, 0, 1032, 0x00044051u},
    {15, 5, 3, 95, 154, 3, 0, 0, 0, 1040, 0x0000a100u},
    {17, 6, 2, 96, 157, 2, 57, 1, 1, 3072, 0x00010004u},
    {18, 6, 3, 97, 159, 3, 0, 0, 1, 3072, 0x00010004u},
    {21, 7, 3, 98, 162, 3, 0, 0, 0, 1056, 0x00200000u},
    {24, 8, 3, 99, 165, 3, 0, 0, 0, 1088, 0x00400000u},
    {27, 9, 3, 100, 168, 3, 0, 0, 1, 1025, 0x00000c00u},
    {30, 10, 3, 101, 171, 3, 0, 0, 0, 1025, 0x00040000u},
    {101, 39, 1, 102, 174, 1, 62, 1, 0, 1024, 0x00010004u},
    {102, 39, 2, 103, 175, 2, 0, 0, 0, 1024, 0x00010004u},
    {103, 40, 1, 104, 177, 1, 63, 1, 1, 1024, 0x00802000u},
    {104, 40, 2, 105, 178, 2, 0, 0, 1, 1024, 0x00802000u},    {105, 41, 1, 106, 180, 1, 64, 1, 1, 1024, 0x00200000u},
    {106, 41, 2, 107, 181, 2, 0, 0, 1, 1024, 0x00200800u},
    {107, 42, 1, 108, 183, 1, 65, 1, 0, 1024, 0x00400000u},
    {108, 42, 2, 109, 184, 2, 0, 0, 0, 1024, 0x00401000u},
    {109, 43, 1, 110, 186, 1, 66, 1, 1, 1024, 0x08004000u},
    {110, 43, 2, 111, 187, 2, 0, 0, 1, 1024, 0x08004000u},
    {111, 44, 1, 112, 189, 1, 67, 1, 0, 1024, 0x02000000u},
    {112, 44, 2, 113, 190, 2, 0, 0, 0, 1024, 0x02002000u},
    {113, 45, 1, 114, 192, 1, 0, 0, 1, 0, 0x01000000u},
    {114, 46, 1, 115, 193, 1, 0, 0, 0, 0, 0x20000000u},
    {115, 47, 1, 116, 194, 1, 0, 0, 1, 0, 0x00401000u},
    {116, 48, 1, 117, 195, 1, 0, 0, 0, 0, 0x08004000u},
    {117, 49, 1, 118, 196, 1, 0, 0, 0, 0, 0x04010000u},
    {118, 50, 1, 119, 197, 1, 0, 0, 1, 0, 0x00000100u},
    {119, 51, 1, 120, 198, 1, 0, 0, 0, 0, 0x00000800u},
    {120, 52, 1, 121, 199, 1, 0, 0, 1, 0, 0x00020004u},

};
/* Sparse locked family IDs are keys, never compact-array indexes. Trial is
 * the current family-qualified u16 UNION, never a legacy scalar or family shift.
 * Northern masks 32/64/128/256/512 belong to F007/F008/F025/F026/F027.
 * Reviewed core data is not proof of artwork, handlers or acquisition routes.
 * Legacy families keep their globally distinct bits; new qualified families
 * deliberately reuse local bit 1. Policy keys, never bit equality, bind owners. */
static const CreatureFamilyPolicy family_policy[] = {
    {1, CREATURE_FIRE, CREATURE_YANG, 1025, FIELD_HOMURA, 0},
    {2, CREATURE_WOOD, CREATURE_YIN, 1026, FIELD_MIDORI, 0},
    {3, CREATURE_WOOD, CREATURE_YANG, 1028, FIELD_FUURI, 0},
    {4, CREATURE_EARTH, CREATURE_YIN, 1032, FIELD_KOHAKU, 0},
    {5, CREATURE_WATER, CREATURE_YIN, 1040, FIELD_DEWSPINDLE, FIELD_LINK_POOLS},
    {6, CREATURE_METAL, CREATURE_YANG, 3072, FIELD_CHIMECLASP, 0},
    {7, CREATURE_WOOD, CREATURE_YIN, 1056, FIELD_REEL_LOAD, 0},
    {8, CREATURE_FIRE, CREATURE_YIN, 1088, FIELD_STORE_HEAT, 0},
    {25, CREATURE_WATER, CREATURE_YANG, CREATURE_TRIAL_FRAGILE_CARGO, FIELD_FLOAT_LOAD, 0},
    {26, CREATURE_EARTH, CREATURE_YANG, CREATURE_TRIAL_BALANCED_REACH, FIELD_PRESS_WEIGHT, 0},
    {27, CREATURE_METAL, CREATURE_YIN, CREATURE_TRIAL_COMPASS_ROUND, FIELD_ALIGN_RAIL, 0},
    {9, CREATURE_WOOD, CREATURE_YANG, 1025, FIELD_GROW_ROOTS, FIELD_GROW_BRIDGE},
    {10, CREATURE_EARTH, CREATURE_YIN, 1025, FIELD_UNCAP_WELL, 0},
    {28, CREATURE_WATER, CREATURE_YANG, 1, FIELD_REFRACT_BEAM, 0},
    {29, CREATURE_FIRE, CREATURE_YIN, 1, FIELD_STORE_HEAT, 0},
    {30, CREATURE_EARTH, CREATURE_YANG, 1, FIELD_PRESS_WEIGHT, 0},
    {31, CREATURE_METAL, CREATURE_YANG, 1, FIELD_TUNE_LATCH, 0},
    {32, CREATURE_WOOD, CREATURE_YIN, 1, FIELD_REEL_LOAD, 0},
    {33, CREATURE_WATER, CREATURE_YIN, 1, FIELD_DEWSPINDLE, 0},
    {34, CREATURE_FIRE, CREATURE_YANG, 1, FIELD_IGNITE, 0},
    {35, CREATURE_METAL, CREATURE_YIN, 1, FIELD_DRAW_ORE, 0},
    {11, 1, 0, 3, 0x00400000u, 0},
    {12, 2, 1, 3, 0x00004000u, 0},
    {13, 0, 0, 3, 0x00000800u, 0},
    {14, 4, 1, 3, 0x00008100u, 0},
    {15, 3, 0, 3, 0x00000004u, 0},
    {16, 1, 1, 3, 0x00020000u, 0},
    {36, 2, 0, 1, 0x00040000u, 0},
    {37, 0, 1, 1, 0x00200000u, 0},
    {38, 4, 0, 1, 0x00010000u, 0},
    {17, 4, 0, 3, 0x04000000u, 0},
    {18, 2, 1, 3, 0x08000000u, 0},
    {19, 0, 1, 3, 0x10000800u, 0},
    {20, 3, 0, 3, 0x21000004u, 0},
    {21, 1, 1, 3, 0x00401000u, 0},
    {22, 0, 0, 3, 0x10000400u, 0},
    {23, 3, 1, 3, 0x01010000u, 0},
    {24, 4, 0, 3, 0x06000000u, 0},
    {39, 3, 0, 1024, 0x00010004u, 0},
    {40, 4, 1, 1024, 0x00802000u, 0},    {41, 0, 1, 1024, 0x00200000u, 0x00000800u},
    {42, 1, 0, 1024, 0x00400000u, 0x00001000u},
    {43, 2, 1, 1024, 0x08004000u, 0x00000000u},
    {44, 4, 0, 1024, 0x02000000u, 0x00002000u},
    {45, 3, 1, 0, 0x01000000u, 0x00000000u},
    {46, 0, 0, 0, 0x20000000u, 0x00000000u},
    {47, 1, 1, 0, 0x00401000u, 0x00000000u},
    {48, 2, 0, 0, 0x08004000u, 0x00000000u},
    {49, 3, 0, 0, 0x04010000u, 0x00000000u},
    {50, 4, 1, 0, 0x00000100u, 0x00000000u},
    {51, 0, 0, 0, 0x00000800u, 0x00000000u},
    {52, 3, 1, 0, 0x00020004u, 0x00000000u},

};
static const CreatureAbilityPolicy ability_policy[CREATURE_ABILITY_COUNT] = {
    {1, 75},
    {2, 75},
    {3, 75},
    {4, 75},
    {5, 105},
    {6, 120},
    {7, 105},
    {8, 120},
    {9, 90},
    {10, 120},
    {11, 90},
    {13, 90},
    {14, 120},
    {15, 90},
    {16, 120},
    {17, 90},
    {18, 120},
    {19, 90},
    {20, 120},
    {21, 90},
    {22, 120},
    {23, 90},
    {24, 120},
    {25, 90},
    {26, 120},
    {27, 90},
    {28, 120},
    {29, 90},
    {30, 120},
    {31, 90},
    {32, 120},
    {33, 90},
    {34, 120},
    {35, 90},
    {36, 120},
    {37, 90},
    {38, 120},
    {39, 90},
    {40, 120},
    {41, 90},
    {42, 120},
    {43, 90},
    {44, 120},
    {45, 150},
    {46, 90},
    {47, 120},
    {48, 150},
    {49, 90},
    {50, 120},
    {51, 120},
    {52, 90},
    {53, 120},
    {54, 120},
    {55, 90},
    {56, 120},
    {57, 120},
    {58, 90},
    {59, 120},
    {60, 120},
    {61, 90},
    {62, 120},
    {63, 90},
    {64, 120},
    {65, 90},
    {66, 120},
    {67, 90},
    {68, 120},
    {69, 120},
    {70, 90},
    {71, 120},
    {72, 120},
    {73, 90},
    {74, 120},
    {75, 120},
    {76, 90},
    {77, 180},
    {78, 120},
    {79, 90},
    {80, 120},
    {81, 120},
    {82, 90},
    {83, 120},
    {84, 120},
    {85, 90},
    {86, 120},
    {87, 120},
    {88, 90},
    {89, 120},
    {90, 120},
    {91, 135},
    {92, 150},
    {93, 135},
    {94, 150},
    {95, 135},
    {96, 120},
    {97, 150},
    {98, 135},
    {99, 150},
    {100, 135},
    {101, 150},
    {102, 90},
    {103, 120},
    {104, 90},
    {105, 120},    {106, 72},
    {107, 88},
    {108, 84},
    {109, 100},
    {110, 66},
    {111, 86},
    {112, 64},
    {113, 84},
    {114, 80},
    {115, 92},
    {116, 74},
    {117, 88},
    {118, 72},
    {119, 76},
    {120, 90},
    {121, 70},

};
/* Reviewed sparse key maps store row+1, never an identity. Lookups check
 * full-width bounds and mapped row identity; catalog validation checks both
 * directions so corrupt/stale maps fail closed without a fallback scan. */
static const CreatureU8 form_policy_index[129] = {
    0, 1, 2, 90, 3, 4, 91, 5, 6, 92, 7, 8, 93, 9, 10, 94,
    11, 95, 96, 12, 13, 97, 14, 15, 98, 22, 23, 99, 24, 25, 100, 42,
    43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58,
    59, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79, 80,
    81, 82, 83, 84, 85, 86, 87, 88, 89, 16, 17, 18, 19, 20, 21, 26,
    27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 60,
    61, 62, 63, 64, 65, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111,
    112, 113, 114, 115, 116, 117, 118, 119, 120, 0, 0, 0, 0, 0, 0, 0,
    0,
};
static const CreatureU8 family_policy_index[61] = {
    0, 1, 2, 3, 4, 5, 6, 7, 8, 12, 13, 22, 23, 24, 25, 26,
    27, 31, 32, 33, 34, 35, 36, 37, 38, 9, 10, 11, 14, 15, 16, 17,
    18, 19, 20, 21, 28, 29, 30, 39, 40, 41, 42, 43, 44, 45, 46, 47,
    48, 49, 50, 51, 52, 0, 0, 0, 0, 0, 0, 0, 0,
};
static const CreatureU8 ability_policy_index[256] = {
    0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 0, 12, 13, 14,
    15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30,
    31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46,
    47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62,
    63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78,
    79, 80, 81, 82, 83, 84, 85, 86, 87, 88, 89, 90, 91, 92, 93, 94,
    95, 96, 97, 98, 99, 100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110,
    111, 112, 113, 114, 115, 116, 117, 118, 119, 120, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
};

static const CreatureFormPolicy *form_policy_for_id(unsigned id) {
    unsigned row;
    if (!id || id > 128) return 0;
    row = form_policy_index[id];
    if (!row || row > CREATURE_ENABLED_COUNT || form_policy[row - 1].id != id) return 0;
    return &form_policy[row - 1];
}
static const CreatureFamilyPolicy *family_policy_for_id(unsigned id) {
    unsigned row;
    if (!id || id > 60) return 0;
    row = family_policy_index[id];
    if (!row || row > sizeof(family_policy) / sizeof(family_policy[0]) || family_policy[row - 1].id != id) return 0;
    return &family_policy[row - 1];
}
static const CreatureAbilityPolicy *ability_policy_for_id(unsigned id) {
    unsigned row;
    if (!id || id > 255) return 0;
    row = ability_policy_index[id];
    if (!row || row > CREATURE_ABILITY_COUNT || ability_policy[row - 1].id != id) return 0;
    return &ability_policy[row - 1];
}
static int legacy_family(unsigned family) {
    return (family >= 1 && family <= 8) || (family >= 25 && family <= 27);
}
/* Released legacy scalars have their own immutable policy. Adding a qualified
 * key never widens the old public query or changes legacy mark semantics. */
static const CreatureU16 legacy_trial_scalars[61] = {
    [1] = CREATURE_TRIAL_HEARTH, [2] = CREATURE_TRIAL_CANOPY,
    [3] = CREATURE_TRIAL_WIND_LOOM, [4] = CREATURE_TRIAL_AMBER_ARCH,
    [5] = CREATURE_TRIAL_PAIRED_POOLS, [7] = CREATURE_TRIAL_TENSION_ROOF,
    [8] = CREATURE_TRIAL_DRY_LEDGER, [25] = CREATURE_TRIAL_FRAGILE_CARGO,
    [26] = CREATURE_TRIAL_BALANCED_REACH, [27] = CREATURE_TRIAL_COMPASS_ROUND
};
unsigned creatures_family_trial(unsigned id) {
    const CreatureForm *f = creatures_form(id);
    return f && f->family <= 60 ? legacy_trial_scalars[f->family] : 0;
}
/* Immutable content snapshots. Revision bit membership is explicit: new
 * current learnsets/trials must never expand an old bank's authorization. */
typedef struct CreatureRevisionPolicy {
    CreatureU8 id, family, polarity, learn_count, min_level, revision_bits;
    CreatureU16 trial_mask, learn_offset;
} CreatureRevisionPolicy;
/* BEGIN GENERATED IMMUTABLE CREATURE HISTORY */
/* Generated only from assets/history/creatures-v1-v4.json. */
static const CreatureRevisionPolicy revision_policy[] = {
    {1, 1, 1, 1, 1, 15, 1, 0},
    {2, 1, 1, 2, 12, 15, 1, 1},
    {4, 2, 0, 1, 1, 15, 2, 3},
    {5, 2, 0, 2, 12, 15, 2, 4},
    {7, 3, 1, 1, 1, 15, 4, 6},
    {8, 3, 1, 2, 16, 15, 4, 7},
    {10, 4, 0, 1, 1, 15, 8, 9},
    {11, 4, 0, 2, 20, 15, 8, 10},
    {13, 5, 0, 1, 1, 14, 16, 12},
    {14, 5, 0, 2, 15, 14, 16, 13},
    {16, 6, 1, 1, 1, 14, 0, 15},
    {19, 7, 0, 1, 1, 12, 32, 16},
    {20, 7, 0, 2, 16, 12, 32, 17},
    {22, 8, 0, 1, 1, 12, 64, 19},
    {23, 8, 0, 2, 17, 12, 64, 20},
    {73, 25, 1, 1, 1, 12, 128, 22},
    {74, 25, 1, 2, 18, 12, 128, 23},
    {75, 26, 1, 1, 1, 12, 256, 25},
    {76, 26, 1, 2, 18, 12, 256, 26},
    {77, 27, 0, 1, 1, 12, 512, 28},
    {78, 27, 0, 2, 20, 12, 512, 29},
    {25, 9, 1, 1, 1, 8, 1, 31},
    {26, 9, 1, 2, 20, 8, 1, 32},
    {28, 10, 0, 1, 1, 8, 1, 34},
    {29, 10, 0, 2, 22, 8, 1, 35},
    {79, 28, 1, 1, 1, 8, 1, 37},
    {80, 28, 1, 2, 20, 8, 1, 38},
    {81, 29, 0, 1, 1, 8, 1, 40},
    {82, 29, 0, 2, 22, 8, 1, 41},
    {83, 30, 1, 1, 1, 8, 1, 43},
    {84, 30, 1, 2, 22, 8, 1, 44},
    {85, 31, 1, 1, 1, 8, 1, 46},
    {86, 31, 1, 2, 20, 8, 1, 47},
    {87, 32, 0, 1, 1, 8, 1, 49},
    {88, 32, 0, 2, 24, 8, 1, 50},
    {89, 33, 0, 1, 1, 8, 1, 52},
    {90, 33, 0, 2, 22, 8, 1, 53},
    {91, 34, 1, 1, 1, 8, 1, 55},
    {92, 34, 1, 2, 24, 8, 1, 56},
    {93, 35, 0, 1, 1, 8, 1, 58},
    {94, 35, 0, 2, 22, 8, 1, 59},
};
static const CreatureLearn revision_learnsets[] = {
    {1, 1},
    {1, 1},
    {12, 5},
    {1, 2},
    {1, 2},
    {12, 6},
    {1, 3},
    {1, 3},
    {16, 7},
    {1, 4},
    {1, 4},
    {20, 8},
    {1, 9},
    {1, 9},
    {15, 10},
    {1, 11},
    {1, 13},
    {1, 13},
    {16, 14},
    {1, 15},
    {1, 15},
    {17, 16},
    {1, 17},
    {1, 17},
    {18, 18},
    {1, 19},
    {1, 19},
    {18, 20},
    {1, 21},
    {1, 21},
    {20, 22},
    {1, 23},
    {1, 23},
    {20, 24},
    {1, 25},
    {1, 25},
    {22, 26},
    {1, 27},
    {1, 27},
    {20, 28},
    {1, 29},
    {1, 29},
    {22, 30},
    {1, 31},
    {1, 31},
    {22, 32},
    {1, 33},
    {1, 33},
    {20, 34},
    {1, 35},
    {1, 35},
    {24, 36},
    {1, 37},
    {1, 37},
    {22, 38},
    {1, 39},
    {1, 39},
    {24, 40},
    {1, 41},
    {1, 41},
    {22, 42},
};
static const CreatureU8 revision_policy_index[4][129] = {
    {
        0, 1, 2, 0, 3, 4, 0, 5, 6, 0, 7, 8, 0, 0, 0, 0,
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
        0,
    },
    {
        0, 1, 2, 0, 3, 4, 0, 5, 6, 0, 7, 8, 0, 9, 10, 0,
        11, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
        0,
    },
    {
        0, 1, 2, 0, 3, 4, 0, 5, 6, 0, 7, 8, 0, 9, 10, 0,
        11, 0, 0, 12, 13, 0, 14, 15, 0, 0, 0, 0, 0, 0, 0, 0,
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
        0, 0, 0, 0, 0, 0, 0, 0, 0, 16, 17, 18, 19, 20, 21, 0,
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
        0,
    },
    {
        0, 1, 2, 0, 3, 4, 0, 5, 6, 0, 7, 8, 0, 9, 10, 0,
        11, 0, 0, 12, 13, 0, 14, 15, 0, 22, 23, 0, 24, 25, 0, 0,
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
        0, 0, 0, 0, 0, 0, 0, 0, 0, 16, 17, 18, 19, 20, 21, 26,
        27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 0,
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
        0,
    },
};
/* END GENERATED IMMUTABLE CREATURE HISTORY */
#include "creature_history_v5.inc"
#include "creature_history_v6.inc"
#include "creature_history_v7.inc"
static const CreatureRevisionPolicy *revision_policy_for_id(unsigned id, unsigned revision) {
    unsigned row;
    if (!id || id > 128 || revision < 1 || revision > 7) return 0;
    if (revision == 7) {
        row = revision7_policy_index[id];
        if (!row || row > sizeof(revision7_policy) / sizeof(revision7_policy[0]) ||
            revision7_policy[row - 1].id != id) return 0;
        return &revision7_policy[row - 1];
    }
    if (revision == 6) {
        row = revision6_policy_index[id];
        if (!row || row > sizeof(revision6_policy) / sizeof(revision6_policy[0]) ||
            revision6_policy[row - 1].id != id) return 0;
        return &revision6_policy[row - 1];
    }
    if (revision == 5) {
        row = revision5_policy_index[id];
        if (!row || row > sizeof(revision5_policy) / sizeof(revision5_policy[0]) ||
            revision5_policy[row - 1].id != id) return 0;
        return &revision5_policy[row - 1];
    }
    row = revision_policy_index[revision - 1][id];
    if (!row || row > sizeof(revision_policy) / sizeof(revision_policy[0]) ||
        revision_policy[row - 1].id != id ||
        !(revision_policy[row - 1].revision_bits & (1u << (revision - 1u)))) return 0;
    return &revision_policy[row - 1];
}
int creatures_form_allowed_revision(unsigned id, unsigned revision) {
    return revision == CREATURE_CONTENT_REVISION ? creatures_form(id) != 0 :
           revision_policy_for_id(id, revision) != 0;
}
unsigned creatures_trial_allowed_mask(unsigned id, unsigned revision) {
    const CreatureRevisionPolicy *p = revision_policy_for_id(id, revision);
    if (revision == CREATURE_CONTENT_REVISION) {
        const CreatureFormPolicy *current = form_policy_for_id(id);
        return current && creatures_form(id) ? current->trial_mask : 0;
    }
    return p ? p->trial_mask : 0;
}
int creatures_command_learned_revision(unsigned id, unsigned level, unsigned ability, unsigned revision) {
    const CreatureRevisionPolicy *p = revision_policy_for_id(id, revision);
    unsigned i;
    if (revision == CREATURE_CONTENT_REVISION) return creatures_command_learned(id, level, ability);
    if (!p || level < 1 || level > 50 ||
        !ability || ability > 255 ||
        p->learn_offset + p->learn_count > (revision == 7 ?
            sizeof(revision7_learnsets) / sizeof(revision7_learnsets[0]) : revision == 6 ?
            sizeof(revision6_learnsets) / sizeof(revision6_learnsets[0]) : revision == 5 ?
            sizeof(revision5_learnsets) / sizeof(revision5_learnsets[0]) :
            sizeof(revision_learnsets) / sizeof(revision_learnsets[0]))) return 0;
    for (i = 0; i < p->learn_count; ++i) {
        const CreatureLearn *l = &(revision == 7 ? revision7_learnsets : revision == 6 ? revision6_learnsets : revision == 5 ? revision5_learnsets : revision_learnsets)[p->learn_offset + i];
        if (l->ability_id == ability && l->level <= level) return 1;
    }
    return 0;
}

unsigned creatures_family_revision(unsigned id, unsigned revision) {
    const CreatureRevisionPolicy *p = revision_policy_for_id(id, revision);
    if (revision == CREATURE_CONTENT_REVISION) {
        const CreatureForm *f = creatures_form(id);
        return f ? f->family : 0;
    }
    return p ? p->family : 0;
}
unsigned creatures_legacy_spirit_revision(unsigned id, unsigned revision) {
    const CreatureRevisionPolicy *p = revision_policy_for_id(id, revision);
    if (revision == CREATURE_CONTENT_REVISION) return creatures_legacy_spirit(id);
    return p && p->family >= 1 && p->family <= 4 ? p->family - 1u : 255u;
}

typedef struct CreatureTrialPolicy {
    CreatureU16 family, key, mask, prerequisite;
    CreatureU8 introduced_revision;
} CreatureTrialPolicy;
static const CreatureTrialPolicy trial_policy[] = {
    {1, 1, CREATURE_TRIAL_HEARTH, 0, 1},
    {2, 1, CREATURE_TRIAL_CANOPY, 0, 1},
    {3, 1, CREATURE_TRIAL_WIND_LOOM, 0, 1},
    {4, 1, CREATURE_TRIAL_AMBER_ARCH, 0, 1},
    {5, 1, CREATURE_TRIAL_PAIRED_POOLS, 0, 2},
    {7, 1, CREATURE_TRIAL_TENSION_ROOF, 0, 3},
    {8, 1, CREATURE_TRIAL_DRY_LEDGER, 0, 3},
    {25, 1, CREATURE_TRIAL_FRAGILE_CARGO, 0, 3},
    {26, 1, CREATURE_TRIAL_BALANCED_REACH, 0, 3},
    {27, 1, CREATURE_TRIAL_COMPASS_ROUND, 0, 3},
    {9, 1, 1, 0, 4},
    {10, 1, 1, 0, 4},
    {28, 1, 1, 0, 4},
    {29, 1, 1, 0, 4},
    {30, 1, 1, 0, 4},
    {31, 1, 1, 0, 4},
    {32, 1, 1, 0, 4},
    {33, 1, 1, 0, 4},
    {34, 1, 1, 0, 4},
    {35, 1, 1, 0, 4},
    {11, 1, 1, 0, 5},
    {11, 2, 2, 1, 5},
    {12, 1, 1, 0, 5},
    {12, 2, 2, 1, 5},
    {13, 1, 1, 0, 5},
    {13, 2, 2, 0, 5},
    {14, 1, 1, 0, 5},
    {14, 2, 2, 0, 5},
    {15, 1, 1, 0, 5},
    {15, 2, 2, 0, 5},
    {16, 1, 1, 0, 5},
    {16, 2, 2, 0, 5},
    {36, 1, 1, 0, 5},
    {37, 1, 1, 0, 5},
    {38, 1, 1, 0, 5},
    {17, 1, 1, 0, 6},
    {17, 2, 2, 0, 6},
    {18, 1, 1, 0, 6},
    {18, 2, 2, 0, 6},
    {19, 1, 1, 0, 6},
    {19, 2, 2, 0, 6},
    {20, 1, 1, 0, 6},
    {20, 2, 2, 0, 6},
    {21, 1, 1, 0, 6},
    {21, 2, 2, 0, 6},
    {22, 1, 1, 0, 6},
    {22, 2, 2, 0, 6},
    {23, 1, 1, 0, 6},
    {23, 2, 2, 0, 6},
    {24, 1, 1, 0, 6},
    {24, 2, 2, 0, 6},
    {1, 2, 1024, 1, 7},
    {2, 2, 1024, 2, 7},
    {3, 2, 1024, 4, 7},
    {4, 2, 1024, 8, 7},
    {5, 2, 1024, 16, 7},
    {6, 1, 1024, 0, 7},
    {6, 2, 2048, 1024, 7},
    {7, 2, 1024, 32, 7},
    {8, 2, 1024, 64, 7},
    {9, 2, 1024, 1, 7},
    {10, 2, 1024, 1, 7},
    {39, 1, 1024, 0, 7},
    {40, 1, 1024, 0, 7},
    {41, 1, 1024, 0, 8}, {42, 1, 1024, 0, 8},
    {43, 1, 1024, 0, 8}, {44, 1, 1024, 0, 8},
};
static const CreatureTrialPolicy *trial_policy_for_key(unsigned family, unsigned key) {
    unsigned i;
    if (!family || family > CREATURE_FAMILY_CAPACITY || !key || key > 65535u) return 0;
    for (i = 0; i < sizeof(trial_policy) / sizeof(trial_policy[0]); ++i)
        if (trial_policy[i].family == family && trial_policy[i].key == key &&
            trial_policy[i].introduced_revision <= CREATURE_CONTENT_REVISION) return &trial_policy[i];
    return 0;
}
unsigned creatures_trial_mask_for_key(unsigned family, unsigned key) {
    const CreatureTrialPolicy *p = trial_policy_for_key(family, key);
    return p ? p->mask : 0;
}

/* Every requirement bit is a registered local key in this exact family.
 * No global OR mask establishes identity. Dependencies are not consumed. */
static int trial_subset_valid(const CreatureFamilyPolicy *f, unsigned subset) {
    unsigned i;
    if (!f || (subset & ~f->trial)) return 0;
    /* Released one-key families have no dependency. This exact shape keeps
     * the hot path constant-time without a mutable cache or caller trust. */
    if (!(f->trial & (f->trial - 1u))) return 1;
    for (i = 0; i < sizeof(trial_policy) / sizeof(trial_policy[0]); ++i) {
        const CreatureTrialPolicy *p = &trial_policy[i];
        if (p->family == f->id && (subset & p->mask) &&
            (subset & p->prerequisite) != p->prerequisite) return 0;
    }
    return 1;
}

static const CreatureEvolution *incoming_evolution(unsigned id) {
    unsigned row;
    if (!creatures_form_id_valid(id)) return 0;
    row = creature_incoming_evolution_index[id];
    if (!row || row > CREATURE_EVOLUTION_COUNT || creature_evolutions[row - 1].to != id) return 0;
    return &creature_evolutions[row - 1];
}

int creatures_form_id_valid(unsigned id) { return id >= 1 && id <= CREATURE_FORM_CAPACITY; }
const CreatureForm *creatures_form(unsigned id) {
    unsigned row;
    if (!creatures_form_id_valid(id)) return 0;
    row = creature_form_index[id];
    if (!row || row > CREATURE_ENABLED_COUNT || creature_forms[row - 1].id != id) return 0;
    return &creature_forms[row - 1];
}
const CreatureAbility *creatures_ability(unsigned id) {
    unsigned row;
    if (!id || id > 255) return 0;
    row = creature_ability_index[id];
    if (!row || row > CREATURE_ABILITY_COUNT || creature_abilities[row - 1].id != id) return 0;
    return &creature_abilities[row - 1];
}
unsigned creatures_legacy_spirit(unsigned id) {
    const CreatureForm *f = creatures_form(id);
    /* Current lineage survives a reviewed third tier. Historical validation
     * uses its independent revision lookup, never this expandable mapping. */
    return f && f->family >= 1 && f->family <= 4 ? f->family - 1u : CREATURE_EMPTY_SLOT;
}
CreatureU32 creatures_capabilities(unsigned id) {
    const CreatureForm *f = creatures_form(id);
    return f ? f->field_caps : 0;
}
int creatures_has_capability(unsigned id, CreatureU32 needed) {
    const CreatureForm *f = creatures_form(id);
    return f && (f->field_caps & needed) == needed;
}
/* Stable keyed capabilities preserve legacy masks as one projection. Future
 * non-projectable keys require explicit registry and per-form membership rows;
 * zero projection is never interpreted as permission or as no capability. */
typedef struct CreatureCapabilityPolicy {
    CreatureCapabilityId id;
    CreatureU32 legacy_mask;
} CreatureCapabilityPolicy;
typedef struct CreatureCapabilityMembership {
    FormId form;
    CreatureCapabilityId capability;
} CreatureCapabilityMembership;
static const CreatureCapabilityPolicy capability_policy[] = {
    {1, FIELD_BREAK_CRACK},
    {2, FIELD_BURN_THORNS},
    {3, FIELD_DRAW_ORE},
    {4, FIELD_DRIVE_SAIL},
    {5, FIELD_EARTH_SOCKET},
    {6, FIELD_EXPOSE_FIRE},
    {7, FIELD_EXPOSE_STONE},
    {8, FIELD_EXPOSE_WIND},
    {9, FIELD_FILL_BASIN},
    {10, FIELD_FIRE_SOCKET},
    {11, FIELD_GROW_BRIDGE},
    {12, FIELD_GROW_ROOTS},
    {13, FIELD_IGNITE},
    {14, FIELD_LINK_POOLS},
    {15, FIELD_PRESS_WEIGHT},
    {16, FIELD_REVEAL_CURRENT},
    {17, FIELD_TUNE_LATCH},
    {18, FIELD_TURN_VANE},
    {19, FIELD_UNCAP_WELL},
    {20, FIELD_WIND_SOCKET},
    {21, FIELD_WOOD_SOCKET},
    {22, FIELD_REEL_LOAD},
    {23, FIELD_STORE_HEAT},
    {24, FIELD_FLOAT_LOAD},
    {25, FIELD_ALIGN_RAIL},
    {26, FIELD_REFRACT_BEAM},
    {27, FIELD_ECHO_OUTLINE},
    {28, FIELD_SHIFT_BALLAST},
    {29, FIELD_INSCRIBE_TRACE},
    {30, FIELD_UNFOLD_SCREEN},
};
/* Sentinel only: no extended/unreviewed action is enabled in revision 4. */
static const CreatureCapabilityMembership capability_memberships[] = {
    {0, 0},
};
static const CreatureCapabilityPolicy *capability_policy_for_id(unsigned id) {
    unsigned i;
    if (!id || id > 65535u) return 0;
    for (i = 0; i < sizeof(capability_policy) / sizeof(capability_policy[0]); ++i)
        if (capability_policy[i].id == id) return &capability_policy[i];
    return 0;
}
int creatures_supports_capability(unsigned form, unsigned id) {
    const CreatureCapabilityPolicy *p = capability_policy_for_id(id);
    const CreatureForm *f = creatures_form(form);
    unsigned i;
    if (!p || !f) return 0;
    if (p->legacy_mask) return (f->field_caps & p->legacy_mask) == p->legacy_mask;
    for (i = 0; i < sizeof(capability_memberships) / sizeof(capability_memberships[0]); ++i)
        if (capability_memberships[i].form == form && capability_memberships[i].capability == id) return 1;
    return 0;
}
static int extended_capabilities_inherited(unsigned from, unsigned to) {
    unsigned i;
    for (i = 0; i < sizeof(capability_memberships) / sizeof(capability_memberships[0]); ++i)
        if (capability_memberships[i].form == from &&
            !creatures_supports_capability(to, capability_memberships[i].capability)) return 0;
    return 1;
}

unsigned creatures_phase_multiplier_q8(unsigned a, unsigned d) {
    /* Order: Wood -> Earth -> Water -> Fire -> Metal -> Wood. */
    static const CreatureU8 controls[5] = {2, 3, 4, 0, 1};
    if (a >= 5 || d >= 5) return 0;
    if (controls[a] == d) return 320;
    if (controls[d] == a) return 224;
    return 256;
}
unsigned creatures_generated_phase(unsigned p) {
    if (p >= 5) return CREATURE_EMPTY_SLOT;
    return p == 4 ? 0 : p + 1;
}
CreatureU32 creatures_xp_threshold(unsigned level) {
    CreatureU32 n;
    if (level < 1 || level > 50) return U32_MAX_VALUE;
    n = level - 1;
    return 4u * n * n * n;
}
unsigned creatures_level_for_xp(CreatureU32 xp) {
    unsigned lo = 1, hi = 50;
    while (lo < hi) {
        unsigned mid = (lo + hi + 1) >> 1;
        if (creatures_xp_threshold(mid) <= xp) lo = mid;
        else hi = mid - 1;
    }
    return lo;
}
int creatures_command_learned(unsigned id, unsigned level, unsigned ability) {
    const CreatureForm *f = creatures_form(id);
    unsigned j;
    if (!f || level < 1 || level > 50 || !creatures_ability(ability) ||
        f->learnset_offset + f->learnset_count > CREATURE_LEARNSET_COUNT) return 0;
    for (j = 0; j < f->learnset_count; ++j) {
        const CreatureLearn *l = &creature_learnsets[f->learnset_offset + j];
        if (l->ability_id == ability && l->level <= level) return 1;
    }
    return 0;
}
unsigned creatures_evolution_count(unsigned id) {
    const CreatureForm *f = creatures_form(id);
    unsigned i;
    if (!f || f->evolution_offset + f->evolution_count > CREATURE_EVOLUTION_COUNT) return 0;
    for (i = 0; i < f->evolution_count; ++i)
        if (creature_evolutions[f->evolution_offset + i].from != id) return 0;
    return f->evolution_count;
}
const CreatureEvolution *creatures_evolution_at(unsigned id, unsigned ordinal) {
    const CreatureForm *f = creatures_form(id);
    if (!f || ordinal >= creatures_evolution_count(id)) return 0;
    return &creature_evolutions[f->evolution_offset + ordinal];
}
const CreatureEvolution *creatures_evolution_to(unsigned id, unsigned target) {
    unsigned i, count;
    const CreatureForm *from = creatures_form(id), *to = creatures_form(target);
    if (!from || !to || from->family != to->family) return 0;
    count = creatures_evolution_count(id);
    for (i = 0; i < count; ++i)
        if (creature_evolutions[from->evolution_offset + i].to == target)
            return &creature_evolutions[from->evolution_offset + i];
    return 0;
}
const CreatureEvolution *creatures_evolution(unsigned id) {
    return creatures_evolution_count(id) == 1 ? creatures_evolution_at(id, 0) : 0;
}
#include "creature_validation.inc"
/* Standalone party callers validate members. Full roster validation checks
 * the same structure here, then validates every record exactly once below. */
static int party_validate(const CreatureRoster *r, int validate_instances, unsigned revision) {
    unsigned i, j, members = 0, legendary = 0;
    if (!r) return 0;
    for (i = 0; i < 4; ++i) {
        unsigned slot = r->party[i];
        const CreatureInstance *c;
        const CreatureForm *f;
        if (slot == CREATURE_EMPTY_SLOT) continue;
        if (slot >= 160) return 0;
        c = &r->instances[slot];
        if (!c->form_id || (validate_instances &&
            !(revision ? creatures_instance_validate_revision(c, revision) : creatures_instance_validate(c)))) return 0;
        f = revision ? 0 : creatures_form(c->form_id);
        if (revision ? !creatures_form_allowed_revision(c->form_id, revision) : !f) return 0;
        for (j = 0; j < i; ++j) if (slot == r->party[j]) return 0;
        ++members;
        legendary += f && f->rarity != 0; /* revisions1-5 have no legendary */
    }
    if (legendary > 1) return 0;
    if (!members) return r->selected_party == CREATURE_EMPTY_SLOT;
    return r->selected_party < 4 && r->party[r->selected_party] != CREATURE_EMPTY_SLOT;
}
int creatures_party_validate(const CreatureRoster *r) { return party_validate(r, 1, 0); }
CREATURE_INLINE int roster_validate(const CreatureRoster *r, unsigned revision) {
    unsigned i, j, stories = 0;
    if (!r || !r->next_instance_id || !party_validate(r, 0, revision)) return 0;
    /* Subset is byte-exact; only set discovery bits need an identity lookup.
     * Obtained-only bits still reject, including disabled/reserved identities. */
    for (i = 0; i < sizeof(r->seen); ++i) {
        unsigned bits = r->seen[i], bit = 0;
        if (r->obtained[i] & (CreatureU8)~r->seen[i]) return 0;
        while (bits) {
            if ((bits & 1u) && !(revision ?
                creatures_form_allowed_revision(i * 8u + bit + 1u, revision) :
                creatures_form(i * 8u + bit + 1u) != 0)) return 0;
            bits >>= 1; ++bit;
        }
    }
    for (i = 0; i < 160; ++i) {
        const CreatureInstance *c = &r->instances[i];
        unsigned legacy;
        /* Empty slots still check all24 bytes and their credit. Keep this
         * exact check here to avoid160 large validator call frames; occupied
         * records always take the full current or exact historical path. */
        if (!c->form_id) {
            if (!instance_is_zero(c) || r->expedition_bond[i]) return 0;
            continue;
        }
        if (!(revision ? creatures_instance_validate_revision(c, revision) : creatures_instance_validate(c)) || r->expedition_bond[i] > 10) return 0;
        if (c->instance_id >= r->next_instance_id || !bit_get(r->obtained, c->form_id - 1)) return 0;
        for (j = 0; j < i; ++j)
            if (c->instance_id == r->instances[j].instance_id) return 0;
        if (c->flags & CREATURE_STORY_LOCKED) {
            legacy = revision ? creatures_legacy_spirit_revision(c->form_id, revision) : creatures_legacy_spirit(c->form_id);
            if (legacy >= 4 || (stories & (1u << legacy)) || !bit_get(r->rewards, legacy)) return 0;
            stories |= 1u << legacy;
        }
    }
    return stories == (r->rewards[0] & 15u);
}
int creatures_roster_validate(const CreatureRoster *r) { return roster_validate(r, 0); }
int creatures_roster_validate_revision(const CreatureRoster *r, unsigned revision) {
    if (revision == CREATURE_CONTENT_REVISION) return creatures_roster_validate(r);
    return revision >= 1 && revision <= 7 && roster_validate(r, revision);
}
void creatures_roster_init(CreatureRoster *r) {
    unsigned i;
    if (!r) return;
    clear_bytes(r, sizeof(*r));
    for (i = 0; i < 4; ++i) r->party[i] = CREATURE_EMPTY_SLOT;
    r->selected_party = CREATURE_EMPTY_SLOT;
    r->next_instance_id = 1;
}
unsigned creatures_roster_count(const CreatureRoster *r) {
    unsigned i, n = 0;
    if (!r) return 0;
    for (i = 0; i < 160; ++i) n += r->instances[i].form_id != 0;
    return n;
}
/* Separately reviewed immutable capacity policy. This duplication is258 ROM
 * bytes, no mutable RAM; it makes stale/corrupt generated metadata fail closed. */
static const CreatureTerminalPolicy terminal_policy_expected[129] = {
    {0, 0},
    {1, 1},
    {1, 1},
    {1, 1},
    {2, 1},
    {2, 1},
    {2, 1},
    {3, 1},
    {3, 1},
    {3, 1},
    {4, 1},
    {4, 1},
    {4, 1},
    {5, 1},
    {5, 1},
    {5, 1},
    {6, 1},
    {6, 1},
    {6, 1},
    {7, 1},
    {7, 1},
    {7, 1},
    {8, 1},
    {8, 1},
    {8, 1},
    {9, 1},
    {9, 1},
    {9, 1},
    {10, 1},
    {10, 1},
    {10, 1},
    {11, 1},
    {11, 1},
    {11, 1},
    {12, 1},
    {12, 1},
    {12, 1},
    {13, 3},
    {13, 1},
    {13, 2},
    {14, 3},
    {14, 1},
    {14, 2},
    {15, 3},
    {15, 1},
    {15, 2},
    {16, 3},
    {16, 1},
    {16, 2},
    {17, 3},
    {17, 1},
    {17, 2},
    {18, 3},
    {18, 1},
    {18, 2},
    {19, 3},
    {19, 1},
    {19, 2},
    {20, 3},
    {20, 1},
    {20, 2},
    {21, 3},
    {21, 1},
    {21, 2},
    {22, 3},
    {22, 1},
    {22, 2},
    {23, 3},
    {23, 1},
    {23, 2},
    {24, 3},
    {24, 1},
    {24, 2},
    {25, 1},
    {25, 1},
    {26, 1},
    {26, 1},
    {27, 1},
    {27, 1},
    {28, 1},
    {28, 1},
    {29, 1},
    {29, 1},
    {30, 1},
    {30, 1},
    {31, 1},
    {31, 1},
    {32, 1},
    {32, 1},
    {33, 1},
    {33, 1},
    {34, 1},
    {34, 1},
    {35, 1},
    {35, 1},
    {36, 1},
    {36, 1},
    {37, 1},
    {37, 1},
    {38, 1},
    {38, 1},
    {39, 1},
    {39, 1},
    {40, 1},
    {40, 1},
    {41, 1},
    {41, 1},
    {42, 1},
    {42, 1},
    {43, 1},
    {43, 1},
    {44, 1},
    {44, 1},
    {45, 1},
    {46, 1},
    {47, 1},
    {48, 1},
    {49, 1},
    {50, 1},
    {51, 1},
    {52, 1},
    {53, 1},
    {54, 1},
    {55, 1},
    {56, 1},
    {57, 1},
    {58, 1},
    {59, 1},
    {60, 1},
};
/* Final terminal opportunities are a reservation, not an enablement table. */
unsigned creatures_terminal_family(unsigned id) {
    const CreatureTerminalPolicy *p;
    if (!creatures_form_id_valid(id)) return 0;
    p = &creature_terminal_policy[id];
    return p->family >= 1 && p->family <= CREATURE_FAMILY_CAPACITY &&
           p->terminal_mask >= 1 && p->terminal_mask <= 3 &&
           p->family == terminal_policy_expected[id].family &&
           p->terminal_mask == terminal_policy_expected[id].terminal_mask ? p->family : 0;
}
unsigned creatures_terminal_mask(unsigned id) {
    return creatures_terminal_family(id) ? creature_terminal_policy[id].terminal_mask : 0;
}
static void coverage_finish(CreatureCoverage *c) {
    c->excess = (CreatureU16)(c->occupied - c->viable);
    c->free_slots = (CreatureU16)(CREATURE_ROSTER_CAPACITY - c->occupied);
    c->missing_opportunities = (CreatureU16)(CREATURE_TERMINAL_OPPORTUNITIES - c->viable);
    c->admission_safe = (CreatureU16)(c->excess <= CREATURE_EXTRA_COPY_BUDGET);
}
static unsigned coverage_local(unsigned count, unsigned mask) {
    unsigned bits = (mask & 1u) + ((mask >> 1) & 1u);
    return count < bits ? count : bits;
}
static int coverage_add(CreatureCoverage *out, CreatureU8 counts[60],
                        CreatureU8 masks[60], unsigned id) {
    unsigned family = creatures_terminal_family(id), index, before, after;
    if (!family || out->occupied >= CREATURE_ROSTER_CAPACITY) return 0;
    index = family - 1u;
    before = coverage_local(counts[index], masks[index]);
    if (counts[index] < 2) ++counts[index];
    masks[index] |= (CreatureU8)creatures_terminal_mask(id);
    after = coverage_local(counts[index], masks[index]);
    ++out->occupied;
    out->viable = (CreatureU16)(out->viable + after - before);
    return out->viable <= CREATURE_TERMINAL_OPPORTUNITIES;
}
/* Exactly one bounded coverage scan. Capped counts plus target unions compute
 * maximum matching for the reviewed one-/two-terminal topology. Skip supports
 * an explicit virtual replacement without copying or mutating any instance. */
static int coverage_scan(const CreatureRoster *r, unsigned skip,
                         CreatureU8 counts[60], CreatureU8 masks[60],
                         CreatureCoverage *out) {
    unsigned i;
    clear_bytes(counts, 60); clear_bytes(masks, 60); clear_bytes(out, sizeof(*out));
    for (i = 0; i < CREATURE_ROSTER_CAPACITY; ++i)
        if (i != skip && r->instances[i].form_id &&
            !coverage_add(out, counts, masks, r->instances[i].form_id)) return 0;
    coverage_finish(out);
    return 1;
}
int creatures_collection_coverage(const CreatureRoster *r, CreatureCoverage *out) {
    CreatureU8 counts[60], masks[60];
    if (!out) return 0;
    clear_bytes(out, sizeof(*out));
    if (!r || !creatures_roster_validate(r)) return 0;
    if (!coverage_scan(r, CREATURE_EMPTY_SLOT, counts, masks, out)) {
        clear_bytes(out, sizeof(*out));
        return 0;
    }
    return 1;
}
int creatures_admission_allowed(enum CreatureAdmissionStatus status) {
    return status == CREATURE_ADMISSION_READY ||
           status == CREATURE_ADMISSION_GRANDFATHERED_READY;
}
static enum CreatureAdmissionStatus admission_query_validated(const CreatureRoster *r,
    unsigned id, unsigned slot, CreatureAdmission *detail) {
    CreatureU8 counts[60], masks[60];
    CreatureAdmission result;
    unsigned family, saved_count = 0, saved_mask = 0;
    enum CreatureAdmissionStatus status;
    if (detail) clear_bytes(detail, sizeof(*detail));
    if (!r || !creatures_form(id))
        return CREATURE_ADMISSION_INVALID;
    if (slot != CREATURE_EMPTY_SLOT &&
        (slot >= CREATURE_ROSTER_CAPACITY || !r->instances[slot].form_id ||
         !creatures_evolution_to(r->instances[slot].form_id, id)))
        return CREATURE_ADMISSION_INVALID;
    family = creatures_terminal_family(id);
    if (!family || !coverage_scan(r, slot, counts, masks, &result.before))
        return CREATURE_ADMISSION_INVALID;
    result.after = result.before;
    if (slot != CREATURE_EMPTY_SLOT) {
        /* Same-family edge only. Temporarily restore the actual individual to
         * compute before, then insert the explicit candidate from the same base. */
        saved_count = counts[family - 1u]; saved_mask = masks[family - 1u];
        if (!coverage_add(&result.before, counts, masks, r->instances[slot].form_id))
            return CREATURE_ADMISSION_INVALID;
        coverage_finish(&result.before);
        counts[family - 1u] = (CreatureU8)saved_count;
        masks[family - 1u] = (CreatureU8)saved_mask;
    } else if (result.before.occupied == CREATURE_ROSTER_CAPACITY) {
        if (detail) *detail = result;
        return CREATURE_ADMISSION_FULL;
    }
    if (!coverage_add(&result.after, counts, masks, id)) return CREATURE_ADMISSION_INVALID;
    coverage_finish(&result.after);
    if (result.after.admission_safe) status = CREATURE_ADMISSION_READY;
    else if (!result.before.admission_safe &&
             result.after.excess <= result.before.excess &&
             result.after.viable >= result.before.viable)
        status = CREATURE_ADMISSION_GRANDFATHERED_READY;
    else status = slot == CREATURE_EMPTY_SLOT ? CREATURE_ADMISSION_RESERVED :
                                              CREATURE_ADMISSION_COVERAGE_LOSS;
    if (detail) *detail = result;
    return status;
}
enum CreatureAdmissionStatus creatures_admission_query_grant(
    const CreatureRoster *r, unsigned id, CreatureAdmission *detail) {
    if (!r || !creatures_roster_validate(r)) {
        if (detail) clear_bytes(detail, sizeof(*detail));
        return CREATURE_ADMISSION_INVALID;
    }
    return admission_query_validated(r, id, CREATURE_EMPTY_SLOT, detail);
}
enum CreatureAdmissionStatus creatures_admission_query_evolution(
    const CreatureRoster *r, unsigned slot, unsigned target, CreatureAdmission *detail) {
    if (!r || slot >= CREATURE_ROSTER_CAPACITY || !creatures_roster_validate(r)) {
        if (detail) clear_bytes(detail, sizeof(*detail));
        return CREATURE_ADMISSION_INVALID;
    }
    return admission_query_validated(r, target, slot, detail);
}
static unsigned grant_validated(CreatureRoster *r, unsigned id, unsigned level,
    unsigned bond, unsigned flags, unsigned reward);
enum CreatureAdmissionStatus creatures_grant_admitted(CreatureRoster *r,
    unsigned id, unsigned level, unsigned bond, unsigned flags, unsigned reward,
    unsigned *out_slot) {
    enum CreatureAdmissionStatus status;
    unsigned slot, legacy;
    if (out_slot) *out_slot = CREATURE_EMPTY_SLOT;
    if (!r || !creatures_form(id) || level < 1 || level > 50 || bond > 100 ||
        (flags & ~(CREATURE_STORY_LOCKED | CREATURE_FAVORITE)) || reward > 128 ||
        !creatures_roster_validate(r)) return CREATURE_ADMISSION_INVALID;
    legacy = creatures_legacy_spirit(id);
    if (flags & CREATURE_STORY_LOCKED) {
        if (legacy >= 4 || reward != legacy + 1u) return CREATURE_ADMISSION_INVALID;
    } else if (reward && reward <= 4) return CREATURE_ADMISSION_INVALID;
    /* Preserve source retry semantics even at physical/reserved capacity. */
    if (reward && bit_get(r->rewards, reward - 1u)) return CREATURE_ADMISSION_ALREADY_CLAIMED;
    if (r->next_instance_id == U32_MAX_VALUE) return CREATURE_ADMISSION_ID_EXHAUSTED;
    status = admission_query_validated(r, id, CREATURE_EMPTY_SLOT, 0);
    if (!creatures_admission_allowed(status)) return status;
    slot = grant_validated(r, id, level, bond, flags, reward);
    if (slot == CREATURE_EMPTY_SLOT) return CREATURE_ADMISSION_INVALID;
    if (out_slot) *out_slot = slot;
    return status;
}

CreatureU32 creatures_party_capabilities(const CreatureRoster *r) {
    CreatureU32 caps = 0;
    unsigned i;
    if (!creatures_party_validate(r)) return 0;
    for (i = 0; i < 4; ++i)
        if (r->party[i] != CREATURE_EMPTY_SLOT)
            caps |= creatures_capabilities(r->instances[r->party[i]].form_id);
    return caps;
}
int creatures_party_set(CreatureRoster *r, const CreatureU8 party[4], CreatureU32 required) {
    CreatureU8 old[4];
    unsigned i, selected;
    if (!r || !party || !creatures_party_validate(r)) return 0;
    selected = r->selected_party;
    for (i = 0; i < 4; ++i) old[i] = r->party[i];
    for (i = 0; i < 4; ++i) r->party[i] = party[i];
    /* Keep active creature identity across party sorting when possible. */
    r->selected_party = CREATURE_EMPTY_SLOT;
    if (selected < 4)
        for (i = 0; i < 4; ++i)
            if (r->party[i] == old[selected]) r->selected_party = (CreatureU8)i;
    if (r->selected_party == CREATURE_EMPTY_SLOT)
        for (i = 0; i < 4; ++i)
            if (r->party[i] != CREATURE_EMPTY_SLOT) { r->selected_party = (CreatureU8)i; break; }
    if (creatures_party_validate(r) && (creatures_party_capabilities(r) & required) == required) return 1;
    for (i = 0; i < 4; ++i) r->party[i] = old[i];
    r->selected_party = (CreatureU8)selected;
    return 0;
}
int creatures_party_supports_capability(const CreatureRoster *r, unsigned id) {
    unsigned i;
    if (!capability_policy_for_id(id) || !creatures_party_validate(r)) return 0;
    for (i = 0; i < CREATURE_PARTY_CAPACITY; ++i)
        if (r->party[i] < CREATURE_ROSTER_CAPACITY &&
            creatures_supports_capability(r->instances[r->party[i]].form_id, id)) return 1;
    return 0;
}
int creatures_party_set_requirements(CreatureRoster *r, const CreatureU8 party[4],
                                     const CreatureCapabilityId *required, unsigned count) {
    CreatureU8 old[CREATURE_PARTY_CAPACITY], selected;
    unsigned i;
    if (!r || !party || count > CREATURE_ROUTE_REQUIREMENTS_MAX ||
        (count && !required) || !creatures_party_validate(r)) return 0;
    for (i = 0; i < count; ++i) if (!capability_policy_for_id(required[i])) return 0;
    selected = r->selected_party;
    for (i = 0; i < CREATURE_PARTY_CAPACITY; ++i) old[i] = r->party[i];
    if (!creatures_party_set(r, party, 0)) return 0;
    for (i = 0; i < count; ++i) if (!creatures_party_supports_capability(r, required[i])) {
        unsigned j;
        for (j = 0; j < CREATURE_PARTY_CAPACITY; ++j) r->party[j] = old[j];
        r->selected_party = selected;
        return 0;
    }
    return 1;
}
static unsigned grant_validated(CreatureRoster *r, unsigned id, unsigned level,
                         unsigned bond, unsigned flags, unsigned reward) {
    const CreatureForm *f = creatures_form(id);
    CreatureInstance c;
    unsigned i, j, legacy;
    if (!r || !f || level < 1 || level > 50 || bond > 100 ||
        (flags & ~(CREATURE_STORY_LOCKED | CREATURE_FAVORITE)) || reward > 128 ||
        r->next_instance_id == U32_MAX_VALUE ||
        (reward && bit_get(r->rewards, reward - 1))) return CREATURE_EMPTY_SLOT;
    legacy = creatures_legacy_spirit(id);
    if (flags & CREATURE_STORY_LOCKED) {
        if (legacy >= 4 || reward != legacy + 1) return CREATURE_EMPTY_SLOT;
    } else if (reward && reward <= 4) return CREATURE_EMPTY_SLOT;
    for (i = 0; i < 160; ++i) if (!r->instances[i].form_id) break;
    if (i == 160) return CREATURE_EMPTY_SLOT;
    clear_bytes(&c, sizeof(c));
    c.form_id = (CreatureU8)id; c.flags = (CreatureU8)(flags | CREATURE_OCCUPIED);
    c.level = (CreatureU8)level; c.bond = (CreatureU8)bond;
    c.xp = creatures_xp_threshold(level); c.instance_id = r->next_instance_id;
    c.polarity = f->polarity;
    c.equipped[0] = creature_learnsets[f->learnset_offset].ability_id;
    c.cosmetic_seed = c.instance_id * 2654435761u;
    if (!creatures_instance_validate(&c)) return CREATURE_EMPTY_SLOT;
    r->instances[i] = c; ++r->next_instance_id;
    bit_set(r->seen, id - 1); bit_set(r->obtained, id - 1);
    if (reward) bit_set(r->rewards, reward - 1);
    r->expedition_bond[i] = 0;
    for (j = 0; j < 4; ++j) {
        if (r->party[j] == CREATURE_EMPTY_SLOT) {
            r->party[j] = (CreatureU8)i;
            if (r->selected_party == CREATURE_EMPTY_SLOT) r->selected_party = (CreatureU8)j;
            break;
        }
    }
    return i;
}
unsigned creatures_grant(CreatureRoster *r, unsigned id, unsigned level,
                         unsigned bond, unsigned flags, unsigned reward) {
    if (!r || !creatures_roster_validate(r)) return CREATURE_EMPTY_SLOT;
    return grant_validated(r, id, level, bond, flags, reward);
}
static unsigned party_median_level(const CreatureRoster *r) {
    unsigned levels[4], n = 0, i, j;
    for (i = 0; i < 4; ++i) if (r->party[i] < 160) {
        unsigned value = r->instances[r->party[i]].level;
        j = n;
        while (j && levels[j - 1] > value) { levels[j] = levels[j - 1]; --j; }
        levels[j] = value; ++n;
    }
    if (!n) return 1;
    return n & 1 ? levels[n >> 1] : (levels[(n >> 1) - 1] + levels[n >> 1]) / 2;
}
unsigned creatures_grant_story(CreatureRoster *r, unsigned legacy, unsigned chapters) {
    static const CreatureU8 floor[4] = {1, 1, 8, 14};
    unsigned i, level;
    if (!r || legacy >= 4 || (legacy == 2 && !(chapters & CREATURE_GROVE_CLEAR)) ||
        (legacy == 3 && !(chapters & CREATURE_SKY_CLEAR)) || !creatures_roster_validate(r))
        return CREATURE_EMPTY_SLOT;
    if (bit_get(r->rewards, legacy)) {
        for (i = 0; i < 160; ++i)
            if ((r->instances[i].flags & CREATURE_STORY_LOCKED) &&
                creatures_legacy_spirit(r->instances[i].form_id) == legacy) return i;
        return CREATURE_EMPTY_SLOT;
    }
    level = party_median_level(r);
    if (level < floor[legacy]) level = floor[legacy];
    {
        unsigned slot;
        enum CreatureAdmissionStatus status = creatures_grant_admitted(r,
            creature_legacy_forms[legacy], level, 20, CREATURE_STORY_LOCKED,
            legacy + 1u, &slot);
        return creatures_admission_allowed(status) ? slot : CREATURE_EMPTY_SLOT;
    }
}
int creatures_apply_story_floors(CreatureRoster *r, unsigned chapters) {
    unsigned i, changed = 0;
    if (!r || !creatures_roster_validate(r)) return 0;
    for (i = 0; i < 160; ++i) {
        CreatureInstance *c = &r->instances[i];
        unsigned legacy, level = 0, bond = 0;
        if (!(c->flags & CREATURE_STORY_LOCKED)) continue;
        legacy = creatures_legacy_spirit(c->form_id);
        if (chapters & CREATURE_CORE_CLEAR) { level = 20; bond = legacy == 2 ? 55 : 50; }
        else if (chapters & CREATURE_SKY_CLEAR) {
            if (legacy < 3) { level = 16; bond = legacy == 2 ? 45 : 40; }
        } else if ((chapters & CREATURE_GROVE_CLEAR) && legacy < 2) { level = 12; bond = 30; }
        /* A completed one-time trial stays additive to story compensation. */
        if (bond && (c->trial_flags & (1u << legacy))) bond += 10;
        if (c->level < level) { c->level = (CreatureU8)level; c->xp = creatures_xp_threshold(level); changed = 1; }
        if (c->bond < bond) { c->bond = (CreatureU8)bond; changed = 1; }
    }
    return (int)changed;
}
int creatures_migrate_legacy(CreatureRoster *r, unsigned chapters, unsigned selected) {
    static const CreatureU8 floors[4] = {1, 1, 8, 14};
    unsigned i, count = 2;
    if (!r || (chapters & ~15u) ||
        ((chapters & CREATURE_SKY_CLEAR) && !(chapters & CREATURE_GROVE_CLEAR)) ||
        ((chapters & CREATURE_CORE_CLEAR) && !(chapters & CREATURE_SKY_CLEAR)) ||
        ((chapters & 8u) && !(chapters & CREATURE_CORE_CLEAR))) return 0;
    if (chapters & CREATURE_GROVE_CLEAR) count = 3;
    if (chapters & CREATURE_SKY_CLEAR) count = 4;
    if (selected >= count) return 0;
    creatures_roster_init(r);
    for (i = 0; i < count; ++i)
        if (creatures_grant(r, creature_legacy_forms[i], floors[i], 20, CREATURE_STORY_LOCKED, i + 1) == CREATURE_EMPTY_SLOT) return 0;
    r->selected_party = (CreatureU8)selected;
    creatures_apply_story_floors(r, chapters);
    return creatures_roster_validate(r);
}
int creatures_add_xp(CreatureInstance *c, CreatureU32 amount) {
    if (!c || !c->form_id || !creatures_instance_validate(c)) return 0;
    if (amount > CREATURE_XP_CAP - c->xp) c->xp = CREATURE_XP_CAP;
    else c->xp += amount;
    c->level = (CreatureU8)creatures_level_for_xp(c->xp);
    return 1;
}
int creatures_equip(CreatureInstance *c, unsigned slot, unsigned ability) {
    if (!c || !c->form_id || !creatures_instance_validate(c) || slot > 1 ||
        (ability && !creatures_command_learned(c->form_id, c->level, ability)) ||
        (ability && c->equipped[slot ^ 1] == ability) ||
        (!ability && c->selected_command == slot)) return 0;
    c->equipped[slot] = (CreatureU8)ability;
    return 1;
}
int creatures_select_command(CreatureInstance *c, unsigned slot) {
    if (!c || !c->form_id || !creatures_instance_validate(c) || slot > 1 || !c->equipped[slot]) return 0;
    c->selected_command = (CreatureU8)slot;
    return 1;
}
void creatures_begin_expedition(CreatureRoster *r) {
    if (!r) return;
    clear_bytes(r->expedition_bond, sizeof(r->expedition_bond));
    clear_bytes(r->expedition_events, sizeof(r->expedition_events));
}
int creatures_credit_event(CreatureRoster *r, unsigned event, CreatureU32 xp, unsigned kind) {
    unsigned i, members = 0, bond;
    if (!r || !creatures_party_validate(r) || event >= 512 || kind > CREATURE_CREDIT_PERSONAL_QUEST ||
        (kind == CREATURE_CREDIT_FIELD_AID ? event < 384 : event >= 384)) return -1;
    if (bit_get(r->expedition_events, event)) return 0;
    for (i = 0; i < 4; ++i) if (r->party[i] < 160) {
        ++members;
        if (r->expedition_bond[r->party[i]] > 10) return -1;
    }
    if (!members) return 0;
    bond = kind == CREATURE_CREDIT_ENCOUNTER ? 1 : (kind == CREATURE_CREDIT_FIELD_AID ? 3 : 10);
    if (kind == CREATURE_CREDIT_FIELD_AID && bit_get(r->lifetime_field_aid, event - 384)) bond = 0;
    bit_set(r->expedition_events, event);
    if (kind == CREATURE_CREDIT_FIELD_AID) bit_set(r->lifetime_field_aid, event - 384);
    for (i = 0; i < 4; ++i) if (r->party[i] < 160) {
        unsigned slot = r->party[i], gain = bond;
        CreatureInstance *c = &r->instances[slot];
        creatures_add_xp(c, xp);
        if (gain > 10u - r->expedition_bond[slot]) gain = 10u - r->expedition_bond[slot];
        if (gain > 100u - c->bond) gain = 100u - c->bond;
        c->bond += (CreatureU8)gain; r->expedition_bond[slot] += (CreatureU8)gain;
    }
    return 1;
}
int creatures_mark_trial(CreatureInstance *c, unsigned flag) {
    unsigned required;
    if (!c || !c->form_id || !creatures_instance_validate(c)) return 0;
    required = creatures_family_trial(c->form_id);
    if (!required || flag != required) return 0;
    c->trial_flags |= (CreatureU16)flag;
    return 1;
}
static const CreatureTrialPolicy *qualified_trial(const CreatureInstance *c, unsigned family, unsigned key) {
    const CreatureTrialPolicy *p;
    const CreatureForm *f;
    if (!c || !c->form_id || !creatures_instance_validate(c) ||
        !family || family > CREATURE_FAMILY_CAPACITY || !key || key > 65535u) return 0;
    f = creatures_form(c->form_id);
    if (!f || f->family != family) return 0;
    p = trial_policy_for_key(family, key);
    if (!p || !p->mask || (p->mask & (p->mask - 1u)) ||
        (p->mask & ~creatures_trial_allowed_mask(f->id, CREATURE_CONTENT_REVISION)) ||
        (c->trial_flags & p->prerequisite) != p->prerequisite) return 0;
    return p;
}
int creatures_mark_trial_qualified(CreatureInstance *c, unsigned family, unsigned key) {
    const CreatureTrialPolicy *p = qualified_trial(c, family, key);
    if (!p) return 0;
    c->trial_flags |= p->mask;
    return 1;
}
int creatures_has_trial_qualified(const CreatureInstance *c, unsigned family, unsigned key) {
    const CreatureTrialPolicy *p = qualified_trial(c, family, key);
    return p && (c->trial_flags & p->mask) == p->mask;
}
static unsigned can_evolve_edge(const CreatureInstance *c, const CreatureEvolution *e,
                                unsigned context, int sanctuary) {
    const CreatureForm *from, *to;
    unsigned i;
    if (!e) return CREATURE_EVOLVE_NO_EDGE;
    from = creatures_form(c->form_id); to = creatures_form(e->to);
    if (!from || !to || e->from != from->id || from->family != to->family ||
        from->tier >= to->tier || !e->trial_flag ||
        !trial_subset_valid(family_policy_for_id(from->family), e->trial_flag) ||
        (from->field_caps & to->field_caps) != from->field_caps ||
        !extended_capabilities_inherited(from->id, to->id)) return CREATURE_EVOLVE_INVALID;
    /* Full command inheritance is checked even if an inherited slot happens
     * to be unequipped. An exact edge may not silently revoke a known action. */
    for (i = 0; i < from->learnset_count; ++i) {
        const CreatureLearn *l = &creature_learnsets[from->learnset_offset + i];
        if (!creatures_command_learned(to->id, l->level, l->ability_id)) return CREATURE_EVOLVE_INVALID;
    }
    if (c->level < e->min_level) return CREATURE_EVOLVE_LEVEL;
    if (c->bond < e->min_bond) return CREATURE_EVOLVE_BOND;
    if ((context & e->chapter_flags) != e->chapter_flags) return CREATURE_EVOLVE_STORY;
    if ((c->trial_flags & e->trial_flag) != e->trial_flag) return CREATURE_EVOLVE_TRIAL;
    if (!sanctuary) return CREATURE_EVOLVE_SANCTUARY;
    return CREATURE_EVOLVE_READY;
}
unsigned creatures_can_evolve_to(const CreatureInstance *c, unsigned target, unsigned context, int sanctuary) {
    if (!c || !c->form_id || !creatures_instance_validate(c) ||
        (context & ~CREATURE_EVOLUTION_CONTEXT_MASK) || !creatures_form(target)) return CREATURE_EVOLVE_INVALID;
    return can_evolve_edge(c, creatures_evolution_to(c->form_id, target), context, sanctuary);
}
unsigned creatures_can_evolve(const CreatureInstance *c, unsigned context, int sanctuary) {
    if (!c || !c->form_id || !creatures_instance_validate(c) ||
        (context & ~CREATURE_EVOLUTION_CONTEXT_MASK)) return CREATURE_EVOLVE_INVALID;
    if (creatures_evolution_count(c->form_id) > 1) return CREATURE_EVOLVE_AMBIGUOUS;
    return can_evolve_edge(c, creatures_evolution(c->form_id), context, sanctuary);
}
unsigned creatures_can_evolve_roster_to(const CreatureRoster *r, unsigned slot,
    unsigned target, unsigned context, int sanctuary) {
    unsigned status;
    enum CreatureAdmissionStatus admission;
    if (!r || slot >= CREATURE_ROSTER_CAPACITY || !creatures_roster_validate(r))
        return CREATURE_EVOLVE_INVALID;
    status = creatures_can_evolve_to(&r->instances[slot], target, context, sanctuary);
    if (status != CREATURE_EVOLVE_READY) return status;
    admission = admission_query_validated(r, target, slot, 0);
    if (creatures_admission_allowed(admission)) return CREATURE_EVOLVE_READY;
    return admission == CREATURE_ADMISSION_COVERAGE_LOSS ?
           CREATURE_EVOLVE_COLLECTION_RESERVED : CREATURE_EVOLVE_INVALID;
}
static unsigned evolve_ready(CreatureRoster *r, unsigned slot, unsigned target_id, int confirmed) {
    CreatureInstance *c = &r->instances[slot], candidate;
    const CreatureForm *target;
    if (!confirmed) return CREATURE_EVOLVE_DEFERRED;
    {
        enum CreatureAdmissionStatus admission = admission_query_validated(r, target_id, slot, 0);
        if (!creatures_admission_allowed(admission))
            return admission == CREATURE_ADMISSION_COVERAGE_LOSS ?
                   CREATURE_EVOLVE_COLLECTION_RESERVED : CREATURE_EVOLVE_INVALID;
    }
    target = creatures_form(target_id);
    if (!target) return CREATURE_EVOLVE_INVALID;
    candidate = *c; candidate.form_id = target->id; candidate.polarity = target->polarity;
    if (!creatures_instance_validate(&candidate)) return CREATURE_EVOLVE_INVALID;
    *c = candidate;
    bit_set(r->seen, c->form_id - 1); bit_set(r->obtained, c->form_id - 1);
    return CREATURE_EVOLVE_READY;
}
unsigned creatures_evolve_to(CreatureRoster *r, unsigned slot, unsigned target_id,
                             unsigned context, int sanctuary, int confirmed) {
    unsigned result;
    if (!r || slot >= CREATURE_ROSTER_CAPACITY || !creatures_roster_validate(r)) return CREATURE_EVOLVE_INVALID;
    result = creatures_can_evolve_to(&r->instances[slot], target_id, context, sanctuary);
    if (result != CREATURE_EVOLVE_READY) return result;
    return evolve_ready(r, slot, target_id, confirmed);
}
unsigned creatures_evolve(CreatureRoster *r, unsigned slot, unsigned context, int sanctuary, int confirmed) {
    const CreatureEvolution *e;
    unsigned result;
    if (!r || slot >= CREATURE_ROSTER_CAPACITY || !creatures_roster_validate(r)) return CREATURE_EVOLVE_INVALID;
    result = creatures_can_evolve(&r->instances[slot], context, sanctuary);
    if (result != CREATURE_EVOLVE_READY) return result;
    e = creatures_evolution(r->instances[slot].form_id);
    return evolve_ready(r, slot, e->to, confirmed);
}
unsigned creatures_defer_evolution(const CreatureInstance *c) {
    if (!c || !c->form_id || !creatures_instance_validate(c)) return CREATURE_EVOLVE_INVALID;
    return CREATURE_EVOLVE_DEFERRED;
}

#include "creature_admission_job.inc"
