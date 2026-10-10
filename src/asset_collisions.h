/* Generated static collisions. Dynamic obstacles remain engine-owned. */
#ifndef EMBERBOND_ASSET_COLLISIONS_H
#define EMBERBOND_ASSET_COLLISIONS_H
typedef struct { short x,y,w,h; } AssetRect;
static const AssetRect asset_solids_village[16] = {
    {22,44,67,53},
    {151,47,67,50},
    {40,115,27,36},
    {163,139,46,14},
    {97,27,4,24},
    {140,27,4,24},
    {94,80,11,15},
    {138,80,11,15},
    {0,0,21,43},
    {23,0,22,34},
    {49,0,25,34},
    {77,0,22,31},
    {141,0,22,31},
    {167,0,28,34},
    {201,0,25,37},
    {227,1,13,44},
};
#define ASSET_SOLIDS_VILLAGE_COUNT 16
static const AssetRect asset_solids_forest[23] = {
    {92,19,11,24},
    {138,19,11,24},
    {85,37,11,17},
    {145,37,11,17},
    {223,21,17,139},
    {0,0,21,47},
    {17,0,28,46},
    {46,0,30,36},
    {79,0,22,29},
    {139,0,25,28},
    {166,0,30,39},
    {198,2,28,44},
    {3,40,30,48},
    {36,37,25,40},
    {187,42,25,40},
    {0,86,25,52},
    {32,103,28,44},
    {186,103,28,44},
    {220,100,20,48},
    {13,133,28,27},
    {61,135,28,25},
    {155,133,28,27},
    {202,132,30,28},
};
#define ASSET_SOLIDS_FOREST_COUNT 23
static const AssetRect asset_solids_temple[8] = {
    {0,0,24,160},
    {216,0,24,160},
    {24,0,79,31},
    {138,0,78,31},
    {34,36,13,15},
    {189,36,13,15},
    {35,129,13,15},
    {190,129,13,15},
};
#define ASSET_SOLIDS_TEMPLE_COUNT 8
static const AssetRect asset_solids_boss[20] = {
    {11,46,27,36},
    {203,46,27,36},
    {11,105,27,36},
    {203,105,27,36},
    {0,0,19,50},
    {17,0,30,33},
    {52,0,30,20},
    {93,0,25,12},
    {125,0,25,13},
    {161,0,30,21},
    {196,0,30,34},
    {222,3,18,52},
    {0,58,17,48},
    {222,57,18,48},
    {0,116,20,44},
    {20,146,30,14},
    {58,154,30,6},
    {152,154,30,6},
    {192,148,30,12},
    {224,115,16,45},
};
#define ASSET_SOLIDS_BOSS_COUNT 20
static const AssetRect * const asset_solids[4] = {asset_solids_village,asset_solids_forest,asset_solids_temple,asset_solids_boss};
static const unsigned char asset_solids_count[4] = {16,23,8,20};
#endif
