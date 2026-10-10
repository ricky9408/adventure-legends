#ifndef EMBERBOND_MUSIC_H
#define EMBERBOND_MUSIC_H
void music_init(void);
void music_update(unsigned room, unsigned state);
void music_service(void);
unsigned music_theme_for_room(unsigned room);
#endif
