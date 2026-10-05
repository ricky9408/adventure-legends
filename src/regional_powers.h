#ifndef EMBERBOND_REGIONAL_POWERS_H
#define EMBERBOND_REGIONAL_POWERS_H
extern unsigned char slowed_enemies[6];
extern int regional_power_kind,regional_power_time,regional_power_form;
void regional_powers_reset(void);
int regional_power(unsigned command);
void regional_powers_tick(void);
void regional_powers_draw(void);
#endif
