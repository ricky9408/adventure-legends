/* Generated from the exact original room geometry; no reward state. */
typedef struct {short x,y;unsigned char command,station,beat,radius;} StationTarget;
static const StationTarget station_targets[8][8]={
{{120,216,106,0,1,3},{170,112,108,1,1,3},{160,124,108,1,2,3},{320,92,110,2,1,3},{312,220,102,3,1,3},{120,136,104,4,1,3}},
{{48,88,106,0,1,3},{192,88,104,1,1,3}},
{{106,104,108,0,1,3},{96,116,108,0,2,3},{216,84,102,1,1,3}},
{{48,44,110,0,1,3},{192,40,106,1,1,3}},
{{192,96,106,0,1,3},{280,96,102,1,1,3}},
{{120,40,106,0,1,3},{106,160,112,1,1,3}},
{{96,76,110,0,1,3},{240,88,104,1,1,3},{384,96,104,2,1,3}},
{{82,112,108,0,1,3},{72,124,108,0,2,3},{120,76,110,1,1,3},{160,92,102,2,1,3}},
};
static const unsigned char station_counts[8]={6,2,3,2,2,2,3,4};
static const short manual_points[8][2][2]={
{{144,264},{352,176}},
{{120,232}},
{{336,104}},
{{120,128}},
{{120,240},{240,136}},
{{192,232}},
{{384,120}},
{{120,120}},
};
static const unsigned char manual_counts[8]={2,1,1,1,2,1,1,1};
typedef struct {unsigned char sprite;short x,y;} ResidentDef;
static const ResidentDef residents[8][4]={
{{COVENANTS_SPR_STEWARD,128,272},{COVENANTS_SPR_NEIGHBOR,64,136},{COVENANTS_SPR_FERRY_KEEPER,400,144},{COVENANTS_SPR_GROWER,344,280}},
{{COVENANTS_SPR_GROWER,160,232},{COVENANTS_SPR_NEIGHBOR,48,200}},
{{COVENANTS_SPR_KILN_KEEPER,360,128},{COVENANTS_SPR_NEIGHBOR,48,72}},
{{COVENANTS_SPR_WALKER,64,128}},
{{COVENANTS_SPR_REPAIRER,136,264},{COVENANTS_SPR_NEIGHBOR,376,112},{COVENANTS_SPR_WATCHER,96,120},{COVENANTS_SPR_SEED_KEEPER,344,280}},
{{COVENANTS_SPR_SEED_KEEPER,160,208}},
{{COVENANTS_SPR_PASSENGER,112,128},{COVENANTS_SPR_FERRY_KEEPER,384,88}},
{{COVENANTS_SPR_WATCHER,144,120},{COVENANTS_SPR_NEIGHBOR,104,112}},
};
static const unsigned char resident_counts[8]={4,2,2,1,4,1,2,2};
typedef struct {short origin[2],target[2][2];unsigned char command,count,face;} PracticeDef;
static const PracticeDef practices[8]={
{{120,160},{{120,146}},12,1,1},
{{48,112},{{48,84},{64,84}},122,2,1},
{{96,104},{{96,112},{96,76}},123,2,1},
{{48,64},{{48,40}},124,1,1},
{{192,112},{{204,100}},125,1,1},
{{120,64},{{120,48}},126,1,1},
{{240,112},{{240,84},{264,84}},127,2,1},
{{120,96},{{120,76}},128,1,1},
};
