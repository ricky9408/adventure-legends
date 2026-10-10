#!/usr/bin/env python3
"""Original small cast glyphs and exact 13-pixel effect stamps."""
from pathlib import Path
import json
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'assets/covenants_powers'
OUT.mkdir(exist_ok=True)
# Existing actor palette: water3, pine5, fire2, silver, silver, pine4,
# water2, fire1. The darker final fire edge stays visible on cream ground.
colors = [55, 13, 50, 6, 6, 12, 54, 49]
lights = [96, 14, 51, 7, 7, 14, 96, 51]
paths = [
    [[(3, 5), (5, 2), (8, 2)], [(12, 3), (14, 7), (12, 10)], [(9, 13), (4, 12), (2, 9)]],
    [[(4, 13), (4, 4), (12, 4)], [(2, 6), (4, 4), (6, 6)]],
    [[(4, 12), (2, 7), (5, 3), (11, 3), (14, 7), (11, 12), (7, 11), (6, 7), (9, 6)]],
    [[(2, 8), (8, 2), (14, 8), (8, 14), (2, 8)], [(5, 9), (5, 7)], [(8, 10), (8, 5)], [(11, 9), (11, 7)]],
    [[(3, 3), (12, 8), (3, 13)], [(7, 3), (14, 8), (7, 13)]],
    [[(3, 12), (3, 3), (12, 3), (12, 12)]],
    [[(3, 13), (3, 4), (12, 4), (12, 10), (8, 10)]],
    [[(3, 12), (3, 3), (12, 3), (12, 12)], [(6, 10), (8, 7), (10, 10)]],
]
marks = []
particles = []
sheet = Image.new('RGB', (8 * 48, 80), '#172637')
palette = json.loads((ROOT / 'assets/covenants_creatures/source/reference/palette.json').read_text())['rgb']
for index, color in enumerate(colors):
    glyph = Image.new('P', (16, 16), 0)
    draw = ImageDraw.Draw(glyph)
    for path in paths[index]:
        draw.line(path, fill=color)
    glyph.putpalette([c for rgb in palette for c in rgb])
    marks.append(list(glyph.tobytes()))
    row = []
    for live in range(2):
        pixels = [color if abs(x-3)+abs(y-3) <= 2 else 0 for y in range(8) for x in range(8)]
        if live:
            pixels[27] = lights[index]
        row.append(pixels)
    particles.append(row)
    sheet.paste(glyph.convert('RGB').resize((48, 48), Image.Resampling.NEAREST), (48*index, 0))
sheet.save(OUT / 'glyphs_3x.png')
header = '''#ifndef EMBERBOND_COVENANTS_POWER_ART_H
#define EMBERBOND_COVENANTS_POWER_ART_H
/* Transparent zero, unchanged palette. Exact active pixels: |x-3|+|y-3|<=2.
 * Lease uses only existing PIN256 and WATER_DROP64 bytes; zero new OBJ slots. */
extern const unsigned char covenants_power_marks[8][256];
extern const unsigned char covenants_power_particles[8][2][64];
#endif
'''
(ROOT / 'src/covenants_power_art.h').write_text(header)
def array(value):
    return '{' + ','.join(array(x) if isinstance(x, list) else str(x) for x in value) + '}'
source = '#include "covenants_power_art.h"\n'
source += 'const unsigned char covenants_power_marks[8][256]=' + array(marks) + ';\n'
source += 'const unsigned char covenants_power_particles[8][2][64]=' + array(particles) + ';\n'
(ROOT / 'src/covenants_power_art.c').write_text(source)
(OUT / 'manifest.json').write_text(json.dumps({'commands': [12] + list(range(122, 129)),
    'bytes': 3072, 'stamp_native_pixels': 13, 'new_palette_colors': 0,
    'base_palette_indices': colors, 'highlight_palette_indices': lights,
    'logical_effect_parts_max': 3, 'world_stamp_draw_cap': 24,
    'scope': 'native indexed assets; full ROM performance and controller review pending'}, indent=2) + '\n')
