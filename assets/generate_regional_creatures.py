#!/usr/bin/env python3
"""Original code-native regional companion art. No external/raster source assets.

Art-only module: does not grant creatures, abilities, collision, or quest access.
All field pixels are authored at native 16x16; portraits separately at 32x32.
Run: python3 assets/generate_regional_creatures.py [--verify]
Only writes assets/regional_creatures and src/regional_creature_art.{h,c}/data.
"""
from pathlib import Path
import argparse
import hashlib
import importlib.util
import io
import json
import shutil
import subprocess
import sys
import tempfile
from PIL import Image, ImageDraw

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'assets/regional_creatures'
SRC = ROOT / 'src'
DIRECTIONS = ('down', 'up', 'left', 'right')
FORM_IDS = (13, 14, 16)
NAMES = ('Dewspindle', 'Tidewheel', 'Chimeclasp')
KEYS = ('dewspindle', 'tidewheel', 'chimeclasp')

def load_base():
    spec = importlib.util.spec_from_file_location('regional_art_base', ROOT / 'assets/generate_assets.py')
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

base = load_base()
Art, P, PAL, RGB = base.Art, base.P, base.PAL, base.rgb
assert base.BASE_PALETTE_SIZE == 97


def mirrored(a):
    a.im = a.im.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
    a.d = ImageDraw.Draw(a.im)
    return a


def dewspindle(direction, frame, ability=None):
    """One spiral water droplet on exactly two reed stilts; no fish outline."""
    a = Art(16, 16, 'transparent')
    lift = (0, 0, -1, 0)[frame] if ability is None else (-1, 0)[ability]
    swing = (0, -1, 0, 1)[frame] if ability is None else (-1, 1)[ability]
    def p(pts, c): a.p([(x, y + lift) for x, y in pts], c)
    def l(pts, c): a.l([(x, y + lift) for x, y in pts], c)
    def dot(x, y, c): a.dot(x, y + lift, c)
    if ability is not None:
        # A low elliptical ring frames the planted stilts rather than the face.
        a.e((1, 11, 14, 15), 'water1')
        a.e((2, 12, 13, 14), 'water4')
        a.e((3, 12, 12, 13), 'transparent')
        a.dot(3 if ability == 0 else 12, 11, 'white')
        a.dot(1 if ability == 0 else 14, 9, 'water3')
    if direction in ('left', 'right'):
        # Near and far legs are offset, leaving the long stilt gait readable.
        for x, tip, y in ((6, 3 + swing, 14 - (frame == 1)), (10, 12 - swing, 13 + (frame == 3))):
            a.l([(x, 9 + lift), (x, 11), (tip, y - 1), (tip, y)], 'water0')
            a.l([(x, 10 + lift), (tip, y - 1)], 'water3')
            a.r((tip - 1, y, tip, y), 'water1')
            a.dot(tip - 1, y - 1, 'water4')
        p([(6, 2), (8, 2), (10, 3), (11, 5), (12, 7), (11, 10), (8, 11), (5, 10), (3, 8), (3, 6), (5, 4)], 'water0')
        p([(6, 3), (8, 3), (10, 5), (11, 7), (10, 9), (8, 10), (5, 9), (4, 7), (5, 5)], 'blue2')
        p([(6, 3), (8, 3), (9, 5), (9, 7), (7, 9), (5, 8), (4, 7), (5, 5)], 'blue3')
        l([(6, 4), (7, 3), (8, 4)], 'watergleam')
        # The coil remains on the cheek behind the profile eye.
        l([(10, 6), (10, 8), (8, 9), (7, 8), (8, 7)], 'water2')
        dot(8, 8, 'water4')
        l([(4, 6), (5, 5), (6, 6), (6, 7), (4, 7)], 'white')
        dot(4, 7, 'ink'); dot(5, 9, 'water0')
        if ability == 1:
            dot(2, 5, 'water4'); dot(1, 4, 'white'); dot(1, 6, 'water2')
        if direction == 'right': mirrored(a)
    else:
        for x, tip, y in ((5, 2 + swing, 14 - (frame == 1)), (10, 13 + swing, 14 - (frame == 3))):
            a.l([(x, 9 + lift), (x - 1 if x == 5 else x + 1, 11), (tip, y - 1), (tip, y)], 'water0')
            a.l([(x, 10 + lift), (tip, y - 1)], 'water3')
            a.dot(tip, y - 1, 'water4')
            a.dot(tip - 1 if x == 5 else tip + 1, y, 'water1')
        # The spiral tip is deliberately asymmetric, unlike the round body.
        p([(7, 1), (10, 2), (9, 3), (10, 4), (12, 7), (11, 10), (9, 11), (6, 11), (4, 9), (3, 7), (5, 4), (6, 3)], 'water0')
        p([(7, 2), (8, 2), (8, 4), (10, 5), (11, 7), (10, 9), (8, 10), (6, 10), (4, 7), (6, 4)], 'blue2')
        p([(7, 3), (8, 4), (9, 5), (9, 7), (8, 9), (6, 9), (4, 7), (6, 4)], 'blue3')
        l([(6, 4), (7, 3), (8, 4)], 'watergleam')
        if direction == 'down':
            l([(5, 6), (6, 6), (6, 7), (5, 7)], 'white')
            l([(9, 6), (10, 6), (10, 7), (9, 7)], 'white')
            dot(6, 7, 'ink'); dot(9, 7, 'ink')
            l([(7, 9), (8, 9)], 'water0')
            dot(10, 8, 'water4'); dot(5, 8, 'water4')
        else:
            # Full back spiral plus a swept crest differentiates the rear view.
            l([(6, 5), (8, 4), (10, 6), (10, 8), (8, 9), (6, 8), (6, 6), (8, 6), (8, 7)], 'water1')
            dot(7, 5, 'watergleam'); dot(7, 7, 'water4')
            dot(4, 4, 'water2'); dot(5, 3, 'water4')
        if ability == 1:
            # Separate beads point in the facing direction, not through eyes.
            if direction == 'down':
                a.dot(7, 14, 'white'); a.dot(8, 15, 'water3')
            else:
                a.dot(3, 1, 'water4'); a.dot(4, 0, 'white')
    return a


def tidewheel(direction, frame, ability=None):
    """Turning water hoop, open reed axle, front droplet face, two spoon feet."""
    a = Art(16, 16, 'transparent')
    lift = (0, 0, -1, 0)[frame] if ability is None else (0, -1)[ability]
    sweep = (0, -1, 0, 1)[frame] if ability is None else (-1, 1)[ability]
    def p(pts, c): a.p([(x, y + lift) for x, y in pts], c)
    def l(pts, c): a.l([(x, y + lift) for x, y in pts], c)
    def e(box, c): a.e((box[0], box[1] + lift, box[2], box[3] + lift), c)
    def dot(x, y, c): a.dot(x, y + lift, c)
    if ability is not None:
        # Linking strand is a sparse, independent hem. It never covers the face.
        a.l([(0, 14), (3, 15), (6, 14), (10, 14), (13, 15), (15, 13)], 'water2')
        a.dot(1 if ability == 0 else 14, 14, 'watergleam')
    # Two separately moving spoon-feet retain the original creature's gait.
    for x, step in ((3, frame == 1), (10, frame == 3)):
        yy = 13 - int(step)
        a.l([(x + 2, 10 + lift), (x + 1 + (sweep if x == 3 else -sweep), yy)], 'water0')
        a.p([(x, yy), (x + 3, yy), (x + 3, yy + 1), (x + 1, yy + 1)], 'water0')
        a.l([(x + 1, yy), (x + 2, yy)], 'water4')
    if direction in ('left', 'right'):
        # Side-on ellipse has a real hole; the face sits in front of its axle.
        p([(9, 1), (12, 2), (14, 5), (14, 8), (12, 11), (9, 11), (7, 9), (7, 4)], 'water0')
        p([(9, 2), (11, 2), (13, 5), (13, 8), (11, 10), (9, 10), (8, 8), (8, 4)], 'water3')
        p([(10, 3), (11, 4), (12, 6), (12, 8), (10, 9), (9, 8), (9, 4)], 'transparent')
        l([(9, 2), (10, 2), (12, 4)], 'watergleam')
        l([(13, 6), (13, 8), (11, 10)], 'blue2')
        l([(10, 6), (12, 6)], 'wood4'); dot(11, 5, 'gold4')
        p([(12, 7), (14, 6 + sweep), (15, 7 + sweep), (14, 9), (12, 10)], 'water0')
        l([(13, 8), (14, 7 + sweep)], 'water4')
        # Forward head is not tucked behind the water wheel.
        p([(5, 4), (7, 5), (8, 7), (9, 9), (8, 11), (5, 12), (2, 10), (1, 8), (3, 7)], 'water0')
        p([(5, 5), (6, 6), (7, 8), (8, 9), (7, 10), (5, 11), (3, 10), (2, 8), (4, 7)], 'blue3')
        p([(6, 7), (8, 9), (7, 10), (5, 11), (4, 10), (6, 9)], 'water3')
        l([(3, 8), (4, 7), (5, 8), (5, 9), (3, 9)], 'white')
        dot(3, 9, 'ink'); dot(3, 10, 'water0'); dot(5, 6, 'watergleam')
        l([(7, 8), (7, 9), (6, 10)], 'water1')
        # Rotating beads change position while both spoon feet remain level.
        for x, y in ((9, 3), (13, 5), (12, 9), (8, 7))[frame:frame+1]: dot(x, y, 'white')
        if ability == 1:
            dot(0, 7, 'water4'); dot(0, 5, 'watergleam')
        if direction == 'right': mirrored(a)
    else:
        cy = 1 if direction == 'down' else 3
        e((3, cy, 12, cy + 10), 'water0')
        e((4, cy + 1, 11, cy + 9), 'water3')
        e((5, cy + 3, 10, cy + 7), 'transparent')
        l([(5, cy + 2), (6, cy + 1), (9, cy + 1)], 'watergleam')
        l([(11, cy + 4), (11, cy + 7), (9, cy + 9)], 'blue2')
        # Manta-like water fins flare sideways from the ring, never over eyes.
        p([(3, 6), (1, 6 + sweep), (0, 8 + sweep), (2, 10), (4, 9)], 'water0')
        p([(12, 6), (14, 6 - sweep), (15, 8 - sweep), (13, 10), (11, 9)], 'water0')
        l([(1, 8 + sweep), (3, 7), (3, 9)], 'water4')
        l([(14, 8 - sweep), (12, 7), (12, 9)], 'water3')
        l([(6, cy + 6), (9, cy + 6)], 'wood4'); dot(6, cy + 5, 'gold4')
        if direction == 'down':
            p([(7, 6), (9, 7), (11, 9), (10, 11), (8, 12), (5, 11), (4, 9), (5, 7)], 'water0')
            p([(7, 7), (9, 8), (10, 9), (9, 11), (6, 11), (5, 9), (6, 8)], 'blue3')
            l([(6, 8), (6, 9)], 'white'); l([(9, 8), (9, 9)], 'white')
            dot(6, 9, 'ink'); dot(9, 9, 'ink'); dot(7, 11, 'water0')
            dot(5, 10, 'water4'); dot(10, 10, 'water4'); dot(7, 7, 'watergleam')
            glints = ((4, 5), (6, 2), (11, 5), (10, 10))
        else:
            # Rear crown sits above the ring, with the family's spiral marking.
            p([(7, 1), (9, 2), (10, 3), (10, 5), (8, 6), (5, 5), (4, 3), (6, 2)], 'water0')
            p([(7, 2), (8, 2), (9, 3), (9, 4), (7, 5), (5, 4), (5, 3)], 'blue3')
            l([(6, 3), (7, 2), (8, 3), (7, 4)], 'water1'); dot(6, 2, 'watergleam')
            glints = ((4, 6), (10, 4), (11, 8), (7, 12))
        dot(*glints[frame], 'white')
        if ability == 1:
            if direction == 'down': a.dot(7, 15, 'white'); a.dot(8, 14, 'water4')
            else: a.dot(2, 1, 'water4'); a.dot(1, 0, 'white')
    return a


def chimeclasp(direction, frame, ability=None):
    """Bronze spring clasp with open crown, two hinged jaws and tuning tongue."""
    a = Art(16, 16, 'transparent')
    lift = (0, 0, -1, 0)[frame] if ability is None else (1, -1)[ability]
    wag = (0, -1, 0, 1)[frame] if ability is None else (0, 1)[ability]
    spread = 1 if ability == 1 else 0
    def p(pts, c): a.p([(x, y + lift) for x, y in pts], c)
    def l(pts, c): a.l([(x, y + lift) for x, y in pts], c)
    def e(box, c): a.e((box[0], box[1] + lift, box[2], box[3] + lift), c)
    def dot(x, y, c): a.dot(x, y + lift, c)
    # Three unequal prongs each articulate, rather than a solid rocky underside.
    for x, y in ((4 + wag, 13 - (frame == 1)), (10 - wag, 13 - (frame == 3)), (8, 14)):
        a.l([(6 if x < 6 else 9, 10 + lift), (x, y - 1), (x, y)], 'wood0')
        a.dot(x, y - 1, 'gold2'); a.dot(x + 1, y, 'gold0')
    if direction in ('left', 'right'):
        # Coiled crown is hollow; the forward clasp reaches past the cheek.
        p([(8, 1), (10, 1), (11, 3), (10, 5), (7, 5), (6, 3)], 'wood0')
        l([(8, 2), (10, 2), (10, 3), (9, 4), (7, 4), (7, 3)], 'silver')
        dot(8, 3, 'transparent'); dot(9, 3, 'transparent'); dot(8, 2, 'white')
        p([(6, 4), (10, 4), (12, 6), (12, 9), (11, 11), (6, 11), (3, 9), (3, 6)], 'wood0')
        p([(6, 5), (10, 5), (11, 6), (11, 9), (10, 10), (6, 10), (4, 8), (4, 6)], 'gold1')
        p([(6, 5), (9, 5), (9, 7), (6, 9), (4, 8), (4, 6)], 'gold3')
        l([(5, 5), (7, 5)], 'gold4'); l([(10, 6), (10, 9)], 'gold0')
        l([(4, 6), (5, 6), (5, 7), (4, 7)], 'white'); dot(4, 7, 'ink')
        # Lower hinged jaw and the suspended silver tuning tongue stay separate.
        p([(3, 7), (2 - spread, 8), (2 - spread, 10), (4, 12), (7, 12), (7, 10), (5, 10), (4, 9)], 'wood0')
        l([(3 - spread, 8), (3 - spread, 10), (5, 11), (6, 11)], 'gold2')
        l([(7, 10), (8, 11), (8, 12)], 'silver'); dot(8, 13, 'white')
        dot(6, 8, 'gold0'); dot(11, 7, 'silver')
        if ability == 1:
            a.l([(0, 7), (1, 6)], 'silver'); a.dot(0, 5, 'gold4')
        if direction == 'right': mirrored(a)
    else:
        # Open silver crown makes a clasp/bell silhouette, unlike stone plates.
        p([(6, 1), (9, 1), (10, 2), (10, 4), (9, 5), (6, 5), (5, 4), (5, 2)], 'wood0')
        l([(6, 2), (9, 2), (9, 4), (6, 4), (6, 2)], 'silver')
        dot(7, 3, 'transparent'); dot(8, 3, 'transparent'); dot(6, 2, 'white')
        p([(5, 4), (10, 4), (12, 6), (12, 9), (10, 11), (5, 11), (3, 9), (3, 6)], 'wood0')
        p([(5, 5), (10, 5), (11, 6), (11, 9), (9, 10), (6, 10), (4, 9), (4, 6)], 'gold1')
        p([(5, 5), (9, 5), (9, 7), (7, 9), (4, 8), (4, 6)], 'gold3')
        l([(5, 5), (8, 5)], 'gold4')
        if direction == 'down':
            l([(5, 6), (6, 6), (6, 7), (5, 7)], 'white')
            l([(9, 6), (10, 6), (10, 7), (9, 7)], 'white')
            dot(6, 7, 'ink'); dot(9, 7, 'ink'); dot(7, 9, 'wood0')
            for x in (3 - spread, 11 + spread):
                p([(x, 7), (x + 1, 7), (x + 1, 10), (x - 1 if x < 7 else x + 2, 11), (x - 1 if x < 7 else x + 2, 9)], 'wood0')
                l([(x, 8), (x, 10)], 'gold2')
            # Silver tongue hangs through an actual dark bell mouth.
            l([(6, 10), (9, 10)], 'wood0'); l([(7, 10), (7 + wag, 12)], 'silver')
            dot(7 + wag, 12, 'white')
        else:
            # Back hinge is a visible pin with staggered jaws, no false front face.
            l([(5, 6), (10, 6)], 'gold0')
            l([(7, 6), (7, 9)], 'silver'); dot(7, 6, 'white')
            l([(5, 8), (6, 9), (9, 9), (10, 8)], 'gold2')
            p([(3, 8), (2 - spread, 9), (3 - spread, 11), (5, 11), (5, 9)], 'wood0')
            p([(11, 8), (13 + spread, 9), (12 + spread, 11), (10, 11), (10, 9)], 'wood0')
            dot(3 - spread, 10, 'gold2'); dot(12 + spread, 10, 'gold2')
            l([(8, 10), (9, 12)], 'silver')
        if ability == 1:
            if direction == 'down':
                a.dot(6, 14, 'silver'); a.dot(7, 15, 'white'); a.dot(9, 14, 'gold3')
            else:
                a.dot(3, 1, 'silver'); a.dot(2, 0, 'white'); a.dot(11, 0, 'gold3')
    return a


def dewspindle_ability(direction, pose): return dewspindle(direction, 0, pose)
def tidewheel_ability(direction, pose): return tidewheel(direction, 0, pose)
def chimeclasp_ability(direction, pose): return chimeclasp(direction, 0, pose)


def portrait_dewspindle():
    a = Art(32, 32, 'transparent')
    # The broader droplet gives the portrait a clear transparent spiral cheek.
    for pts in ([(11, 19), (8, 23), (4, 27), (3, 29)], [(21, 19), (23, 23), (27, 26), (28, 29)]):
        a.l(pts, 'water0', 2); a.l([(x, y - 1) for x, y in pts], 'water3')
    a.l([(2, 29), (5, 29)], 'water1'); a.l([(26, 29), (30, 29)], 'water1')
    a.dot(3, 28, 'watergleam'); a.dot(28, 28, 'watergleam')
    a.p([(15, 2), (19, 3), (20, 5), (18, 7), (22, 9), (25, 13), (25, 17), (22, 21), (17, 23), (11, 22), (7, 19), (5, 15), (7, 11), (11, 7), (12, 4)], 'water0')
    a.p([(15, 3), (18, 4), (18, 5), (16, 7), (21, 10), (24, 14), (24, 17), (21, 20), (17, 22), (12, 21), (8, 18), (6, 15), (8, 11), (12, 7), (13, 4)], 'blue2')
    a.p([(14, 4), (17, 4), (15, 8), (19, 10), (21, 14), (20, 18), (16, 21), (12, 20), (8, 17), (7, 14), (10, 10), (13, 7)], 'blue3')
    a.p([(12, 8), (15, 7), (15, 9), (11, 13), (9, 15), (8, 13)], 'watergleam')
    a.l([(21, 10), (23, 13), (23, 17), (21, 19), (18, 20), (16, 19), (16, 17), (18, 16), (20, 17), (19, 18)], 'water1')
    a.l([(22, 12), (22, 16), (21, 17)], 'water4')
    # Tall eyes are readable at 1x, with pupils biased toward the player.
    for x, y in ((10, 12), (18, 11)):
        a.e((x - 1, y, x + 2, y + 5), 'water0'); a.e((x, y, x + 2, y + 4), 'white')
        a.r((x + 1, y + 2, x + 2, y + 4), 'ink'); a.dot(x + 1, y + 1, 'white')
    a.l([(13, 18), (14, 19), (15, 18)], 'water0')
    a.dot(9, 17, 'water4'); a.dot(21, 16, 'watergleam')
    a.l([(2, 25), (4, 24), (6, 25)], 'water3'); a.l([(26, 24), (29, 25), (30, 26)], 'water3')
    a.dot(3, 23, 'watergleam')
    return a


def portrait_tidewheel():
    a = Art(32, 32, 'transparent')
    # An open water hoop behind the smiling droplet, never across its face.
    a.e((6, 1, 27, 24), 'water0'); a.e((7, 2, 26, 23), 'water3')
    a.e((10, 6, 23, 20), 'water0'); a.e((11, 7, 22, 19), 'transparent')
    a.l([(9, 6), (11, 4), (15, 3), (19, 3), (23, 5)], 'watergleam', 2)
    a.l([(25, 9), (25, 16), (23, 20), (20, 22)], 'blue2', 2)
    a.l([(9, 10), (9, 15), (11, 19)], 'blue3')
    a.p([(8, 14), (4, 13), (2, 15), (0, 19), (4, 23), (10, 23)], 'water0')
    a.p([(8, 15), (4, 14), (2, 17), (2, 19), (5, 21), (9, 21)], 'blue3')
    a.l([(2, 18), (5, 16), (7, 17)], 'watergleam')
    a.p([(25, 13), (28, 12), (31, 14), (30, 20), (26, 22), (23, 21)], 'water0')
    a.p([(26, 14), (28, 13), (30, 15), (29, 18), (25, 20)], 'water3')
    a.l([(27, 14), (29, 14)], 'water4')
    # Reed axle remains hollow, with a clearly outlined open end.
    a.r((13, 12, 24, 14), 'wood0'); a.r((13, 12, 23, 13), 'wood4')
    a.r((22, 11, 25, 15), 'gold0'); a.r((23, 12, 24, 14), 'water0'); a.dot(23, 11, 'gold4')
    for pts in ([(11, 22), (9, 26), (7, 28)], [(21, 22), (22, 25), (24, 28)]):
        a.l(pts, 'water0', 2); a.l(pts, 'water3')
    for x in (4, 22):
        a.p([(x, 28), (x + 4, 27), (x + 6, 28), (x + 5, 30), (x + 1, 30)], 'water0')
        a.l([(x + 1, 28), (x + 4, 28)], 'water4')
    a.p([(14, 12), (17, 13), (19, 15), (22, 17), (23, 20), (21, 24), (17, 26), (11, 25), (8, 22), (7, 19), (10, 15), (12, 14)], 'water0')
    a.p([(14, 13), (16, 14), (18, 16), (21, 18), (22, 20), (20, 23), (17, 25), (12, 24), (9, 21), (8, 19), (11, 16)], 'blue3')
    a.p([(19, 17), (22, 20), (20, 23), (17, 25), (13, 24), (17, 22), (19, 20)], 'water3')
    a.l([(11, 17), (14, 14), (15, 15)], 'watergleam')
    for x in (11, 18):
        a.e((x, 17, x + 3, 21), 'white'); a.r((x + 1, 19, x + 2, 21), 'ink'); a.dot(x + 1, 18, 'white')
    a.l([(14, 23), (15, 24), (17, 23)], 'water0')
    a.dot(10, 22, 'water4'); a.dot(21, 22, 'watergleam'); a.dot(25, 7, 'white')
    return a


def portrait_chimeclasp():
    a = Art(32, 32, 'transparent')
    # Three unequal mechanical prongs, slender and visibly jointed.
    for pts in ([(11, 22), (9, 25), (5, 27), (5, 29)], [(20, 21), (24, 25), (25, 28)], [(16, 23), (17, 27), (16, 30)]):
        a.l(pts, 'wood0', 3); a.l(pts, 'gold1'); a.dot(*pts[-1], 'gold3')
    a.l([(4, 29), (7, 29)], 'gold0'); a.l([(24, 28), (28, 28)], 'gold0')
    # Open spring loop, silver and bronze with a tiny cast seam.
    a.p([(12, 1), (18, 1), (21, 4), (21, 8), (18, 11), (12, 10), (9, 7), (9, 4)], 'wood0')
    a.l([(12, 3), (17, 2), (19, 4), (19, 7), (17, 9), (13, 8), (11, 6), (11, 4), (12, 3)], 'silver', 2)
    a.l([(12, 3), (17, 3)], 'white'); a.dot(19, 5, 'gold3')
    a.p([(10, 8), (21, 8), (24, 11), (25, 16), (23, 21), (19, 24), (12, 24), (7, 21), (5, 16), (6, 12)], 'wood0')
    a.p([(10, 9), (20, 9), (23, 12), (24, 16), (22, 20), (19, 22), (12, 23), (8, 20), (6, 16), (7, 12)], 'gold1')
    a.p([(10, 9), (17, 9), (20, 12), (19, 17), (15, 20), (10, 20), (7, 17), (7, 13)], 'gold2')
    a.p([(10, 10), (16, 10), (17, 12), (15, 14), (9, 16), (8, 14)], 'gold3')
    a.l([(10, 10), (15, 10)], 'gold4'); a.l([(22, 13), (22, 18), (20, 20)], 'gold0')
    for x in (10, 18):
        a.e((x - 1, 13, x + 3, 18), 'wood0'); a.e((x, 13, x + 3, 17), 'white')
        a.r((x + 1, 15, x + 2, 17), 'ink'); a.dot(x + 1, 14, 'white')
    a.l([(14, 19), (15, 20), (17, 19)], 'wood0')
    # Curled bronze clasp jaws surround the tongue without blocking expression.
    a.p([(6, 15), (4, 15), (3, 19), (5, 23), (9, 25), (12, 24), (11, 21), (8, 21), (7, 19)], 'wood0')
    a.l([(5, 16), (5, 19), (7, 22), (10, 23)], 'gold2', 2)
    a.l([(4, 18), (5, 20)], 'gold4')
    a.p([(25, 14), (27, 15), (28, 19), (26, 23), (22, 25), (20, 23), (23, 20), (24, 17)], 'wood0')
    a.l([(26, 16), (26, 19), (24, 22), (22, 23)], 'gold1', 2)
    a.dot(26, 16, 'silver')
    a.r((13, 22, 19, 23), 'wood0'); a.l([(16, 22), (16, 25), (17, 26)], 'stone2', 2)
    a.p([(16, 25), (19, 26), (18, 28), (15, 27)], 'silver'); a.dot(16, 25, 'white')
    return a


FIELD_FUNCTIONS = (dewspindle, tidewheel, chimeclasp)
ABILITY_FUNCTIONS = (dewspindle_ability, tidewheel_ability, chimeclasp_ability)
PORTRAIT_FUNCTIONS = (portrait_dewspindle, portrait_tidewheel, portrait_chimeclasp)


def mask(im):
    return Image.frombytes('L', im.size, bytes(255 if n else 0 for n in im.tobytes()))


def paste(target, sprite, xy):
    im = sprite if isinstance(sprite, Image.Image) else sprite.im
    target.paste(im.convert(target.mode), xy, mask(im))


def save_indexed(im, path):
    im.save(path, transparency=0, optimize=False)


def make_previews(fields, abilities, portraits):
    walks = Image.new('P', (192, 64), 0); walks.putpalette(PAL)
    acts = Image.new('P', (96, 64), 0); acts.putpalette(PAL)
    for i in range(3):
        single = Image.new('P', (64, 64), 0); single.putpalette(PAL)
        actions = Image.new('P', (32, 64), 0); actions.putpalette(PAL)
        for d in range(4):
            for f in range(4): single.paste(fields[i][d][f].im, (f * 16, d * 16))
            for f in range(2): actions.paste(abilities[i][d][f].im, (f * 16, d * 16))
        walks.paste(single, (i * 64, 0)); acts.paste(actions, (i * 32, 0))
        save_indexed(single, OUT / f'{KEYS[i]}_walk.png')
        save_indexed(actions, OUT / f'{KEYS[i]}_ability.png')
        save_indexed(portraits[i].im, OUT / f'{KEYS[i]}_portrait.png')
    save_indexed(walks, OUT / 'walk_sheet.png'); save_indexed(acts, OUT / 'ability_sheet.png')
    # This is the primary 1x review: actual 16px cells and 32px portraits, twice.
    native = Image.new('RGB', (432, 222), RGB[P['night']]); nd = ImageDraw.Draw(native)
    nd.text((8, 5), 'ORIGINAL COMPANION ART / NATIVE PIXELS', fill=RGB[P['white']])
    for bg, yy, fg in (('deep', 27, 'white'), ('dirt4', 124, 'ink')):
        nd.rectangle((0, yy, 431, yy + 90), fill=RGB[P[bg]])
        for i in range(3):
            x = i * 144
            nd.text((x + 4, yy + 3), NAMES[i], fill=RGB[P[fg]])
            for d in range(4):
                for f in range(4): paste(native, fields[i][d][f], (x + 3 + f * 16, yy + 20 + d * 16))
                for f in range(2): paste(native, abilities[i][d][f], (x + 71 + f * 16, yy + 20 + d * 16))
            paste(native, portraits[i], (x + 108, yy + 23))
    native.save(OUT / 'native_dark_light.png')
    native.resize((1296, 666), Image.Resampling.NEAREST).save(OUT / 'native_dark_light_3x.png')
    # A larger, separate portrait review does not replace the native-size sheet.
    contact = Image.new('RGB', (720, 368), RGB[P['deep']]); cd = ImageDraw.Draw(contact)
    cd.text((12, 9), 'ART ONLY / 48 WALK POSES + 24 ABILITY POSES + 3 PORTRAITS', fill=RGB[P['white']])
    for i in range(3):
        x = i * 240
        cd.text((x + 12, 29), f'{FORM_IDS[i]:02d}  {NAMES[i]}', fill=RGB[P['gold3']])
        paste(contact, portraits[i].im.resize((96, 96), Image.Resampling.NEAREST), (x + 72, 49))
        cd.text((x + 9, 153), 'D / U / L / R; walk x4, ability x2', fill=RGB[P['silver']])
        for d in range(4):
            for f, sp in enumerate(fields[i][d] + abilities[i][d]):
                paste(contact, sp.im.resize((32, 32), Image.Resampling.NEAREST), (x + 20 + f * 33, 178 + d * 40))
        cd.text((x + 14, 345), 'Native 16x16 / portrait 32x32', fill=RGB[P['silver']])
    contact.save(OUT / 'contact_sheet.png')
    sil = Image.new('RGB', (288, 166), RGB[P['dirt4']]); sd = ImageDraw.Draw(sil)
    for i in range(3):
        sd.text((i * 96 + 3, 5), NAMES[i], fill=RGB[P['ink']])
        for d in range(4):
            flat = Image.new('RGB', (16, 16), RGB[P['ink']])
            sil.paste(flat.resize((32, 32), Image.Resampling.NEAREST), (i * 96 + 32, 26 + d * 34), mask(fields[i][d][0].im).resize((32, 32), Image.Resampling.NEAREST))
    sil.save(OUT / 'directional_silhouettes.png')
    animation = []
    for f in range(4):
        im = Image.new('RGB', (288, 118), RGB[P['dirt4']]); ad = ImageDraw.Draw(im)
        ad.text((5, 5), 'ART ONLY / WALK CYCLE AT NATIVE PIXELS', fill=RGB[P['ink']])
        for i in range(3):
            ad.text((i * 96 + 4, 25), NAMES[i], fill=RGB[P['ink']])
            for d in range(4): paste(im, fields[i][d][f], (i * 96 + d * 22 + 6, 45))
            for d in range(4): paste(im, abilities[i][d][f % 2], (i * 96 + d * 22 + 6, 82))
        animation.append(im)
    animation[0].save(OUT / 'motion_native.gif', save_all=True, append_images=animation[1:], duration=140, loop=0, disposal=2, optimize=False)


def emit_code(fields, abilities, portraits):
    header = '''/* Generated original art; edit assets/generate_regional_creatures.py. */
#ifndef EMBERBOND_REGIONAL_CREATURE_ART_H
#define EMBERBOND_REGIONAL_CREATURE_ART_H
#define REGIONAL_CREATURE_ART_COUNT 3
#define REGIONAL_CREATURE_ART_FRAME_BYTES 256
#define REGIONAL_CREATURE_ART_PORTRAIT_BYTES 1024
#define REGIONAL_CREATURE_ART_DIRECTION_COUNT 4
#define REGIONAL_CREATURE_ART_WALK_FRAME_COUNT 4
#define REGIONAL_CREATURE_ART_ABILITY_FRAME_COUNT 2
enum { REGIONAL_CREATURE_DEWSPINDLE, REGIONAL_CREATURE_TIDEWHEEL, REGIONAL_CREATURE_CHIMECLASP };
/* Stable form IDs 13,14,16. Directions down/up/left/right. Walk cycle 0..3;
 * ability 0 gathers/coils, 1 releases. Art only, no gameplay unlocks.
 * Native row-major 8bpp indices into game_palette; zero is transparent.
 * 16x16 field anchor (8,8); 32x32 portrait blits at top-left.
 * Immutable ROM data, no new palette, runtime buffers, data or BSS.
 */
extern const unsigned char regional_creature_form_ids[REGIONAL_CREATURE_ART_COUNT];
extern const unsigned char regional_creature_direction_frames[REGIONAL_CREATURE_ART_COUNT][4][4][REGIONAL_CREATURE_ART_FRAME_BYTES];
extern const unsigned char regional_creature_ability_frames[REGIONAL_CREATURE_ART_COUNT][4][2][REGIONAL_CREATURE_ART_FRAME_BYTES];
extern const unsigned char regional_creature_portraits[REGIONAL_CREATURE_ART_COUNT][REGIONAL_CREATURE_ART_PORTRAIT_BYTES];
/* Fail closed: unsupported stable IDs return -1/NULL. Out-of-range direction,
 * walk frame or ability pose also returns NULL; there is no implicit fallback.
 */
int regional_creature_art_index(unsigned int form_id);
const unsigned char *regional_creature_art_frame(unsigned int form_id, unsigned int direction, unsigned int frame);
const unsigned char *regional_creature_art_ability_frame(unsigned int form_id, unsigned int direction, unsigned int pose);
const unsigned char *regional_creature_art_portrait(unsigned int form_id);
#endif
'''
    (SRC / 'regional_creature_art.h').write_text(header)
    f = io.StringIO(); f.write('const unsigned char regional_creature_form_ids[3] = {13,14,16};\n\n')
    base.emit_image_tensor(f, 'regional_creature_direction_frames', fields, [3, 4, 4, 256])
    base.emit_image_tensor(f, 'regional_creature_ability_frames', abilities, [3, 4, 2, 256])
    base.emit_image_tensor(f, 'regional_creature_portraits', portraits, [3, 1024])
    chunks = []; current = []; size = 0
    for line in f.getvalue().splitlines(keepends=True):
        n = len(line.encode())
        if current and size + n > 32000: chunks.append(''.join(current)); current = []; size = 0
        current.append(line); size += n
    if current: chunks.append(''.join(current))
    folder = SRC / 'regional_creature_art_data'; folder.mkdir(exist_ok=True)
    for old in folder.glob('part_*.inc'): old.unlink()
    for i, chunk in enumerate(chunks): (folder / f'part_{i:03d}.inc').write_text(chunk)
    code = '#include "regional_creature_art.h"\n/* Generated by assets/generate_regional_creatures.py. */\n'
    code += ''.join(f'#include "regional_creature_art_data/part_{i:03d}.inc"\n' for i in range(len(chunks)))
    code += '''
int regional_creature_art_index(unsigned int form_id) {
    switch (form_id) {
    case 13: return REGIONAL_CREATURE_DEWSPINDLE;
    case 14: return REGIONAL_CREATURE_TIDEWHEEL;
    case 16: return REGIONAL_CREATURE_CHIMECLASP;
    default: return -1;
    }
}
const unsigned char *regional_creature_art_frame(unsigned int form_id, unsigned int direction, unsigned int frame) {
    int i = regional_creature_art_index(form_id);
    if (i < 0 || direction >= 4 || frame >= 4) return (const unsigned char *)0;
    return regional_creature_direction_frames[i][direction][frame];
}
const unsigned char *regional_creature_art_ability_frame(unsigned int form_id, unsigned int direction, unsigned int pose) {
    int i = regional_creature_art_index(form_id);
    if (i < 0 || direction >= 4 || pose >= 2) return (const unsigned char *)0;
    return regional_creature_ability_frames[i][direction][pose];
}
const unsigned char *regional_creature_art_portrait(unsigned int form_id) {
    int i = regional_creature_art_index(form_id);
    return i < 0 ? (const unsigned char *)0 : regional_creature_portraits[i];
}
'''
    (SRC / 'regional_creature_art.c').write_text(code)
    return [len(c.encode()) for c in chunks]


def validate_pixels(fields, abilities, portraits):
    all_images = [s for rows in fields + abilities for row in rows for s in row] + portraits
    for sp in all_images:
        im = sp.im; data = im.tobytes()
        assert im.mode == 'P' and im.getpalette() == PAL
        assert 0 in data and max(data) < base.BASE_PALETTE_SIZE
        assert im.size in ((16, 16), (32, 32))
        assert im.getpixel((0, 0)) == 0 and im.getpixel((im.width - 1, 0)) == 0
    for i, rows in enumerate(fields):
        for d, row in enumerate(rows):
            assert len({s.im.tobytes() for s in row}) == 4, (KEYS[i], DIRECTIONS[d], 'walk pixels')
            assert len({mask(s.im).tobytes() for s in row}) >= 3, (KEYS[i], DIRECTIONS[d], 'walk silhouettes')
            action = abilities[i][d]
            assert len({s.im.tobytes() for s in row + action}) == 6, (KEYS[i], DIRECTIONS[d], 'ability pixels')
            assert len({mask(s.im).tobytes() for s in action}) == 2
            assert all(55 <= sum(bool(n) for n in s.im.tobytes()) <= 220 for s in row + action)
        assert len({rows[d][0].im.tobytes() for d in range(4)}) == 4
        assert len({mask(rows[d][0].im).tobytes() for d in range(4)}) == 4, (KEYS[i], 'direction silhouettes')
        assert portraits[i].im.size == (32, 32)
        assert portraits[i].im.tobytes() != rows[0][0].im.resize((32, 32), Image.Resampling.NEAREST).tobytes()
    # All three front silhouettes differ without relying on palette recoloring.
    assert len({mask(rows[0][0].im).tobytes() for rows in fields}) == 3
    # A hoop aperture must remain physically transparent in every Tidewheel view.
    for d in range(4):
        for row in (fields[1][d], abilities[1][d]):
            for sp in row:
                if d == 0: points = [(x, y) for x in range(6, 10) for y in range(3, 6)]
                elif d == 1: points = [(x, y) for x in range(6, 10) for y in range(7, 10)]
                else: points = [(x, y) for x in (9, 10, 11) for y in (3, 4, 5)] if d == 2 else [(x, y) for x in (4, 5, 6) for y in (3, 4, 5)]
                assert sum(sp.im.getpixel(pt) == 0 for pt in points) >= 2, ('Tidewheel aperture', d)
    return {'field_dimensions': [3, 4, 4, 256], 'ability_dimensions': [3, 4, 2, 256],
            'portrait_dimensions': [3, 1024], 'existing_actor_palette_only': True,
            'palette_indices': sorted({n for s in all_images for n in s.im.tobytes()}),
            'transparent_zero': True, 'four_distinct_walk_frames_per_direction': True,
            'articulated_walk_silhouettes': True, 'four_distinct_direction_silhouettes': True,
            'two_additional_distinct_ability_poses': True, 'three_distinct_form_silhouettes': True,
            'tidewheel_apertures_clear': True, 'independent_portraits': True}


def output_hashes():
    files = sorted(p for p in OUT.iterdir() if p.is_file() and p.name != 'validation.json')
    files += sorted((SRC / 'regional_creature_art_data').glob('*.inc'))
    files += [SRC / 'regional_creature_art.c', SRC / 'regional_creature_art.h']
    return {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in files}


def generate():
    OUT.mkdir(parents=True, exist_ok=True)
    fields = [[[fn(d, f) for f in range(4)] for d in DIRECTIONS] for fn in FIELD_FUNCTIONS]
    abilities = [[[fn(d, f) for f in range(2)] for d in DIRECTIONS] for fn in ABILITY_FUNCTIONS]
    portraits = [fn() for fn in PORTRAIT_FUNCTIONS]
    validation = validate_pixels(fields, abilities, portraits)
    chunks = emit_code(fields, abilities, portraits)
    make_previews(fields, abilities, portraits)
    manifest = {'schema_version': 1, 'generator': 'assets/generate_regional_creatures.py',
                'names': list(NAMES), 'form_ids': list(FORM_IDS), 'directions': list(DIRECTIONS),
                'rights': 'Original code-native pixel art. No external art, extracted game assets, traced characters, or raster inputs.',
                'status': 'ART ONLY / DEVELOPER REVIEW. Acquisition, runtime rendering and ability behavior are separate engine work. Keep companion sheets out of player-facing media.',
                'palette_sha256': hashlib.sha256(json.dumps(base.COLORS).encode()).hexdigest(),
                'data_bytes': 21507, 'runtime_data_bytes': 0, 'runtime_bss_bytes': 0,
                'include_bytes': chunks, 'max_include_bytes': max(chunks), 'anchor': [8, 8],
                'frame_ticks_suggestion': 8, 'ability_poses': ['gather_or_coil', 'release'],
                'motions': ['Two reed stilts alternate under a soft spiral droplet',
                            'Water hoop turns above level spoon feet; droplet face stays forward',
                            'Three unequal prongs step; suspended tuning tongue sways inside bronze jaws'],
                'validation': validation}
    (OUT / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    (OUT / 'CREDITS.txt').write_text(manifest['rights'] + '\nAuthored at native size with deterministic Python/Pillow geometry.\nExisting RGB555 game_palette reused verbatim; no extra palette.\nArt previews are not emulator screenshots or evidence of playable acquisition.\nDeveloper review only. Keep future companion sheets out of player-facing media.\n')
    return manifest


def verify(manifest):
    before = output_hashes(); generate(); after = output_hashes()
    assert before == after, 'Regeneration must be byte-identical'
    report = {'pixel_validation': manifest['validation'], 'deterministic_regeneration': True,
              'output_sha256': after, 'max_include_bytes': manifest['max_include_bytes']}
    host_test = '''#include "regional_creature_art.h"
#include <assert.h>
int main(void) {
 unsigned int id,i,d,f,k;
 assert(sizeof regional_creature_form_ids==3);
 assert(sizeof regional_creature_direction_frames==12288);
 assert(sizeof regional_creature_ability_frames==6144);
 assert(sizeof regional_creature_portraits==3072);
 for(id=0;id<65536;id++) {
  int expected=(id==13?0:id==14?1:id==16?2:-1);
  assert(regional_creature_art_index(id)==expected);
  assert((regional_creature_art_portrait(id)!=0)==(expected>=0));
  assert((regional_creature_art_frame(id,0,0)!=0)==(expected>=0));
  assert((regional_creature_art_ability_frame(id,0,0)!=0)==(expected>=0));
 }
 assert(regional_creature_art_index(~0u)==-1);
 assert(!regional_creature_art_frame(~0u,0,0));
 assert(!regional_creature_art_portrait(~0u));
 assert(!regional_creature_art_ability_frame(~0u,0,0));
 for(i=0;i<3;i++) {
  id=regional_creature_form_ids[i];
  assert(regional_creature_art_portrait(id)==regional_creature_portraits[i]);
  for(k=0;k<1024;k++) assert(regional_creature_art_portrait(id)[k]<=96);
  for(d=0;d<4;d++) {
   for(f=0;f<4;f++) {
    const unsigned char *p=regional_creature_art_frame(id,d,f);
    assert(p==regional_creature_direction_frames[i][d][f]);
    for(k=0;k<256;k++) assert(p[k]<=96);
   }
   for(f=0;f<2;f++) {
    const unsigned char *p=regional_creature_art_ability_frame(id,d,f);
    assert(p==regional_creature_ability_frames[i][d][f]);
    for(k=0;k<256;k++) assert(p[k]<=96);
   }
  }
  assert(!regional_creature_art_frame(id,4,0));
  assert(!regional_creature_art_frame(id,0,4));
  assert(!regional_creature_art_frame(id,~0u,~0u));
  assert(!regional_creature_art_ability_frame(id,4,0));
  assert(!regional_creature_art_ability_frame(id,0,2));
  assert(!regional_creature_art_ability_frame(id,~0u,~0u));
 }
 return 0;
}
'''
    with tempfile.TemporaryDirectory(prefix='regional-creature-art-') as td:
        td = Path(td); (td / 'test.c').write_text(host_test)
        subprocess.run(['gcc', '-std=c99', '-O2', '-Wall', '-Wextra', '-Werror', '-pedantic', '-I', str(SRC), str(td / 'test.c'), str(SRC / 'regional_creature_art.c'), '-o', str(td / 'test')], check=True, capture_output=True)
        subprocess.run([str(td / 'test')], check=True, capture_output=True)
        report['host_compile_and_lookup_tests'] = 'passed'
        arm = ROOT / 'tools/sysroot/usr/bin/arm-none-eabi-gcc'
        if not arm.exists():
            fallback = shutil.which('arm-none-eabi-gcc')
            if not fallback: raise RuntimeError('ARM toolchain missing; target compile not verified')
            arm = Path(fallback)
        obj = td / 'regional_creature_art.o'
        subprocess.run([str(arm), '-std=c99', '-mcpu=arm7tdmi', '-mthumb', '-O2', '-ffreestanding', '-fno-builtin', '-Wall', '-Wextra', '-Werror', '-c', str(SRC / 'regional_creature_art.c'), '-o', str(obj)], check=True, capture_output=True)
        size = subprocess.run([str(arm).replace('gcc', 'size'), str(obj)], check=True, capture_output=True, text=True).stdout
        sections = list(map(int, size.splitlines()[-1].split()[:3]))
        assert sections[1:] == [0, 0], size
        assert sections[0] <= 22528, size
        report.update({'arm_compile': 'passed', 'arm_rom_object_bytes': sections[0],
                       'arm_data_bytes': sections[1], 'arm_bss_bytes': sections[2],
                       'arm_size_output': size.strip().replace(str(obj), 'regional_creature_art.o')})
    (OUT / 'validation.json').write_text(json.dumps(report, indent=2) + '\n')
    return {k: v for k, v in report.items() if k not in ('output_sha256', 'pixel_validation')}


def main():
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument('--verify', action='store_true'); args = parser.parse_args()
    manifest = generate()
    print(json.dumps(verify(manifest) if args.verify else {'generated_forms': FORM_IDS, 'data_bytes': manifest['data_bytes'], 'max_include_bytes': manifest['max_include_bytes']}, indent=2))

if __name__ == '__main__': main()
