#ifndef EMBER_OPENING_SCENE_DATA_H
#define EMBER_OPENING_SCENE_DATA_H
#include "ui.h"
enum {
 OS_TITLE,
 OS_CONTROLS,
 OS_SPEAKER0,
 OS_LINE0_0,
 OS_LINE0_1,
 OS_SPEAKER1,
 OS_LINE1_0,
 OS_LINE1_1,
 OS_SPEAKER2,
 OS_LINE2_0,
 OS_LINE2_1,
 OS_SPEAKER3,
 OS_LINE3_0,
 OS_LINE3_1,
 OS_SPEAKER4,
 OS_LINE4_0,
 OS_LINE4_1,
 OS_SPEAKER5,
 OS_LINE5_0,
 OS_LINE5_1,
 OS_SPEAKER6,
 OS_LINE6_0,
 OS_LINE6_1,
 OS_SPEAKER7,
 OS_LINE7_0,
 OS_LINE7_1,
 OS_TEXT_COUNT };
extern const UiText opening_scene_texts[OS_TEXT_COUNT];
extern const unsigned char opening_lantern[3][384];
extern const unsigned char opening_chore_props[32*16];
#endif
