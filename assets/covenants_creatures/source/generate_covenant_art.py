#!/usr/bin/env python3
"""Original, isolated code-native Covenant pixel art. Never writes a game tree.

Run with Python 3 + Pillow. Every output stays beside this file. Palette and
comparison masks are frozen read-only inputs; no external artwork is loaded.
"""
from pathlib import Path
import argparse, hashlib, json, re, subprocess, sys
from PIL import Image, ImageDraw
sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'previews'
GEN = ROOT / 'generated'
PALETTE = json.loads((ROOT / 'reference/palette.json').read_text())
P = PALETTE['indices']
RGB = [tuple(c) for c in PALETTE['rgb']]
PAL = [v for rgb in RGB for v in rgb]
ROSTER = json.loads((ROOT / 'reference/legendary-roster.json').read_text())['forms']
IDS = tuple(range(121, 129))
DIRS = ('down', 'up', 'left', 'right')
WALK_TICKS = ((8, 6, 9, 7), (7, 6, 8, 6), (12, 9, 12, 10), (11, 9, 12, 9),
              (8, 6, 9, 7), (10, 8, 11, 9), (8, 8, 5, 7), (10, 8, 11, 8))
CAST_TICKS = ((10, 18, 12), (9, 14, 11), (18, 8, 12), (14, 12, 14),
              (10, 15, 12), (12, 14, 13), (10, 9, 12), (15, 18, 14))


class Pen:
    def __init__(self, size=16):
        self.im = Image.new('P', (size, size), 0)
        self.im.putpalette(PAL)
        self.draw = ImageDraw.Draw(self.im)

    def check(self, pts):
        assert all(0 <= x < self.im.width and 0 <= y < self.im.height for x, y in pts), pts

    def l(self, pts, c, w=1):
        self.check(pts)
        self.draw.line(pts, fill=P[c], width=w)

    def p(self, pts, c):
        self.check(pts)
        self.draw.polygon(pts, fill=P[c])

    def e(self, box, c):
        self.check((box[:2], box[2:]))
        self.draw.ellipse(box, fill=P[c])

    def r(self, box, c):
        self.check((box[:2], box[2:]))
        self.draw.rectangle(box, fill=P[c])

    def dot(self, x, y, c):
        self.check(((x, y),))
        self.im.putpixel((x, y), P[c])


def eye(a, x, y):
    a.dot(x, y, 'white')
    a.dot(x, y + 1, 'ink')


def leg(a, x, y, dx, end, color):
    a.l([(x, y), (x + dx, end - 1), (x + dx - 1, end)], 'ink')
    a.dot(x + dx, end - 1, color)


def phase(f, cast):
    return ((-1, 0, 1, 0)[f], (0, 1, 0, -1)[f]) if cast is None else ((-1, 1, 0)[cast], (1, -1, 0)[cast])


def finish(a, d):
    return a.im.transpose(Image.Transpose.FLIP_LEFT_RIGHT) if d == 'right' else a.im


def orrery(d, f, cast):
    a = Pen()
    # Three separate open arcs plus one persistent pebble. Internal negative
    # space is anatomy, not a solid disk animated by rigid rotation.
    s, t = phase(f, cast)
    spread = (0, 1, 0)[cast] if cast is not None else 0
    top = 3 + min(s, 0)
    paths = [([(3-spread, 6+s), (3-spread, 4+s), (4, top), (7+t, top)], 'water3'),
             ([(10+t, 3), (11+spread, 4), (12+spread, 7-t), (11+spread, 9-t)], 'water4'),
             ([(10+s, 11+spread), (7+s, 12+spread), (4, 11+spread), (3, 10+t)], 'blue2')]
    # The down-leading arc opens low; up-leading arc opens high. Side travel
    # is a quarter turn with one independently lagging endpoint.
    def orient(pt):
        x, y = pt
        if d == 'up': return 15-x, 15-y
        if d in ('left', 'right'): return y, 15-x
        return x, y
    for points, color in paths:
        points = [orient(p) for p in points]
        a.l(points, 'ink', 2)
        a.l(points, color)
        a.dot(*points[-1], 'watergleam')
    # Authored clear-water aperture: a complete transparent moat around the
    # pebble is preserved even when one traveling arc approaches the center.
    a.r((6, 6, 10, 10), 'transparent')
    a.e((7, 7, 9, 9), 'ink')
    a.dot(8, 7, 'slate')
    if cast == 0: a.dot(*orient((4, 7)), 'watergleam')
    if cast == 1: a.dot(*orient((11, 11)), 'watergleam')
    if cast == 2: a.dot(*orient((5, 4)), 'watergleam')
    return finish(a, d)


def vowbough(d, f, cast):
    a = Pen(); s, t = phase(f, cast); side = d in ('left', 'right')
    front = 3 if side else 5
    hy = (7 if d == 'up' else 8) + (1 if cast == 0 else 0)
    # Four planted limbs and high belly; empty spaces remain between them.
    for x, z in ((5, s), (7, -t), (10, -s), (12, t)):
        leg(a, x, 10, z if cast is None else 0, 13 if x in (5, 10) else 14, 'wood4')
    a.p([(5, 7), (10, 7), (12, 9), (12, 10), (6, 10), (5, 9)], 'ink')
    a.l([(6, 8), (10, 8), (11, 9)], 'wood4', 2)
    a.l([(5, 8), (front+1, hy)], 'wood3', 2)
    # Outward flat branch fans, not a vertical crown.
    bend = (1, -1, 0)[cast] if cast is not None else t
    a.l([(front+1, hy-1), (5, 5), (3, 3+bend), (1, 3+bend)], 'ink')
    a.l([(5, 5), (4, 2+bend), (2, 2+bend)], 'ink')
    a.l([(front+3, hy-1), (9, 5), (11, 3-bend), (14, 3-bend)], 'ink')
    a.l([(9, 5), (11, 2-bend), (13, 2-bend)], 'ink')
    a.l([(1, 3+bend), (3, 3+bend)], 'pine5')
    a.l([(11, 3-bend), (14, 3-bend)], 'leaflight')
    a.dot(2, 2+bend, 'pine4'); a.dot(13, 2-bend, 'pine4')
    a.p([(front, hy-1), (front+3, hy-2), (front+4, hy), (front+3, hy+2), (front, hy+1)], 'ink')
    a.l([(front+1, hy), (front+3, hy)], 'wood5')
    if d != 'up':
        eye(a, front, hy-1)
        if not side: eye(a, front+3, hy-1)
    else: a.dot(front+2, hy-1, 'pine3')
    a.l([(12, 8), (14, 7+s)], 'pine4')
    if cast == 1: a.dot(2, 6, 'leaflight'); a.dot(13, 5, 'pine5')
    if cast == 2: a.dot(4, 6, 'leafwarm')
    return finish(a, d)


def kilnwhorl(d, f, cast):
    a = Pen(); s, t = phase(f, cast); side = d in ('left', 'right')
    # Off-center shell and three broad, divided living mantle lobes.
    sx = 7 if side else (5 if d == 'up' else 6)
    sy = 3 + (1 if f == 2 and cast is None else 0)
    for x, z in ((3, s), (7, t), (11, -s)):
        a.p([(x, 10), (x+2, 10), (x+2+z, 13), (x+z, 14), (x-1, 12)], 'ink')
        a.l([(x, 11), (x+z, 13), (x+1+z, 13)], 'rose4')
    a.e((sx-2, sy, sx+6, sy+9), 'ink')
    a.e((sx-1, sy+1, sx+5, sy+8), 'fire2')
    a.l([(sx+4, sy+6), (sx+4, sy+3), (sx+2, sy+2), (sx, sy+3), (sx, sy+5), (sx+2, sy+6), (sx+2, sy+4)], 'wood1')
    a.l([(sx+1, sy+1), (sx+3, sy+1), (sx+5, sy+3)], 'gold4')
    fy = 9 if d != 'up' else 7
    fx = 1 if side else 3
    a.p([(fx, fy+1), (fx+1, fy-1), (fx+4, fy-1), (fx+5, fy+2), (fx+3, fy+4), (fx, fy+3)], 'ink')
    a.e((fx+1, fy, fx+4, fy+3), 'rose5')
    a.l([(fx+1, fy), (fx+1, fy-2+t)], 'rose3')
    a.dot(fx+1, fy-2+t, 'white')
    if d != 'up':
        eye(a, fx+1, fy)
        if not side: eye(a, fx+4, fy)
    else: a.dot(fx+3, fy, 'rose3')
    # Shell mouth visibly opens on release and closes on recovery.
    if cast == 0: a.l([(sx+5, sy+5), (sx+5, sy+7)], 'ink'); a.dot(sx+4, sy+6, 'fire3')
    elif cast == 1:
        a.p([(sx+4, sy+4), (sx+6, sy+5), (sx+5, sy+8), (sx+3, sy+7)], 'ink')
        a.l([(sx+4, sy+5), (sx+4, sy+7)], 'gold4')
        a.dot(sx+6, sy+8, 'ember')
    elif cast == 2: a.l([(sx+4, sy+5), (sx+5, sy+7)], 'fire0'); a.dot(3, 13, 'fire3')
    return finish(a, d)


def cairnward(d, f, cast):
    a = Pen(); s, t = phase(f, cast); side = d in ('left', 'right')
    # Tail open arch stays separate from three separated ridges.
    a.l([(11, 10), (13, 9), (14, 6+t), (12, 5+t)], 'ink', 2)
    a.l([(12, 9), (13, 7+t), (12, 6+t)], 'stone4')
    for x, z in ((4, s), (6, -t), (9, -s), (11, t)):
        leg(a, x, 10, z if cast is None else 0, 13 if x in (4, 9) else 14, 'wood5')
    a.p([(3, 8), (6, 6), (11, 7), (12, 10), (10, 12), (4, 11)], 'ink')
    a.p([(4, 8), (7, 7), (10, 8), (11, 10), (9, 11), (4, 10)], 'wood3')
    for j, (x, y) in enumerate(((5, 4), (8, 2), (11, 4))):
        sink = int(cast is not None and j <= cast)
        lift = int(cast is None and (f+j)%4 == 1)
        y += sink + lift
        a.p([(x-1, 7), (x-1, y+1), (x, y), (x+1, y+1), (x+1, 7)], 'ink')
        a.l([(x, y+1), (x, 6)], 'stone5')
    nx = 1 if side else 2; ny = 8 if d != 'up' else 6
    ny += int(cast == 0)
    a.p([(nx, ny+3), (nx+1, ny), (nx+3, ny-1), (nx+5, ny+1), (nx+4, ny+3), (nx+2, ny+4)], 'ink')
    a.l([(nx+1, ny+2), (nx+3, ny), (nx+4, ny+1)], 'wood5', 2)
    if d != 'up': eye(a, nx+3, ny)
    else: a.dot(nx+3, ny+1, 'wood2')
    a.dot(nx, ny+3, 'ink')
    if cast == 1: a.l([(1, 13), (3, 13)], 'stone4')
    if cast == 2: a.l([(11, 14), (13, 14)], 'stone4')
    return finish(a, d)


def bellmantle(d, f, cast):
    a = Pen(); s, t = phase(f, cast); side = d in ('left', 'right')
    # Rear walking legs, separately tapping raised forelegs.
    for x, z in ((6, s), (9, -s)): leg(a, x, 10, z, 14, 'gold2')
    for x, sign, z in ((5, -1, t), (10, 1, -t)):
        a.l([(x, 7), (x+sign*2, 9+z), (x+sign*2, 12+z)], 'ink')
        a.dot(x+sign*2, 11+z, 'silver')
    lift = (0, -2, 1)[cast] if cast is not None else t
    for x, sg, lag in ((5, -1, lift), (10, 1, -s if cast is None else lift+1)):
        a.p([(x, 7), (x+sg*2, 8+lag), (x+sg*2, 11+lag), (x, 12+lag), (x-sg, 10)], 'ink')
        a.l([(x+sg, 8+lag), (x+sg, 11+lag), (x, 11+lag)], 'gold3' if sg<0 else 'silver')
    a.l([(7, 6), (8, 10), (7, 12)], 'ink', 3)
    a.l([(7, 7), (8, 10), (7, 11)], 'teal1')
    hx = 5 if side else 6; hy = 5 if d != 'up' else 4
    a.e((hx, hy, hx+3, hy+3), 'ink')
    a.l([(hx+1, hy+1), (hx+2, hy+1)], 'watergleam')
    if d != 'up': eye(a, hx, hy+1); eye(a, hx+3, hy+1)
    spread = (0, 1, -1)[cast] if cast is not None else 0
    # Unequal mandibles: narrow hook on left, broad hollow crescent on right.
    a.l([(hx, hy), (hx-2-spread, 3), (hx-1-spread, 1)], 'ink')
    a.dot(hx-1-spread, 2, 'gold3')
    a.l([(hx+3, hy), (hx+5+spread, 4), (hx+4+spread, 2), (hx+2, 2)], 'ink', 2)
    a.l([(hx+3, hy-1), (hx+4+spread, 4), (hx+3+spread, 3)], 'silver')
    if cast == 1: a.dot(13, 7, 'gold4')
    if cast == 2: a.dot(11, 5, 'white')
    return finish(a, d)


def shadeweaver(d, f, cast):
    a = Pen(); s, t = phase(f, cast); side = d in ('left', 'right')
    # Four high arches, four lower legs: all attach to the living abdomen.
    for x, sg in ((6, -1), (9, 1)):
        a.l([(x, 9), (x+sg, 3+s*sg), (x+sg*3, 4+s*sg), (x+sg*4, 8+t)], 'ink')
        a.dot(x+sg*3, 4+s*sg, 'pine5')
        a.l([(x, 10), (x+sg*2, 6-t*sg), (x+sg*4, 8-t*sg), (x+sg*4, 11)], 'ink')
        a.dot(x+sg*2, 6-t*sg, 'wood4')
        a.l([(x, 10), (x+sg*2, 11+s*sg), (x+sg*3, 12+s*sg)], 'ink')
        a.l([(x, 11), (x+sg, 12-t*sg), (x+sg*2, 13-t*sg)], 'ink')
    # Leaf canopy attaches at a narrow visible pedicel, leaving the arches open.
    tilt = (0, -1, 1)[cast] if cast is not None else t
    a.l([(7, 8), (8, 6)], 'wood3')
    a.p([(5, 4+tilt), (7, 2), (10, 3-tilt), (11, 5), (9, 7), (6, 6)], 'ink')
    a.p([(6, 4+tilt), (7, 3), (9, 4-tilt), (10, 5), (8, 6), (6, 5)], 'leaflight')
    a.l([(7, 4), (9, 5)], 'pine3')
    a.e((5, 8, 10, 12), 'ink'); a.e((6, 9, 9, 11), 'pine4')
    hx = 4 if side else 5; hy = 8 if d == 'up' else 10
    a.e((hx, hy, hx+5, hy+3), 'ink'); a.l([(hx+1, hy+1), (hx+4, hy+1)], 'leafwarm')
    if d != 'up': eye(a, hx+1, hy); eye(a, hx+4, hy)
    else: a.dot(hx+2, hy+1, 'pine2')
    if cast == 0: a.l([(3, 10), (3, 8), (5, 8)], 'watergleam')
    if cast == 1: a.l([(11, 9), (13, 8), (13, 10)], 'leaflight')
    if cast == 2: a.l([(4, 11), (4, 9)], 'wood5')
    return finish(a, d)


def tideplume(d, f, cast):
    a = Pen(); s, t = phase(f, cast); side = d in ('left', 'right')
    # Three connected tail sails, deliberately distinct from floating boats.
    fold = (1, -1, 0)[cast] if cast is not None else t
    sails = [[(9, 9), (10, 3+fold), (11, 2+fold), (12, 7)],
             [(10, 10), (12, 4-fold), (14, 5-fold), (13, 9)],
             [(10, 10), (14, 8+fold), (14, 11), (11, 11)]]
    for j, points in enumerate(sails):
        a.p(points, 'ink'); a.l([points[0], (points[1][0], points[1][1]+1), points[2]], ('blue3', 'water3', 'water4')[j])
    for x, z, end in ((6, s, 14), (9, -t, 13)):
        leg(a, x, 10, z, end, 'gold2')
    a.e((5, 7, 11, 11), 'ink'); a.e((6, 8, 10, 10), 'water4')
    nx = 4 if side else 6; hy = 3 if d != 'up' else 2
    a.l([(6, 9), (nx+1, 7), (nx+1, hy+2)], 'ink', 3)
    a.l([(6, 8), (nx+1, 6), (nx+1, hy+2)], 'blue3')
    a.e((nx-1, hy, nx+3, hy+3), 'ink'); a.e((nx, hy+1, nx+2, hy+2), 'watergleam')
    a.l([(nx-2, hy+2), (nx, hy+2)], 'gold2')
    a.l([(nx, hy), (nx-1, hy-1), (nx-3, hy-1)], 'water3')
    if d != 'up': eye(a, nx, hy+1)
    else: a.dot(nx+2, hy+1, 'water2')
    wy = 10 if cast == 0 else (8 if cast == 1 else 9)
    a.l([(7, 8), (8, wy), (10, wy)], 'water1')
    if cast == 1: a.l([(3, 13), (4, 14), (6, 14)], 'watergleam')
    if cast == 2: a.dot(12, 12, 'watergleam')
    return finish(a, d)


def hearthmoth(d, f, cast):
    a = Pen(); s, t = phase(f, cast); side = d in ('left', 'right')
    for x, z, end in ((5, s, 13), (6, -t, 14), (10, -s, 13), (9, t, 14)):
        leg(a, x, 10, z, end, 'wood4')
    cup = (1, 2, 0)[cast] if cast is not None else 0
    left = 1+cup; right = 14-cup
    # Two unequal triangular roof wings with open inner edges and real veins.
    a.p([(6, 7), (left, 3+t), (left, 10+s), (5, 12), (6, 10)], 'ink')
    a.p([(5, 7), (left+1, 5+t), (left+1, 10+s), (4, 10), (5, 10)], 'fire2')
    a.l([(left+1, 6+t), (4, 8), (4, 10)], 'gold4')
    a.p([(9, 7), (right, 2-t), (right, 9-s), (11, 12), (9, 10)], 'ink')
    a.p([(10, 7), (right-1, 4-t), (right-1, 9-s), (11, 10), (10, 10)], 'rose4')
    a.l([(right-1, 5-t), (11, 8), (11, 10)], 'fire3')
    a.l([(7, 7), (8, 11), (7, 13)], 'ink', 3)
    a.dot(7, 10, 'gold4' if cast in (0, 1) else 'fire3')
    a.dot(8, 12, 'gold4' if cast == 1 else 'fire2')
    hx = 5 if side else 6; hy = 5 if d != 'up' else 4
    a.l([(hx, hy), (hx-1, hy-2), (hx-2, hy-2)], 'ink')
    a.dot(hx-1, hy-3, 'wood4')
    a.l([(hx+3, hy), (hx+4, hy-2), (hx+5, hy-2)], 'ink')
    a.dot(hx+4, hy-3, 'wood4')
    a.e((hx, hy, hx+3, hy+3), 'ink'); a.l([(hx+1, hy+1), (hx+2, hy+2)], 'wood5')
    if d != 'up': eye(a, hx, hy+1); eye(a, hx+3, hy+1)
    else: a.dot(hx+2, hy+1, 'fire0')
    if cast == 2: a.l([(5, 14), (7, 14)], 'fire3')
    return finish(a, d)


DRAW = dict(zip(IDS, (orrery, vowbough, kilnwhorl, cairnward, bellmantle, shadeweaver, tideplume, hearthmoth)))


def field(fid, d, f, cast=None):
    if type(fid) is not int or fid not in IDS or d not in DIRS or type(f) is not int or not 0 <= f < 4 or (cast is not None and (type(cast) is not int or not 0 <= cast < 3)):
        raise ValueError('Unsupported form, direction, walk frame, or cast pose')
    return DRAW[fid](d, f, cast)


def big_eye(a, x, y):
    a.e((x, y, x+3, y+4), 'ink'); a.r((x+1, y, x+2, y+2), 'white'); a.dot(x+1, y+2, 'ink')


def portrait(fid):
    """Independent 32px anatomy compositions, never scaled field sprites."""
    a = Pen(32)
    if fid == 121:
        for pts, c in (([(6, 15), (3, 10), (6, 5), (12, 3), (15, 4)], 'water3'),
                       ([(21, 4), (26, 8), (28, 14), (26, 19)], 'water4'),
                       ([(23, 25), (18, 28), (10, 27), (6, 23), (6, 20)], 'blue2')):
            a.l(pts, 'ink', 4); a.l(pts, c, 2); a.dot(*pts[-1], 'watergleam')
        a.p([(14, 14), (17, 13), (20, 16), (18, 20), (14, 19), (13, 16)], 'ink')
        a.l([(15, 14), (17, 14), (18, 15)], 'slate')
    elif fid == 122:
        for x, y in ((10, 23), (14, 24), (23, 22), (27, 22)):
            a.l([(x, y), (x-1, 28), (x-3, 29)], 'ink', 2); a.dot(x-1, 28, 'wood4')
        a.p([(10, 17), (22, 16), (28, 21), (26, 25), (14, 25), (10, 22)], 'ink')
        a.p([(12, 18), (22, 18), (26, 21), (25, 23), (14, 23)], 'wood3')
        a.l([(11, 20), (11, 15), (10, 12)], 'wood4', 3)
        for pts in ([(9, 12), (7, 8), (3, 6), (1, 6)], [(7, 8), (5, 3), (2, 3)],
                    [(13, 12), (18, 8), (24, 5), (29, 5)], [(18, 8), (23, 2), (27, 2)]): a.l(pts, 'ink', 2)
        a.l([(1, 5), (5, 5)], 'pine5'); a.l([(23, 4), (29, 4)], 'leaflight'); a.l([(23, 2), (27, 2)], 'pine4')
        a.p([(5, 13), (9, 11), (15, 12), (17, 16), (13, 21), (9, 22), (5, 18)], 'ink')
        a.p([(7, 14), (10, 13), (14, 14), (15, 16), (12, 20), (9, 20), (7, 17)], 'wood5')
        big_eye(a, 6, 14); big_eye(a, 13, 13); a.dot(10, 19, 'ink')
        a.l([(27, 19), (30, 15)], 'pine4', 2)
    elif fid == 123:
        for pts in ([(7, 22), (12, 23), (11, 28), (5, 29), (3, 27)],
                    [(13, 23), (19, 24), (21, 28), (16, 30), (12, 28)],
                    [(23, 22), (27, 23), (29, 27), (25, 29), (22, 27)]):
            a.p(pts, 'ink'); a.l([pts[0], pts[-1], pts[-2]], 'rose4', 2)
        a.e((10, 3, 30, 25), 'ink'); a.e((12, 5, 28, 23), 'fire2')
        a.l([(26, 19), (26, 11), (22, 7), (17, 8), (14, 13), (16, 18), (21, 20), (23, 16), (21, 13), (18, 14)], 'wood1', 2)
        a.l([(16, 6), (21, 5), (26, 8)], 'gold4', 2)
        a.p([(3, 18), (7, 14), (12, 15), (16, 22), (12, 27), (6, 27), (2, 23)], 'ink')
        a.e((4, 17, 13, 25), 'rose5'); a.l([(5, 19), (4, 12)], 'rose3', 2); big_eye(a, 3, 12); big_eye(a, 10, 17)
        a.l([(26, 18), (28, 21), (26, 24)], 'ink', 3); a.l([(26, 19), (27, 21)], 'gold4')
    elif fid == 124:
        a.l([(24, 23), (28, 18), (29, 11), (26, 8), (24, 9)], 'ink', 3); a.l([(25, 21), (27, 17), (28, 12), (26, 10)], 'stone4')
        for x, y in ((8, 23), (13, 25), (20, 23), (24, 22)):
            a.l([(x, y), (x-1, 28), (x-3, 29)], 'ink', 3); a.l([(x-2, 29), (x, 29)], 'wood5')
        a.e((5, 13, 26, 26), 'ink'); a.e((7, 15, 24, 24), 'wood3')
        for x, y in ((10, 7), (16, 2), (22, 6)):
            a.p([(x-2, 16), (x-2, y+2), (x, y), (x+2, y+2), (x+2, 15)], 'ink')
            a.l([(x, y+2), (x, 13)], 'stone5', 2)
        a.p([(1, 24), (3, 19), (6, 16), (11, 16), (14, 21), (10, 25), (5, 27)], 'ink')
        a.p([(3, 23), (6, 19), (10, 18), (12, 21), (9, 24), (5, 25)], 'wood5'); big_eye(a, 7, 18); a.dot(2, 24, 'ink')
    elif fid == 125:
        for pts in ([(12, 23), (10, 29), (7, 30)], [(19, 23), (22, 28), (25, 29)],
                    [(11, 15), (5, 19), (4, 27)], [(21, 14), (27, 18), (28, 26)]):
            a.l(pts, 'ink', 2); a.dot(*pts[-1], 'silver')
        for pts, c in (([(12, 14), (6, 17), (6, 23), (11, 26), (14, 21)], 'gold3'),
                       ([(19, 14), (25, 17), (25, 25), (20, 27), (17, 22)], 'silver')):
            a.p(pts, 'ink'); a.l([(pts[1][0]+1, 18), (pts[1][0]+1, 22), (pts[0][0], 24)], c, 2)
        a.e((12, 11, 20, 25), 'ink'); a.l([(15, 14), (17, 20), (15, 23)], 'teal1', 3)
        a.l([(12, 13), (7, 9), (7, 4), (10, 2)], 'ink', 2); a.l([(8, 8), (8, 4)], 'gold2')
        a.l([(20, 13), (26, 8), (25, 3), (20, 1), (17, 2)], 'ink', 4)
        a.l([(20, 11), (24, 8), (23, 4), (20, 3)], 'silver', 2)
        a.e((11, 10, 21, 17), 'ink'); a.e((13, 11, 19, 15), 'watergleam'); big_eye(a, 11, 11); big_eye(a, 18, 11)
    elif fid == 126:
        for pts in ([(12, 19), (10, 6), (5, 5), (2, 17)], [(13, 21), (8, 12), (3, 13), (1, 24)],
                    [(12, 23), (7, 22), (3, 28)], [(13, 24), (10, 28), (7, 30)],
                    [(19, 19), (22, 5), (26, 7), (30, 16)], [(19, 21), (24, 13), (29, 14), (30, 24)],
                    [(19, 23), (24, 23), (28, 28)], [(18, 24), (22, 28), (24, 30)]):
            a.l(pts, 'ink', 2); a.dot(*pts[1], 'pine5')
        a.l([(16, 18), (17, 11)], 'wood3', 2)
        a.p([(10, 9), (14, 3), (21, 4), (24, 9), (20, 13), (14, 13)], 'ink')
        a.p([(12, 9), (15, 5), (20, 6), (22, 9), (19, 11), (14, 11)], 'leaflight')
        a.l([(14, 7), (19, 10)], 'pine3'); a.e((10, 17, 22, 26), 'ink'); a.e((12, 18, 20, 24), 'pine4')
        a.e((8, 21, 22, 29), 'ink'); a.e((10, 22, 20, 27), 'leafwarm'); big_eye(a, 9, 22); big_eye(a, 18, 21); a.l([(14, 26), (16, 26)], 'pine2')
    elif fid == 127:
        for pts, c in (([(19, 22), (21, 6), (24, 3), (26, 15)], 'blue3'),
                       ([(21, 23), (26, 9), (30, 11), (28, 22)], 'water3'),
                       ([(22, 23), (30, 18), (30, 25), (25, 26)], 'water4')):
            a.p(pts, 'ink'); a.l([pts[0], (pts[1][0], pts[1][1]+2), pts[2]], c, 2)
        for pts in ([(13, 23), (12, 29), (9, 30)], [(20, 23), (21, 28), (24, 28)]): a.l(pts, 'ink', 2); a.dot(*pts[-1], 'gold2')
        a.e((10, 16, 25, 25), 'ink'); a.e((12, 18, 23, 23), 'water4')
        a.l([(13, 20), (10, 15), (11, 8)], 'ink', 5); a.l([(13, 19), (11, 14), (12, 9)], 'blue3', 2)
        a.e((6, 5, 16, 11), 'ink'); a.e((8, 6, 14, 9), 'watergleam'); a.l([(2, 9), (8, 9)], 'gold2', 2)
        a.l([(10, 6), (7, 3), (3, 3)], 'water3', 2); big_eye(a, 8, 6); a.l([(15, 19), (18, 22), (22, 22)], 'water1')
    elif fid == 128:
        for pts in ([(12, 23), (9, 28), (6, 29)], [(14, 24), (12, 30), (10, 30)],
                    [(19, 23), (24, 28), (27, 29)], [(17, 25), (19, 30), (21, 30)]): a.l(pts, 'ink', 2)
        a.p([(13, 14), (2, 5), (1, 22), (10, 26), (13, 21)], 'ink')
        a.p([(11, 15), (4, 9), (3, 21), (9, 23), (11, 21)], 'fire2')
        a.l([(4, 11), (8, 16), (7, 21)], 'gold4', 2); a.l([(5, 19), (9, 19)], 'fire0')
        a.p([(18, 14), (29, 3), (30, 21), (23, 26), (18, 21)], 'ink')
        a.p([(20, 15), (27, 7), (28, 20), (24, 23), (20, 21)], 'rose4')
        a.l([(27, 9), (23, 16), (24, 21)], 'fire3', 2); a.l([(22, 19), (27, 18)], 'rose2')
        a.e((12, 13, 19, 28), 'ink'); a.e((14, 19, 17, 21), 'gold4'); a.e((14, 24, 17, 26), 'fire3')
        for pts in ([(13, 12), (10, 7), (7, 7)], [(18, 12), (21, 6), (24, 6)]):
            a.l(pts, 'ink', 2); a.dot(pts[1][0], pts[1][1]-2, 'wood4')
        a.e((10, 10, 21, 17), 'ink'); a.e((12, 11, 19, 15), 'wood5'); big_eye(a, 10, 11); big_eye(a, 18, 11)
    else:
        raise ValueError('Unsupported portrait form')
    return a.im


def mask(im): return Image.frombytes('L', im.size, bytes(255 if p else 0 for p in im.tobytes()))
def norm(im):
    m = mask(im); b = m.getbbox()
    return m.crop(b).size, m.crop(b).tobytes()
def paste(dst, im, xy): dst.paste(im.convert(dst.mode), xy, mask(im))
def save(im, path): im.save(path, **({'transparency': 0} if im.mode == 'P' else {}), optimize=False)
def digest(path): return hashlib.sha256(path.read_bytes()).hexdigest()


def tensors():
    return ([[[field(fid, d, f) for f in range(4)] for d in DIRS] for fid in IDS],
            [[[field(fid, d, p, p) for p in range(3)] for d in DIRS] for fid in IDS],
            [portrait(fid) for fid in IDS])


def validate(fields, casts, portraits):
    assert tuple(f['id'] for f in ROSTER) == IDS
    rows = []; errors = []
    def check(truth, detail):
        if not truth: errors.append(detail)
    allimgs = [im for tensor in (fields, casts) for row in tensor for d in row for im in d] + portraits
    for im in allimgs:
        check(im.mode == 'P' and im.getpalette() == PAL and max(im.tobytes()) < 97, 'palette contract')
    for i, fid in enumerate(IDS):
        for d in range(4):
            w = fields[i][d]; c = casts[i][d]
            values = {'id': fid, 'direction': DIRS[d], 'unique_pixels': len({im.tobytes() for im in w+c}),
                      'unique_walk_masks': len({norm(im) for im in w}), 'unique_cast_masks': len({norm(im) for im in c})}
            rows.append(values)
            check(values['unique_pixels'] == 7, f'{fid} {DIRS[d]}: seven distinct indexed poses')
            check(values['unique_walk_masks'] == 4, f'{fid} {DIRS[d]}: four articulated walk masks')
            check(values['unique_cast_masks'] == 3, f'{fid} {DIRS[d]}: three articulated cast masks')
            for im in w+c:
                check(im.size == (16, 16), f'{fid}: dimensions')
                check(all(im.getpixel((x, y)) == 0 for x in range(16) for y in (0, 15)) and all(im.getpixel((x, y)) == 0 for x in (0, 15) for y in range(16)), f'{fid} {DIRS[d]}: transparent rim')
                check(30 <= sum(bool(p) for p in im.tobytes()) <= 210, f'{fid}: occupancy')
                if fid == 121:
                    seen = {(8,8)}; pending = [(8,8)]
                    while pending:
                        x,y = pending.pop()
                        for dx in (-1,0,1):
                            for dy in (-1,0,1):
                                q = (x+dx,y+dy)
                                if 0 <= q[0] < 16 and 0 <= q[1] < 16 and im.getpixel(q) and q not in seen:
                                    seen.add(q); pending.append(q)
                    check(len(seen) == 5, '121: persistent isolated pebble and central aperture')
        check(len({mask(row[0]).tobytes() for row in fields[i]}) == 4, f'{fid}: distinct direction masks')
        for tensor in (fields[i], casts[i]):
            for f in range(len(tensor[0])):
                check(len({mask(tensor[d][f]).tobytes() for d in range(4)}) == 4, f'{fid}: every pose has four direction masks')
                check(tensor[3][f].tobytes() == tensor[2][f].transpose(Image.Transpose.FLIP_LEFT_RIGHT).tobytes(), f'{fid}: mirrored side-facing contract')
        check(portraits[i].size == (32, 32) and portraits[i].tobytes() != fields[i][0][0].resize((32,32), Image.Resampling.NEAREST).tobytes(), f'{fid}: independent portrait')
    check(len({norm(row[0][0]) for row in fields}) == 8, 'eight unique front silhouettes')
    check(len({norm(im) for im in portraits}) == 8, 'eight unique portrait silhouettes')
    return {'passed': not errors, 'errors': sorted(set(errors)), 'images': len(allimgs), 'direction_rows': rows,
            'actor_palette_indices': sorted({p for im in allimgs for p in im.tobytes()}),
            'field_dimensions': [8,4,4,256], 'cast_dimensions': [8,4,3,256], 'portrait_dimensions': [8,1024]}


def previews(fields, casts, portraits):
    OUT.mkdir(exist_ok=True)
    roster = Image.new('RGB', (480, 310), RGB[P['dirt4']]); r = ImageDraw.Draw(roster)
    r.text((4,3), 'COVENANTS / ORIGINAL ART PROPOSAL / NOT IN GAME', fill=RGB[1])
    sheet = Image.new('RGB', (248, 8*86+18), RGB[P['dirt4']]); s = ImageDraw.Draw(sheet)
    s.text((3,2), 'WALK 0 1 2 3 / CAST 0 1 2', fill=RGB[1])
    for i, entry in enumerate(ROSTER):
        fid = entry['id']; key = entry['name'].lower().replace(' ', '_')
        x = (i%2)*240; y = 19+(i//2)*72
        r.text((x+4,y), f"{fid} {entry['name']}", fill=RGB[1])
        paste(roster, portraits[i], (x+4,y+17))
        for d in range(4): paste(roster, fields[i][d][0], (x+43+d*23,y+19))
        r.text((x+43,y+38), entry['phase']+' / '+entry['polarity'], fill=RGB[1])
        for p in range(3): paste(roster, casts[i][0][p], (x+164+p*24,y+20))
        sy = 18+i*86; s.text((3,sy), f"{fid} {entry['name']}", fill=RGB[1]); paste(sheet,portraits[i],(3,sy+19))
        walk = Pen(64).im; cast = Image.new('P',(48,64),0); cast.putpalette(PAL)
        for d in range(4):
            s.text((39,sy+17+d*16), DIRS[d][0].upper(), fill=RGB[1])
            for f, im in enumerate(fields[i][d]+casts[i][d]): paste(sheet, im, (58+f*26,sy+17+d*16))
            for f in range(4): walk.paste(fields[i][d][f],(f*16,d*16))
            for f in range(3): cast.paste(casts[i][d][f],(f*16,d*16))
        save(walk,OUT/f'{key}_walk.png'); save(cast,OUT/f'{key}_cast.png'); save(portraits[i],OUT/f'{key}_portrait.png')
        native = Image.new('RGB',(240,160),RGB[P['deep']]); n=ImageDraw.Draw(native)
        n.text((3,2),f'{fid} '+entry['name']+' / ART',fill=RGB[P['white']]); paste(native,portraits[i],(205,21))
        for bg, y0 in (('deep',19),('dirt4',91)):
            n.rectangle((0,y0,200,y0+65),fill=RGB[P[bg]])
            for d in range(4):
                for f,im in enumerate(fields[i][d]+casts[i][d]): paste(native,im,(3+f*28,y0+d*16))
        save(native,OUT/f'{key}_native.png');save(native.resize((960,640),Image.Resampling.NEAREST),OUT/f'{key}_4x.png')
        frames=[]
        for mode, f in [('walk',n)for n in range(4)]+[('cast',n)for n in range(3)]:
            frame=Image.new('RGB',(256,64),RGB[P['dirt4']])
            for d in range(4):paste(frame,(fields if mode=='walk'else casts)[i][d][f].resize((64,64),Image.Resampling.NEAREST),(d*64,0))
            frames.append(frame)
        frames[0].save(OUT/f'{key}_motion_4x.gif',save_all=True,append_images=frames[1:],duration=[round(t*1000/60)for t in WALK_TICKS[i]+CAST_TICKS[i]],loop=0,optimize=False,disposal=2)
        native_frames=[im.resize((64,16),Image.Resampling.NEAREST)for im in frames]
        native_frames[0].save(OUT/f'{key}_motion_native.gif',save_all=True,append_images=native_frames[1:],duration=[round(t*1000/60)for t in WALK_TICKS[i]+CAST_TICKS[i]],loop=0,optimize=False,disposal=2)
    for name,im in (('roster',roster),('all_frames',sheet)):
        save(im,OUT/f'{name}_native.png');save(im.resize((im.width*4,im.height*4),Image.Resampling.NEAREST),OUT/f'{name}_4x.png')
        save(im.convert('L'),OUT/f'{name}_grayscale_native.png')


def silhouette_report(fields):
    ref=json.loads((ROOT/'reference/current120-silhouettes.json').read_text()); old={}
    for row in ref['forms']:
        old[row['form_id']]=[bytes(255 if n&(1<<b)else 0 for n in bytes.fromhex(h)for b in range(7,-1,-1))for h in row['masks_hex']]
    current={fid:[mask(fields[i][d][0]).tobytes()for d in range(4)]for i,fid in enumerate(IDS)}
    nearest=[]; same=[]; normalized_same=[]
    for fid, directions in current.items():
        for d,m in enumerate(directions):
            candidates=[(sum(a!=b for a,b in zip(m,om)),oid,od)for oid,ms in old.items()for od,om in enumerate(ms)]
            delta,oid,od=min(candidates)
            nearest.append({'form':fid,'direction':DIRS[d],'nearest_current_form':oid,'nearest_direction':DIRS[od],'different_pixels':delta})
            if delta==0:same.append([fid,d,oid,od])
            mm=Image.frombytes('L',(16,16),m); b=mm.getbbox(); nm=(mm.crop(b).size,mm.crop(b).tobytes())
            for oid,ms in old.items():
                for od,om in enumerate(ms):
                    oi=Image.frombytes('L',(16,16),om);ob=oi.getbbox()
                    if nm==(oi.crop(ob).size,oi.crop(ob).tobytes()):normalized_same.append([fid,d,oid,od])
    pairs=[]
    for i,fid in enumerate(IDS):
        for gid in IDS[i+1:]: pairs.append({'forms':[fid,gid],'changed_front_pixels':sum(a!=b for a,b in zip(current[fid][0],current[gid][0]))})
    sheet=Image.new('RGB',(560,24+19*42),RGB[P['white']]);dr=ImageDraw.Draw(sheet)
    dr.text((4,3),'CURRENT 120 + COVENANT PROPOSAL 8 / SILHOUETTES ONLY',fill=RGB[1])
    for i,(fid,ms)in enumerate(list(old.items())+list(current.items())):
        x=(i%7)*80;y=24+(i//7)*42;dr.text((x+4,y),str(fid),fill=RGB[1])
        for d,m in enumerate(ms):sheet.paste(Image.new('RGB',(16,16),RGB[1]),(x+4+d*18,y+13),Image.frombytes('L',(16,16),m))
    save(sheet,OUT/'all128_silhouettes_native.png');save(sheet.resize((1120,sheet.height*2),Image.Resampling.NEAREST),OUT/'all128_silhouettes_2x.png')
    close=Image.new('RGB',(256,8*42+18),RGB[P['white']]);cd=ImageDraw.Draw(close)
    cd.text((3,2),'NEW FRONT / NEAREST CURRENT MASK',fill=RGB[1])
    for i,fid in enumerate(IDS):
        row=next(n for n in nearest if n['form']==fid and n['direction']=='down');y=18+i*42
        cd.text((3,y),f"{fid} / {row['nearest_current_form']} {row['nearest_direction']} / delta {row['different_pixels']}",fill=RGB[1])
        for x,m in ((5,current[fid][0]),(35,old[row['nearest_current_form']][DIRS.index(row['nearest_direction'])])):
            close.paste(Image.new('RGB',(16,16),RGB[1]),(x,y+14),Image.frombytes('L',(16,16),m))
        paste(close,fields[i][0][0],(72,y+14))
    save(close,OUT/'nearest_silhouettes_native.png');save(close.resize((1024,close.height*4),Image.Resampling.NEAREST),OUT/'nearest_silhouettes_4x.png')
    return {'reference_count':120,'reference_status':'104 accepted references plus 16 current Horizons candidate references; this is not 128-form release acceptance',
            'comparisons':8*4*120*4,'exact_matches':same,'translation_normalized_matches':normalized_same,
            'nearest_current_masks':nearest,'new_pair_front_differences':pairs,
            'minimum_new_pair_front_difference':min(x['changed_front_pixels']for x in pairs),
            'limitation':'Pixel-mask differences establish non-identity, not legal originality, artistic quality, motion readability or gameplay acceptance.'}


def terrain_review(fields, casts):
    sources=json.loads((ROOT/'reference/terrain-sources.json').read_text())
    rows=[]
    contact=Image.new('RGB',(6*32,8*38+16),RGB[P['dirt4']]);dr=ImageDraw.Draw(contact)
    dr.text((2,2),'TERRAIN / DIRECTION DOWN',fill=RGB[1])
    for i,fid in enumerate(IDS):
        sheet=Image.new('RGB',(6*168,114),RGB[P['deep']]);sd=ImageDraw.Draw(sheet)
        for b,source in enumerate(sources):
            patch=Image.open(ROOT/'reference'/f"{source['label']}.png").convert('RGB')
            sd.text((b*168+2,2),source['label'],fill=RGB[P['white']])
            samples=[];edges=[]
            for d in range(4):
                for f,im in enumerate(fields[i][d]+casts[i][d]):
                    tile=patch.copy();paste(tile,im,(4,4));sheet.paste(tile,(b*168+f*24,16+d*24))
                    px=im.tobytes();sample=[];edge=[]
                    for y in range(16):
                        for x in range(16):
                            c=px[y*16+x]
                            if not c:continue
                            fg=RGB[c];bg=patch.getpixel((x+4,y+4))
                            visible=sum((fg[k]-bg[k])**2 for k in range(3))>=48**2;sample.append(visible)
                            if any(not(0<=xx<16 and 0<=yy<16)or not px[yy*16+xx]for xx,yy in((x-1,y),(x+1,y),(x,y-1),(x,y+1))):edge.append(visible)
                    samples.append(sum(sample)/len(sample));edges.append(sum(edge)/len(edge))
            rows.append({'id':fid,'source':source['label'],'minimum_opaque_fraction':round(min(samples),6),'minimum_boundary_fraction':round(min(edges),6)})
            tile=patch.copy();paste(tile,fields[i][0][0],(4,4));contact.paste(tile,(b*32+4,i*38+28))
        dr.text((2,i*38+16),str(fid),fill=RGB[1])
        key=ROSTER[i]['name'].lower().replace(' ','_')
        save(sheet,OUT/f'{key}_terrain_native.png')
    save(contact,OUT/'terrain_contact_native.png');save(contact.resize((768,1280),Image.Resampling.NEAREST),OUT/'terrain_contact_4x.png')
    return {'samples':8*4*7*6,'source_crops':sources,'metric':'Heuristic native RGB555 Euclidean distance >=48. Does not establish gameplay readability. Six frozen terrain crops only.',
            'minimum_opaque_fraction':min(r['minimum_opaque_fraction']for r in rows),'minimum_boundary_fraction':min(r['minimum_boundary_fraction']for r in rows),'rows':rows}


def emit(fields, casts, portraits):
    GEN.mkdir(exist_ok=True); (GEN/'data').mkdir(exist_ok=True)
    dimensions={'walk':'[8][4][4][256]','cast':'[8][4][3][256]','portraits':'[8][1024]'}
    def lines(value,depth):
        pad=' '*depth
        yield pad+'{\n'
        if hasattr(value,'tobytes'):
            px=value.tobytes()
            for j in range(0,len(px),32):yield pad+' '+','.join(map(str,px[j:j+32]))+',\n'
        else:
            for child in value:yield from lines(child,depth+1)
        yield pad+'},\n'
    source=[]
    for name,tensor in (('walk',fields),('cast',casts),('portraits',portraits)):
        source.append(f'const unsigned char covenant_art_{name}{dimensions[name]} = {{\n')
        for row in tensor:source.extend(lines(row,1))
        source.append('};\n')
    chunks=[];chunk=''
    for line in source:
        if len((chunk+line).encode())>30000:chunks.append(chunk);chunk=''
        chunk+=line
    if chunk:chunks.append(chunk)
    for n,chunk in enumerate(chunks):(GEN/f'data/part_{n:03d}.inc').write_text(chunk)
    header='''/* Generated asset proposal. No catalog, OAM, collision, or gameplay changes. */
#ifndef COVENANT_ART_PROPOSAL_H
#define COVENANT_ART_PROPOSAL_H
#define COVENANT_ART_COUNT 8
#define COVENANT_ART_PIXEL_BYTES 65536
/* IDs 121..128; direction down/up/left/right; 16x16 row-major 8bpp,
 * transparent zero, unchanged shared actor palette 0..96. Field anchor 8,8;
 * separate renderer shadow anchor 8,13. No in-sprite shadow or palette upload.
 * Cast poses anticipate/release/settle. All pointers have immutable lifetime.
 * Unsupported IDs or indices return null. Caller owns clipping and rendering. */
struct CovenantArtEntry {
    unsigned char form_id, anchor_x, anchor_y, shadow_x, shadow_y;
    unsigned char walk_ticks[4], cast_ticks[3];
};
extern const struct CovenantArtEntry covenant_art_entries[8];
extern const unsigned char covenant_art_walk[8][4][4][256];
extern const unsigned char covenant_art_cast[8][4][3][256];
extern const unsigned char covenant_art_portraits[8][1024];
int covenant_art_index(unsigned int form_id);
const unsigned char *covenant_art_frame(unsigned int form_id, unsigned int direction, unsigned int frame);
const unsigned char *covenant_art_cast_frame(unsigned int form_id, unsigned int direction, unsigned int pose);
const unsigned char *covenant_art_portrait(unsigned int form_id);
#endif
'''
    code='#include "covenant_art.h"\n'+''.join(f'#include "data/part_{n:03d}.inc"\n'for n in range(len(chunks)))
    code+='\nconst struct CovenantArtEntry covenant_art_entries[8] = {\n'
    for i,fid in enumerate(IDS):code+='    {'+f'{fid},8,8,8,13,'+'{'+','.join(map(str,WALK_TICKS[i]))+'},{'+','.join(map(str,CAST_TICKS[i]))+'}}, /* '+ROSTER[i]['name']+' */\n'
    code+='''};
int covenant_art_index(unsigned int form_id) {
    return form_id >= 121 && form_id <= 128 ? (int)(form_id - 121) : -1;
}
const unsigned char *covenant_art_frame(unsigned int form_id, unsigned int direction, unsigned int frame) {
    int i=covenant_art_index(form_id);
    return i < 0 || direction >= 4 || frame >= 4 ? (const unsigned char *)0 : covenant_art_walk[i][direction][frame];
}
const unsigned char *covenant_art_cast_frame(unsigned int form_id, unsigned int direction, unsigned int pose) {
    int i=covenant_art_index(form_id);
    return i < 0 || direction >= 4 || pose >= 3 ? (const unsigned char *)0 : covenant_art_cast[i][direction][pose];
}
const unsigned char *covenant_art_portrait(unsigned int form_id) {
    int i=covenant_art_index(form_id);
    return i < 0 ? (const unsigned char *)0 : covenant_art_portraits[i];
}
'''
    (GEN/'covenant_art.h').write_text(header);(GEN/'covenant_art.c').write_text(code)
    sizes={str(p.relative_to(ROOT)):p.stat().st_size for p in sorted(GEN.rglob('*'))if p.is_file()}
    assert max(sizes.values()) < 75000
    return sizes


def generate():
    fields, casts, portraits=tensors();valid=validate(fields,casts,portraits)
    if not valid['passed']:raise ValueError('\n'.join(valid['errors']))
    previews(fields,casts,portraits)
    comparison=silhouette_report(fields)
    terrain=terrain_review(fields,casts)
    (ROOT/'terrain-readability.json').write_text(json.dumps(terrain,indent=2)+'\n')
    assert not comparison['exact_matches'] and not comparison['translation_normalized_matches']
    sizes=emit(fields,casts,portraits)
    manifest={'scope':'DESIGN_ASSET_PROPOSAL_ONLY_NOT_ENABLED_NOT_RELEASE_ACCEPTED','generator_sha256':digest(Path(__file__)),
      'roster_sha256':digest(ROOT/'reference/legendary-roster.json'),'palette_sha256':digest(ROOT/'reference/palette.json'),
      'rights':'Original code-native pixel geometry authored from the original Covenant brief. No Nintendo, Tolkien, traced, downloaded, extracted, or generated-image creature art.',
      'field_contract':{'dimensions':[16,16],'directions':list(DIRS),'walk_frames':4,'cast_frames':3,'cast_poses':['anticipate','release','settle'],'anchor':[8,8],'shadow_anchor':[8,13],'shadow_in_sprite':False,'transparent_index':0,'actor_palette_entries':97},
      'portrait_dimensions':[32,32],'pixel_data_bytes':65536,'entry_table_bytes':96,'mutable_data_bytes':0,'bss_bytes':0,
      'generated_file_bytes':sizes,'validation':valid,'silhouette_comparison':comparison,
      'terrain_review':{'sample_count':terrain['samples'],'minimum_opaque_fraction':terrain['minimum_opaque_fraction'],'minimum_boundary_fraction':terrain['minimum_boundary_fraction']},
      'entries':[{'index':i,'form_id':f['id'],'family':f['family_id'],'name':f['name'],'phase':f['phase'],'polarity':f['polarity'],
        'anchor':[8,8],'shadow_anchor':[8,13],'walk_ticks':WALK_TICKS[i],'cast_ticks':CAST_TICKS[i],
        'silhouette':f['silhouette'],'gait_intent':f['gait'],'cast_intent':f['cast_animation']}for i,f in enumerate(ROSTER)],
      'limitations':['These are art review composites, not emulator captures or live renderer evidence.',
        'Suggested animation timing is not integrated. Event-conditioned Orrery interception pauses need runtime integration.',
        'No effect renderer pixels, enlarged hitboxes, OAM allocation, source policies, catalog unlocks, or gameplay code are included.',
        'Native motion cadence, all terrains, collision clipping, live shadows, and localization still require future game review.',
        'Phase and independent Yin/Yang metadata carry no damage or gameplay authority. Companions are living agents, never loot or equipment.',
        'Current 120-form references include 16 Horizons candidates that were not release-accepted when this kit was authored.']}
    (ROOT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    return manifest


def output_hashes():
    paths=list(OUT.glob('*'))+list(GEN.rglob('*'))+[ROOT/'manifest.json',ROOT/'terrain-readability.json']
    return {str(p.relative_to(ROOT)):digest(p)for p in sorted(paths)if p.is_file()}


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--verify',action='store_true');args=parser.parse_args()
    manifest=generate()
    report={'pixel_validation':manifest['validation'],'silhouette_exact_matches':len(manifest['silhouette_comparison']['exact_matches'])}
    if args.verify:
        before=output_hashes();generate();assert before==output_hashes(),'Non-deterministic regeneration'
        report.update({'deterministic_regeneration':True,'hashes':before})
        fields,casts,portraits=tensors()
        source=''.join(p.read_text()for p in sorted((GEN/'data').glob('part_*.inc')))
        expected=[bytes(p for row in fields for d in row for im in d for p in im.tobytes()),
                  bytes(p for row in casts for d in row for im in d for p in im.tobytes()),
                  bytes(p for im in portraits for p in im.tobytes())]
        emitted=[bytes(map(int,re.findall(r'\d+',body)))for body in re.findall(r'= \{(.*?)\};',source,re.S)]
        assert emitted==expected,'Generated C pixels differ from authored images'
        for i,entry in enumerate(ROSTER):
            key=entry['name'].lower().replace(' ','_')
            for suffix,size,frames in (('walk',(64,64),fields[i]),('cast',(48,64),casts[i])):
                im=Image.open(OUT/f'{key}_{suffix}.png')
                assert im.size==size and im.mode=='P' and im.info['transparency']==0 and im.getpalette()==PAL
                for d,row in enumerate(frames):
                    for f,frame in enumerate(row):assert im.crop((f*16,d*16,f*16+16,d*16+16)).tobytes()==frame.tobytes()
        report.update({'emitted_c_pixel_parity':True,'exported_png_contract':True,'generated_pixel_bytes':sum(map(len,emitted))})
        # Syntax-only parsing of this isolated asset module, not a game build.
        completed=subprocess.run(['cc','-std=c99','-Wall','-Wextra','-Werror','-fsyntax-only',str(GEN/'covenant_art.c')],capture_output=True,text=True)
        report['c_syntax_only']={'passed':completed.returncode==0,'stderr':completed.stderr}
        assert completed.returncode==0,completed.stderr
    (ROOT/'validation.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items()if k!='hashes'},indent=2))
    if not manifest['validation']['passed']:sys.exit(1)


if __name__ == '__main__':main()
