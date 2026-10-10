#ifndef EMBERBOND_COVENANTS_POWER_ART_H
#define EMBERBOND_COVENANTS_POWER_ART_H
/* Transparent zero, unchanged palette. Exact active pixels: |x-3|+|y-3|<=2.
 * Lease uses only existing PIN256 and WATER_DROP64 bytes; zero new OBJ slots. */
extern const unsigned char covenants_power_marks[8][256];
extern const unsigned char covenants_power_particles[8][2][64];
#endif
