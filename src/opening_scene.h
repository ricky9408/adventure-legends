#ifndef EMBER_OPENING_SCENE_H
#define EMBER_OPENING_SCENE_H
/* An ephemeral scene, never serialized. Old saves are already past it. */
#define OPENING_SCENE 14
#define OPENING_SCENE_PAGES 8
#if defined(__arm__)
#define OPENING_CODE __attribute__((section(".text.rom"),long_call,noinline))
#else
#define OPENING_CODE
#endif
extern unsigned char opening_page,opening_clock,opening_armed;
OPENING_CODE void opening_scene_begin(void);
OPENING_CODE void opening_scene_update(void);
OPENING_CODE void opening_scene_render(void);
#endif
