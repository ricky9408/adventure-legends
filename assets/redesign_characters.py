"""Native 16px character authoring for the lantern-keeper art direction."""
from PIL import Image, ImageDraw


def mirror(art):
    art.im = art.im.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
    art.d = ImageDraw.Draw(art.im)
    return art


def keeper(Art, direction, frame, costume=0):
    a = Art(16, 16, 'transparent')
    lift = (0, 0, -1, 0)[frame]
    step = (0, -1, 0, 1)[frame]
    coats = [('teal0', 'teal1', 'teal2'), ('rose1', 'rose3', 'rose4'),
             ('blue0', 'blue1', 'blue3'), ('pine1', 'pine3', 'pine5'),
             ('wood1', 'wood3', 'wood5'), ('purple1', 'purple2', 'purple3')]
    dark, cloth, light = coats[costume % len(coats)]
    side = direction in ('left', 'right')
    for x, up in ((4, frame == 1), (9, frame == 3)):
        a.r((x, 12, x + 2, 14 - int(up)), 'ink')
        a.r((x, 14 - int(up), x + 3, 15 - int(up)), 'wood0')
        a.l([(x + 1, 14 - int(up)), (x + 2, 14 - int(up))], 'wood3')
    if side:
        tail = 7 + lift + step
        a.p([(7, 8 + lift), (4, tail), (1, tail - 2), (0, tail - 1),
             (2, tail + 2), (6, 10 + lift)], 'gold0')
        a.l([(1, tail), (4, tail + 1), (6, 9 + lift)], 'gold3')
    else:
        tail = 8 + lift + step
        a.p([(10, 8 + lift), (12, tail), (14, tail - 2), (15, tail),
             (13, tail + 2), (10, 10 + lift)], 'gold0')
        a.l([(11, 9 + lift), (13, tail + 1), (14, tail)], 'gold3')
    a.p([(5, 8 + lift), (10, 8 + lift), (12, 10 + lift),
         (11, 13 + lift), (4, 13 + lift), (3, 10 + lift)], 'ink')
    a.r((5, 9 + lift, 10, 12 + lift), dark)
    a.r((5, 9 + lift, 8, 11 + lift), cloth)
    a.l([(5, 10 + lift), (5, 11 + lift)], light)
    a.r((4, 12 + lift, 11, 12 + lift), dark)
    a.dot(8, 12 + lift, 'gold2')
    a.l([(9, 9 + lift), (6, 12 + lift)], 'wood0')
    a.dot(8, 10 + lift, 'wood4')
    a.r((3, 9 + lift + step, 3, 11 + lift + step), 'ink')
    a.dot(3, 10 + lift + step, 'skin2')
    a.r((12, 9 + lift - step, 12, 11 + lift - step), 'ink')
    a.dot(12, 10 + lift - step, 'skin1')
    a.r((2, 11 + lift, 4, 13 + lift), 'wood0')
    a.r((2, 11 + lift, 3, 12 + lift), 'wood3')
    a.dot(3, 11 + lift, 'gold3')
    if side:
        a.p([(4, 2 + lift), (6, 1 + lift), (10, 1 + lift), (12, 3 + lift),
             (12, 5 + lift), (13, 6 + lift), (13, 7 + lift), (11, 8 + lift),
             (10, 9 + lift), (5, 8 + lift), (3, 6 + lift), (3, 3 + lift)], 'ink')
        a.p([(8, 4 + lift), (11, 4 + lift), (11, 6 + lift),
             (12, 6 + lift), (12, 7 + lift), (10, 8 + lift), (7, 7 + lift)], 'skin2')
        a.p([(4, 3 + lift), (6, 2 + lift), (10, 2 + lift), (11, 3 + lift),
             (10, 4 + lift), (8, 4 + lift), (7, 6 + lift), (7, 8 + lift),
             (5, 7 + lift), (4, 6 + lift)], 'fire0')
        a.l([(5, 3 + lift), (6, 2 + lift), (9, 2 + lift)], 'fire2')
        a.l([(5, 4 + lift), (7, 3 + lift), (9, 3 + lift)], 'fire1')
        a.dot(6, 2 + lift, 'fire3')
        a.dot(11, 5 + lift, 'ink')
        a.dot(8, 6 + lift, 'skin1')
        a.r((7, 9 + lift, 10, 9 + lift), 'gold2')
        a.dot(9, 9 + lift, 'gold4')
        a.r((8 + step, 10 + lift, 9 + step, 11 + lift), cloth)
        a.dot(9 + step, 12 + lift, 'skin2')
        if direction == 'left':
            mirror(a)
    else:
        a.p([(3, 3 + lift), (5, 1 + lift), (10, 1 + lift), (12, 3 + lift),
             (12, 7 + lift), (10, 9 + lift), (5, 9 + lift), (3, 7 + lift)], 'ink')
        if direction == 'down':
            a.r((4, 4 + lift, 11, 7 + lift), 'skin1')
            a.r((5, 4 + lift, 10, 8 + lift), 'skin2')
            a.p([(4, 3 + lift), (6, 2 + lift), (10, 2 + lift), (11, 3 + lift),
                 (11, 5 + lift), (9, 4 + lift), (8, 3 + lift), (6, 4 + lift),
                 (4, 5 + lift)], 'fire0')
            a.l([(5, 3 + lift), (7, 2 + lift), (9, 2 + lift)], 'fire2')
            a.dot(6, 2 + lift, 'fire3')
            a.dot(5, 6 + lift, 'ink')
            a.dot(10, 6 + lift, 'ink')
            a.dot(7, 8 + lift, 'skin0')
        else:
            a.p([(4, 3 + lift), (6, 2 + lift), (10, 2 + lift), (11, 4 + lift),
                 (11, 7 + lift), (9, 8 + lift), (5, 7 + lift)], 'fire0')
            a.p([(5, 3 + lift), (7, 2 + lift), (10, 3 + lift), (9, 4 + lift),
                 (7, 4 + lift), (6, 6 + lift), (4, 5 + lift)], 'fire1')
            a.l([(6, 2 + lift), (8, 2 + lift)], 'fire2')
            a.r((6, 10 + lift, 9, 11 + lift), dark)
        a.r((5, 9 + lift, 10, 9 + lift), 'gold2')
        a.dot(5, 9 + lift, 'gold4')
    if costume:
        if costume == 1:
            a.p([(4, 9), (3, 13), (1, 14), (12, 14), (11, 9)], dark)
            a.l([(4, 13), (10, 13)], cloth)
            a.dot(8, 10, 'gold3')
        elif costume == 2:
            a.p([(3, 3), (5, 1), (10, 1), (12, 3), (14, 4), (1, 4)], 'wood0')
            a.l([(3, 3), (12, 3)], 'wood4')
            a.r((6, 1, 9, 2), 'wood3')
        elif costume == 3:
            a.p([(10, 3), (11, 0), (14, 0), (13, 2)], 'pine3')
            a.dot(12, 1, 'leaflight')
            a.r((1, 10, 4, 13), 'wood3')
        elif costume == 4:
            a.l([(12, 9), (14, 9), (14, 11)], 'wood0')
            a.r((12, 11, 15, 14), 'wood0')
            a.r((13, 12, 14, 13), 'gold3')
            a.dot(13, 12, 'gold4')
        else:
            a.p([(2, 6), (3, 2), (7, 0), (11, 2), (13, 6),
                 (11, 5), (9, 3), (5, 3), (3, 6)], dark)
            a.l([(3, 3), (7, 1), (10, 3)], cloth)
    return a


def emberfox(Art, direction, frame):
    a = Art(16, 16, 'transparent')
    lift = (0, 0, -1, 0)[frame]
    wag = (0, -1, 0, 1)[frame]
    side = direction in ('left', 'right')
    if side:
        a.p([(5, 11), (2, 11), (0, 8), (1, 5 + wag), (0, 3 + wag),
             (3, 5 + wag), (4, 2 + wag), (5, 6), (4, 9), (7, 10)], 'ink')
        a.p([(4, 10), (2, 9), (1, 7), (2, 5 + wag), (3, 7),
             (4, 4 + wag), (4, 8), (6, 10)], 'fire1')
        a.l([(2, 7), (3, 8), (3, 10)], 'fire3')
        a.dot(2, 6 + wag, 'gold4')
        a.p([(4, 10 + lift), (8, 8 + lift), (11, 10 + lift),
             (10, 13 + lift), (5, 13 + lift), (3, 12 + lift)], 'ink')
        a.r((5, 10 + lift, 9, 12 + lift), 'fire1')
        a.l([(5, 10 + lift), (8, 9 + lift), (10, 10 + lift)], 'fire2')
        for x, up in ((5, frame == 1), (10, frame == 3)):
            a.r((x, 12, x + 1, 14 - int(up)), 'ink')
            a.dot(x, 13 - int(up), 'fire3')
        a.p([(7, 6 + lift), (7, 1 + lift), (9, 2 + lift), (10, 4 + lift),
             (12, 2 + lift), (13, 3 + lift), (13, 6 + lift), (15, 7 + lift),
             (15, 9 + lift), (12, 11 + lift), (9, 10 + lift), (7, 8 + lift)], 'ink')
        a.p([(8, 6 + lift), (8, 3 + lift), (10, 5 + lift), (12, 4 + lift),
             (12, 7 + lift), (14, 8 + lift), (12, 10 + lift), (9, 9 + lift)], 'fire2')
        a.l([(11, 9 + lift), (13, 9 + lift), (14, 8 + lift)], 'white')
        a.dot(12, 7 + lift, 'ink')
        a.dot(15, 8 + lift, 'ink')
        a.dot(8, 3 + lift, 'rose2')
        if direction == 'left':
            mirror(a)
    else:
        a.p([(10, 12), (13, 10), (12, 7 + wag), (14, 4 + wag),
             (15, 6 + wag), (15, 12), (12, 14), (9, 13)], 'ink')
        a.p([(11, 12), (14, 10), (13, 8 + wag), (14, 6 + wag),
             (14, 12), (12, 13)], 'fire1')
        a.l([(14, 8 + wag), (14, 10), (12, 12)], 'fire3')
        for x, up in ((4, frame == 1), (9, frame == 3)):
            a.r((x, 11, x + 1, 14 - int(up)), 'ink')
            a.dot(x, 13 - int(up), 'fire2')
        a.p([(3, 8 + lift), (10, 8 + lift), (11, 12 + lift),
             (9, 13 + lift), (4, 13 + lift), (2, 11 + lift)], 'ink')
        a.r((4, 9 + lift, 9, 12 + lift), 'fire1')
        a.p([(2, 6 + lift), (2, 1 + lift), (4, 2 + lift), (6, 4 + lift),
             (8, 4 + lift), (10, 1 + lift), (12, 2 + lift), (12, 7 + lift),
             (10, 10 + lift), (7, 12 + lift), (4, 10 + lift), (2, 8 + lift)], 'ink')
        a.p([(3, 6 + lift), (3, 3 + lift), (5, 5 + lift), (8, 5 + lift),
             (10, 3 + lift), (11, 4 + lift), (11, 7 + lift),
             (9, 9 + lift), (7, 11 + lift), (4, 9 + lift)], 'fire2')
        a.l([(4, 5 + lift), (6, 5 + lift), (7, 6 + lift), (9, 5 + lift)], 'fire3')
        if direction == 'down':
            a.p([(4, 8 + lift), (6, 9 + lift), (7, 8 + lift), (9, 9 + lift),
                 (10, 8 + lift), (9, 10 + lift), (7, 11 + lift), (5, 10 + lift)], 'white')
            a.dot(4, 7 + lift, 'ink')
            a.dot(10, 7 + lift, 'ink')
            a.dot(7, 9 + lift, 'ink')
        else:
            a.p([(4, 7 + lift), (7, 6 + lift), (10, 7 + lift),
                 (8, 10 + lift), (6, 10 + lift)], 'fire1')
            a.dot(7, 8 + lift, 'fire2')
    return a


def leafseed(Art, direction, frame):
    a = Art(16, 16, 'transparent')
    bob = (0, -1, 0, 1)[frame]
    fold = (0, 1, -1, 0)[frame]
    side = direction in ('left', 'right')
    a.l([(6, 11 + bob), (4 - fold, 14), (2 - fold, 14)], 'pine1')
    a.l([(9, 11 + bob), (10 + fold, 14), (12 + fold, 13)], 'pine2')
    a.dot(3 - fold, 14, 'moss3')
    a.p([(5, 7 + bob), (8, 6 + bob), (11, 8 + bob), (11, 11 + bob),
         (8, 13 + bob), (5, 12 + bob), (3, 10 + bob)], 'pine0')
    a.p([(5, 8 + bob), (8, 7 + bob), (10, 8 + bob), (10, 11 + bob),
         (8, 12 + bob), (5, 11 + bob), (4, 10 + bob)], 'moss1')
    a.p([(5, 8 + bob), (8, 7 + bob), (9, 8 + bob), (8, 10 + bob),
         (5, 10 + bob)], 'moss3')
    a.dot(6, 8 + bob, 'leafwarm')
    a.p([(7, 6 + bob), (4, 3 + bob + fold), (1, 3 + bob + fold),
         (0, 5 + bob + fold), (3, 7 + bob), (6, 8 + bob)], 'pine0')
    a.p([(6, 6 + bob), (3, 4 + bob + fold), (1, 4 + bob + fold),
         (3, 6 + bob), (5, 7 + bob)], 'pine4')
    a.l([(2, 4 + bob + fold), (4, 5 + bob), (6, 6 + bob)], 'leaflight')
    a.p([(7, 6 + bob), (8, 2 + bob), (12, 1 + bob),
         (14, 2 + bob), (13, 5 + bob - fold), (10, 7 + bob)], 'pine0')
    a.p([(8, 6 + bob), (9, 3 + bob), (12, 2 + bob), (13, 2 + bob),
         (12, 4 + bob - fold), (10, 6 + bob)], 'pine3')
    a.l([(9, 5 + bob), (11, 3 + bob), (12, 2 + bob)], 'pine5')
    if direction == 'down':
        a.dot(5, 10 + bob, 'ink')
        a.dot(9, 10 + bob, 'ink')
        a.dot(7, 12 + bob, 'gold4')
    elif direction == 'up':
        a.l([(7, 8 + bob), (7, 11 + bob)], 'moss0')
        a.dot(8, 10 + bob, 'moss2')
    else:
        a.dot(10, 10 + bob, 'ink')
        a.dot(11, 11 + bob, 'gold4')
        a.l([(4, 8 + bob), (5, 10 + bob)], 'pine2')
        if direction == 'left':
            mirror(a)
    return a


def flame(Art, frame, shape=0):
    a = Art(16, 16, 'transparent')
    lean = (-1, 1)[frame & 1]
    tip = 8 + lean + (shape % 3 - 1)
    a.p([(tip, 1), (tip + 1, 4), (11, 6), (12, 4), (14, 8),
         (14, 11), (12, 14), (8, 15), (4, 13), (2, 10),
         (3, 6), (5, 8), (6, 5)], 'fire0')
    a.p([(tip, 3), (9, 7), (11, 8), (12, 6), (13, 9), (12, 12),
         (9, 14), (5, 12), (4, 9), (6, 10), (7, 7)], 'fire1')
    a.p([(8 + lean, 6), (9, 9), (11, 10), (10, 13), (7, 13),
         (5, 10), (7, 11)], 'fire3')
    a.p([(8, 9), (10, 12), (8, 13), (7, 12)], 'gold4')
    a.dot(8, 12, 'white')
    return a


def projectile(Art):
    a = Art(16, 16, 'transparent')
    # Enemy shots share this unrotated slot, so a tail would imply a false heading.
    a.p([(6, 2), (9, 2), (11, 3), (12, 4), (13, 6), (13, 9),
         (12, 11), (11, 12), (9, 13), (6, 13), (4, 12), (3, 11),
         (2, 9), (2, 6), (3, 4), (4, 3)], 'fire0')
    a.p([(6, 3), (9, 3), (12, 6), (12, 9), (9, 12), (6, 12),
         (3, 9), (3, 6)], 'fire2')
    a.p([(6, 5), (9, 5), (10, 6), (10, 9), (9, 10), (6, 10),
         (5, 9), (5, 6)], 'fire3')
    a.r((6, 6, 9, 9), 'gold4')
    a.r((7, 7, 8, 8), 'white')
    for bounds in ((7, 0, 8, 0), (15, 7, 15, 8),
                   (7, 15, 8, 15), (0, 7, 0, 8)):
        a.r(bounds, 'fire3')
    return a


def windsail(Art, direction, frame):
    a = Art(16, 16, 'transparent')
    bob = (0, -1, 0, 1)[frame]
    spread = (0, 1, 2, 1)[frame]
    side = direction in ('left', 'right')
    def p(points, color):
        a.p([(x, y + bob) for x, y in points], color)
    def line(points, color):
        a.l([(x, y + bob) for x, y in points], color)
    if side:
        p([(7, 7), (2, 2 + spread), (0, 4 + spread), (2, 8), (6, 10)], 'purple1')
        p([(6, 7), (2, 3 + spread), (1, 4 + spread), (3, 7), (6, 9)], 'white')
        line([(2, 5 + spread), (4, 7), (5, 8)], 'purple3')
        p([(6, 10), (3, 12), (0, 12), (2, 14), (5, 13), (8, 10)], 'purple1')
        line([(1, 12), (3, 13), (6, 11)], 'gold3')
        p([(9, 3), (12, 5), (14, 7), (13, 9), (10, 11), (7, 9), (7, 6)], 'purple1')
        p([(9, 4), (11, 5), (13, 7), (12, 9), (10, 10), (8, 8), (8, 6)], 'flower1')
        line([(9, 4), (10, 6), (10, 8)], 'white')
        a.dot(12, 7 + bob, 'ink')
        p([(10, 3), (9, 0), (11, 1), (12, 4)], 'white')
        if direction == 'left':
            mirror(a)
    else:
        p([(6, 6), (2, 2 + spread), (0, 4 + spread), (1, 8), (5, 10), (7, 8)], 'purple1')
        p([(6, 6), (3, 3 + spread), (1, 4 + spread), (2, 7), (5, 9)], 'white')
        line([(2, 5 + spread), (4, 6), (5, 8)], 'purple3')
        p([(9, 6), (13, 2 + spread), (15, 4 + spread), (14, 8), (10, 10), (8, 8)], 'purple1')
        p([(9, 6), (12, 3 + spread), (14, 4 + spread), (13, 7), (10, 9)], 'white')
        line([(13, 5 + spread), (11, 6), (10, 8)], 'purple3')
        turn = (0, 1, 0, -1)[frame]
        line([(6, 10), (5, 13), (2 + turn, 14)], 'purple1')
        line([(6, 10), (6, 13), (3 + turn, 14)], 'gold3')
        line([(9, 10), (10, 13), (12 - turn, 14)], 'purple1')
        line([(9, 10), (9, 13), (12 - turn, 13)], 'white')
        p([(7, 3), (9, 5), (10, 8), (8, 11), (6, 10), (5, 7)], 'purple1')
        p([(7, 4), (8, 5), (9, 8), (8, 10), (6, 8), (6, 6)], 'flower1')
        p([(6, 4), (4, 1), (5, 0), (7, 3)], 'white')
        p([(9, 4), (11, 1), (10, 0), (8, 3)], 'white')
        if direction == 'down':
            a.dot(6, 7 + bob, 'ink')
            a.dot(9, 7 + bob, 'ink')
            a.dot(7, 9 + bob, 'gold2')
        else:
            line([(7, 5), (7, 8), (8, 9)], 'purple3')
    return a


def hearthwarden(Art):
    a = Art(32, 32, 'transparent')
    a.p([(7, 22), (13, 23), (13, 28), (11, 30), (4, 30), (4, 28), (7, 26)], 'ink')
    a.p([(20, 23), (26, 22), (26, 27), (29, 29), (28, 31), (21, 30), (19, 27)], 'ink')
    a.p([(8, 24), (12, 24), (11, 28), (6, 29), (8, 27)], 'stone2')
    a.p([(21, 24), (25, 24), (24, 27), (27, 29), (22, 28)], 'stone2')
    a.l([(7, 28), (10, 28)], 'stone4')
    a.l([(22, 28), (25, 29)], 'stone3')
    a.p([(7, 11), (11, 8), (22, 8), (27, 12), (27, 22),
         (23, 27), (12, 27), (7, 23), (5, 17)], 'ink')
    a.p([(8, 12), (12, 9), (21, 9), (25, 13), (25, 21),
         (22, 25), (12, 25), (9, 22), (7, 17)], 'stone1')
    a.p([(9, 12), (13, 10), (20, 10), (23, 13), (22, 19),
         (18, 23), (12, 23), (9, 19)], 'stone2')
    a.l([(10, 12), (13, 11), (18, 11)], 'stone4')
    a.p([(6, 10), (2, 12), (0, 18), (2, 23), (6, 24), (9, 20), (9, 13)], 'ink')
    a.p([(5, 12), (3, 13), (2, 18), (3, 21), (6, 22), (7, 19), (7, 14)], 'stone2')
    a.l([(3, 14), (3, 17)], 'stone4')
    a.l([(3, 21), (6, 21)], 'stone0')
    a.p([(24, 11), (29, 10), (31, 14), (30, 22), (27, 24), (24, 21)], 'ink')
    a.p([(26, 12), (29, 12), (30, 15), (29, 20), (27, 22), (25, 20)], 'stone2')
    a.l([(27, 13), (29, 13)], 'stone4')
    a.p([(9, 5), (12, 2), (20, 2), (24, 5), (24, 10), (21, 13),
         (12, 12), (8, 9)], 'ink')
    a.p([(10, 5), (13, 3), (20, 3), (22, 6), (22, 10),
         (20, 11), (12, 10), (10, 8)], 'stone2')
    a.l([(12, 5), (14, 4), (19, 4), (21, 6)], 'stone4')
    a.r((11, 7, 22, 9), 'stone0')
    a.r((13, 8, 14, 9), 'gold2')
    a.r((19, 8, 20, 9), 'gold2')
    a.dot(13, 8, 'gold4')
    a.dot(19, 8, 'gold4')
    a.p([(15, 13), (20, 14), (22, 18), (20, 23), (15, 24),
         (11, 21), (11, 16)], 'stone0')
    a.p([(15, 14), (19, 15), (21, 18), (19, 22), (15, 23),
         (12, 20), (12, 17)], 'wood1')
    a.p([(16, 15), (16, 18), (19, 17), (20, 19), (18, 22),
         (15, 22), (13, 20), (14, 17)], 'fire1')
    a.p([(16, 18), (18, 19), (18, 21), (15, 21), (15, 20)], 'gold3')
    a.dot(16, 20, 'gold4')
    for x, y, width in ((9, 3, 5), (18, 2, 5), (1, 12, 5), (24, 10, 6), (8, 22, 4)):
        a.p([(x, y), (x + 2, y - 1), (x + width, y),
             (x + width - 1, y + 2), (x + 1, y + 3)], 'pine1')
        a.l([(x + 1, y), (x + 3, y), (x + width - 1, y + 1)], 'moss2')
        a.dot(x + 2, y, 'moss3')
    a.l([(10, 3), (8, 0), (6, 1)], 'wood1')
    a.l([(21, 3), (24, 1), (26, 1)], 'wood2')
    a.dot(25, 0, 'pine4')
    a.dot(26, 1, 'pine5')
    a.l([(10, 14), (9, 17), (10, 20)], 'stone0')
    a.l([(23, 15), (24, 18), (23, 21)], 'stone0')
    a.dot(24, 4, 'flower1')
    a.dot(25, 3, 'flower0')
    return a


# The role and clothing are explicit; random palette swaps cannot establish identity.
RESIDENTS = {
    'reed': {
        'SMITH': ('broad', 'scarf', 'wood2', 'wood4', 'skin1', 'hammer'),
        'WEAVER': ('dress', 'bun', 'purple2', 'water3', 'skin2', 'spool'),
        'WARDEN': ('tall', 'brim', 'teal0', 'leaflight', 'skin1', 'staff'),
        'REST_KEEPER': ('round', 'whitecurl', 'rose2', 'gold3', 'skin2', 'bread'),
        'APPRENTICE': ('small', 'tousle', 'pine3', 'rose4', 'skin1', 'rod'),
        'MERCHANT': ('coat', 'cap', 'wood3', 'plaster', 'skin2', 'basket')},
    'north': {
        'EDDA': ('coat', 'braid', 'rose2', 'gold3', 'skin1', 'rope'),
        'TOVE': ('broad', 'scarf', 'wood2', 'gold3', 'skin2', 'pot'),
        'NERI': ('tall', 'cap', 'water1', 'water4', 'skin1', 'wrench'),
        'PELL': ('small', 'tousle', 'pine3', 'gold3', 'skin2', 'parcel'),
        'IVEN': ('dress', 'whitecurl', 'purple2', 'gold3', 'skin1', 'chart')},
    'south': {
        'GUIDE': ('tall', 'brim', 'water1', 'gold3', 'skin1', 'chart'),
        'TAILOR': ('dress', 'bun', 'fire1', 'plaster', 'skin0', 'spool'),
        'MARKET': ('round', 'brim', 'purple2', 'wood4', 'skin1', 'basket'),
        'RAIN': ('small', 'bob', 'pine3', 'water4', 'skin2', 'staff'),
        'PORTER': ('broad', 'scarf', 'wood3', 'gold3', 'skin0', 'parcel'),
        'CURATOR': ('coat', 'whitecurl', 'rose2', 'gold4', 'skin1', 'book')},
    'magma': {
        'RESSA': ('dress', 'bun', 'rose2', 'plaster', 'skin1', 'pot'),
        'NEMI': ('broad', 'scarf', 'wood2', 'fire2', 'skin0', 'bowl'),
        'OMI': ('round', 'whitecurl', 'water1', 'plaster', 'skin1', 'jug'),
        'TAVI': ('small', 'bob', 'teal0', 'water3', 'skin2', 'book'),
        'SEN': ('tall', 'brim', 'purple2', 'gold3', 'skin1', 'staff'),
        'PELL': ('small', 'tousle', 'pine3', 'gold3', 'skin2', 'parcel')},
    'underwater': {
        'KEEPER': ('coat', 'shell', 'water1', 'gold3', 'skin2', 'book'),
        'SHELLWRIGHT': ('broad', 'scarf', 'rose2', 'water3', 'skin1', 'hammer'),
        'COOK': ('round', 'chef', 'stone4', 'rose4', 'skin2', 'bowl'),
        'FRAMER': ('tall', 'cap', 'wood3', 'water4', 'skin1', 'frame'),
        'DANCER': ('dress', 'ribbon', 'rose3', 'water4', 'skin2', 'ribbon')},
    'return': {
        'GARDENER': ('dress', 'brim', 'pine3', 'leafwarm', 'skin1', 'seed'),
        'BELLMAKER': ('broad', 'scarf', 'wood3', 'silver', 'skin2', 'bell'),
        'PORTER': ('coat', 'cap', 'rose2', 'gold3', 'skin1', 'parcel'),
        'WEAVER': ('tall', 'bun', 'water1', 'gold3', 'skin0', 'spool'),
        'GUIDE': ('small', 'tousle', 'purple2', 'rose4', 'skin2', 'chart')},
    'horizons': {
        'HOST': ('round', 'braid', 'water1', 'water4', 'skin1', 'cup'),
        'PORTER': ('broad', 'scarf', 'wood3', 'gold3', 'skin0', 'parcel'),
        'STORYTELLER': ('dress', 'ribbon', 'rose2', 'gold3', 'skin2', 'ribbon'),
        'SCRIBE': ('coat', 'bun', 'teal0', 'white', 'skin1', 'book'),
        'JOINER': ('tall', 'cap', 'wood2', 'gold3', 'skin2', 'hammer')},
    'covenants': {
        'STEWARD': ('coat', 'shell', 'teal0', 'water4', 'skin2', 'chart'),
        'GROWER': ('broad', 'brim', 'pine3', 'leafwarm', 'skin1', 'basket'),
        'KILN_KEEPER': ('dress', 'bun', 'rose2', 'plaster', 'skin2', 'pot'),
        'WALKER': ('tall', 'hood', 'wood3', 'gold3', 'skin0', 'staff'),
        'REPAIRER': ('small', 'scarf', 'water1', 'gold3', 'skin1', 'wrench'),
        'SEED_KEEPER': ('round', 'braid', 'rose2', 'pine5', 'skin2', 'seed'),
        'FERRY_KEEPER': ('tall', 'cap', 'water1', 'water4', 'skin1', 'oar'),
        'WATCHER': ('coat', 'hood', 'rose2', 'gold3', 'skin2', 'lantern'),
        'NEIGHBOR': ('round', 'whitecurl', 'purple2', 'gold3', 'skin1', 'bread'),
        'PASSENGER': ('small', 'bob', 'pine2', 'rose4', 'skin2', 'parcel')},
    'village': {
        'ELDER': ('round', 'whitecurl', 'purple2', 'gold3', 'skin2', 'staff')},
}


def resident(Art, region, name, work=False, step=0):
    build, hair, coat, trim, skin, tool = RESIDENTS[region][name]
    a = Art(16, 16, 'transparent')
    top = 4 if build == 'small' else 2 if build == 'tall' else 3
    cheek = top + 5
    a.e((3, 13, 12, 15), 'shadow')
    for x, rise in ((4, step == 1), (9, step == 2)):
        a.r((x, 12, x + 2, 14 - int(rise)), 'ink')
        a.r((x, 14 - int(rise), x + 3, 14 - int(rise)), 'wood2')
    if build == 'dress':
        outline = [(5, 8), (10, 8), (11, 10), (13, 14), (3, 14), (4, 10)]
        body = [(5, 9), (10, 9), (11, 12), (12, 13), (4, 13)]
    elif build == 'broad':
        outline = [(4, 8), (11, 8), (13, 10), (12, 13), (3, 13), (2, 10)]
        body = [(4, 9), (11, 9), (12, 11), (11, 12), (4, 12), (3, 11)]
    elif build == 'round':
        outline = [(5, 8), (10, 8), (13, 11), (12, 13), (4, 14), (2, 12), (3, 10)]
        body = [(5, 9), (10, 9), (12, 11), (11, 12), (4, 13), (3, 11)]
    elif build == 'small':
        outline = [(5, 9), (10, 9), (12, 11), (11, 13), (4, 13), (3, 11)]
        body = [(5, 10), (10, 10), (11, 12), (4, 12)]
    else:
        outline = [(5, 7), (10, 7), (12, 10), (11, 14), (4, 14), (3, 10)]
        body = [(5, 8), (10, 8), (11, 10), (10, 13), (5, 13), (4, 10)]
    a.p(outline, 'ink')
    a.p(body, coat)
    if tool in ('pot', 'bowl', 'hammer', 'wrench', 'jug'):
        a.p([(6, 8), (9, 8), (10, 13), (5, 13)], trim)
        a.l([(6, 9), (8, 9)], 'white' if trim == 'plaster' else 'wood4')
    else:
        a.l([(5, 9), (9, 12)], trim)
        a.dot(6, 9, 'gold4')
    left = 8 if work else 9 if step == 1 else 11 if step == 2 else 10
    right = 8 if work else 11 if step == 1 else 9 if step == 2 else 11
    a.r((2, left, 3, left + 1), 'skin0')
    a.dot(2, left, skin)
    a.r((11, right, 12, right + 1), 'skin0')
    a.dot(12, right, skin)
    a.p([(5, top), (9, top), (11, top + 2), (11, cheek - 1),
         (9, cheek + 1), (6, cheek + 1), (4, cheek - 1), (4, top + 2)], 'ink')
    a.r((5, top + 2, 10, cheek - 1), skin)
    a.r((6, cheek, 9, cheek), 'skin1' if skin == 'skin2' else 'skin0')
    a.dot(6, top + 3, 'ink')
    a.dot(9, top + 3, 'ink')
    a.dot(7, cheek, 'skin0')
    if hair in ('bun', 'braid', 'bob', 'tousle'):
        a.p([(4, top + 2), (4, top), (6, top - 1), (9, top - 1),
             (11, top + 1), (11, top + 3), (9, top + 2), (8, top + 1),
             (6, top + 2)], 'wood0')
        a.l([(5, top), (8, top), (9, top + 1)], 'wood2')
        if hair == 'bun':
            a.e((9, top - 2, 13, top + 2), 'wood0')
            a.l([(10, top - 1), (12, top)], 'wood3')
            a.dot(12, top + 1, trim)
        elif hair == 'braid':
            a.l([(11, top + 2), (12, cheek), (11, cheek + 2)], 'wood0', 2)
            a.dot(11, cheek + 1, 'wood3')
            a.dot(11, cheek + 2, trim)
        elif hair == 'bob':
            a.r((3, top + 2, 4, cheek), 'wood0')
            a.r((11, top + 2, 12, cheek), 'wood0')
            a.dot(3, top + 3, 'wood3')
        else:
            a.p([(3, top), (5, top - 1), (6, top - 2), (8, top - 1),
                 (10, top - 2), (11, top + 1)], 'wood0')
            a.dot(6, top - 1, 'wood3')
    elif hair == 'whitecurl':
        a.p([(3, top + 2), (4, top), (6, top - 1), (9, top - 1),
             (11, top), (12, top + 2), (11, top + 4),
             (10, top + 2), (5, top + 2), (4, top + 4)], 'silver')
        a.l([(4, top + 1), (5, top), (8, top), (10, top + 1)], 'white')
        if region == 'village':
            a.p([(5, cheek), (7, cheek - 1), (8, cheek),
                 (10, cheek - 1), (9, cheek + 2), (7, cheek + 3)], 'white')
    elif hair == 'brim':
        a.p([(1, top + 1), (4, top), (5, top - 2), (10, top - 2),
             (11, top), (14, top + 1), (14, top + 2), (1, top + 2)], 'wood0')
        a.p([(3, top + 1), (5, top), (6, top - 1), (9, top - 1),
             (10, top), (12, top + 1)], 'wood4')
        a.l([(4, top + 1), (11, top + 1)], 'gold3')
    elif hair == 'scarf':
        a.p([(4, top + 2), (4, top), (7, top - 1), (10, top),
             (11, top + 2)], 'ink')
        a.l([(5, top), (8, top), (10, top + 1)], trim)
        a.l([(4, top + 2), (10, top + 2)], coat)
        a.p([(3, top + 1), (1, top + 2), (2, top + 4), (3, top + 3)], trim)
    elif hair == 'hood':
        a.p([(3, top + 3), (4, top), (7, top - 2), (11, top),
             (12, top + 4), (11, cheek), (10, top + 2), (8, top + 1),
             (5, top + 2), (4, cheek)], 'wood0')
        a.l([(4, top + 1), (7, top - 1), (10, top + 1)], coat)
        a.dot(6, top, trim)
    elif hair == 'chef':
        a.e((3, top - 3, 8, top + 1), 'silver')
        a.e((7, top - 3, 12, top + 1), 'silver')
        a.e((4, top - 3, 10, top), 'white')
        a.r((5, top + 1, 10, top + 2), 'white')
        a.l([(5, top + 2), (10, top + 2)], trim)
    elif hair == 'shell':
        a.p([(3, top + 1), (4, top - 1), (7, top - 2), (10, top - 1),
             (12, top + 1), (10, top + 2), (5, top + 2)], 'stone4')
        a.l([(5, top), (7, top - 1), (10, top + 1)], 'white')
        a.dot(7, top + 1, coat)
    elif hair == 'ribbon':
        a.r((4, top, 10, top + 2), 'wood0')
        a.p([(4, top + 1), (1, top - 1), (1, top + 2), (4, top + 2),
             (5, top - 2), (7, top - 2), (6, top + 1)], trim)
        a.dot(5, top + 1, 'gold4')
    else:
        a.p([(3, top + 1), (5, top - 1), (10, top - 1), (11, top + 1),
             (13, top + 2), (4, top + 2)], 'ink')
        a.r((5, top, 10, top + 1), coat)
        a.l([(4, top + 2), (12, top + 2)], trim)
    held_tool(a, tool, work, trim, step)
    return a


def held_tool(a, tool, work, trim, step=0):
    y = 6 if work else 8 if step == 1 else 10 if step == 2 else 9
    if tool in ('staff', 'rod', 'oar'):
        a.l([(13, 4), (13, 14)], 'wood0')
        a.l([(13, 5), (13, 12)], 'wood4')
        if tool == 'oar':
            a.p([(12, 0), (14, 0), (15, 4), (13, 6), (12, 4)], 'wood2')
            a.l([(13, 1), (14, 4)], 'wood5')
        elif tool == 'staff':
            a.p([(12, 4), (12, 2), (14, 1), (15, 3), (14, 4)], 'gold2')
            a.dot(13, 2, 'gold4')
        a.dot(12, 10, 'skin2')
    elif tool in ('hammer', 'wrench'):
        a.l([(13, y - 2), (12, y + 4)], 'wood0', 2)
        a.l([(13, y), (12, y + 3)], 'wood4')
        a.r((11, y - 3, 15, y - 1), 'stone0')
        a.l([(11, y - 3), (14, y - 3)], 'silver')
        if tool == 'wrench':
            a.dot(13, y - 3, 'transparent')
        a.dot(12, y + 1, 'skin2')
    elif tool == 'rope':
        a.e((0, y - 1, 5, y + 4), 'wood0')
        a.e((1, y, 4, y + 3), 'gold2')
        a.e((2, y + 1, 3, y + 2), 'transparent')
        a.l([(2, y + 4), (3, 14), (5, 14)], 'wood4')
        a.dot(1, y, 'gold4')
    elif tool in ('book', 'chart'):
        a.p([(11, y - 1), (14, y - 1), (15, y + 1),
             (15, y + 4), (11, y + 4)], 'wood0')
        a.r((12, y, 14, y + 3), 'plaster')
        a.l([(12, y + 1), (13, y + 1)], 'water1')
        a.dot(13, y + 3, 'rose3' if tool == 'chart' else 'wood3')
    elif tool in ('basket', 'parcel', 'seed'):
        a.r((0, y, 4, y + 4), 'wood0')
        a.r((1, y, 3, y + 3), 'wood3' if tool != 'seed' else 'plaster')
        if tool == 'parcel':
            a.l([(0, y + 1), (4, y + 1)], 'gold2')
            a.l([(2, y), (2, y + 3)], 'gold3')
        else:
            a.l([(1, y - 1), (3, y - 1)], 'wood0')
            a.dot(2, y, 'pine5')
            a.dot(3, y + 1, 'pine3')
            a.l([(1, y + 3), (3, y + 3)], 'wood2')
    elif tool == 'spool':
        a.r((11, y, 14, y + 3), 'water2')
        a.r((10, y - 1, 15, y - 1), 'wood0')
        a.r((10, y + 4, 15, y + 4), 'wood0')
        a.l([(11, y), (14, y)], 'watergleam')
        a.l([(11, y + 2), (14, y + 2)], 'water4')
    elif tool in ('pot', 'jug', 'cup', 'bowl', 'bread', 'bell'):
        yy = y + 1
        a.p([(0, yy), (5, yy), (5, yy + 2), (4, yy + 4), (1, yy + 4),
             (0, yy + 2)], 'wood0')
        a.p([(1, yy + 1), (4, yy + 1), (4, yy + 3), (2, yy + 3)],
            'water2' if tool in ('jug', 'cup') else 'wood3' if tool == 'bread' else 'fire2')
        a.l([(1, yy), (4, yy)], 'gold3')
        if tool == 'jug':
            a.r((2, yy - 2, 3, yy), 'water2')
            a.dot(2, yy - 2, 'water4')
        elif tool == 'bread':
            a.p([(1, yy), (2, yy - 1), (4, yy), (4, yy + 1), (1, yy + 1)], 'wood4')
            a.dot(2, yy, 'gold4')
        elif tool == 'bell':
            a.p([(2, yy - 1), (3, yy - 1), (4, yy + 2), (5, yy + 3),
                 (0, yy + 3), (1, yy + 1)], 'gold2')
            a.dot(2, yy, 'gold4')
    elif tool == 'lantern':
        a.l([(12, y - 2), (14, y - 2), (14, y)], 'wood0')
        a.r((11, y, 15, y + 4), 'ink')
        a.r((12, y + 1, 14, y + 3), 'gold2')
        a.dot(13, y + 2, 'gold4')
    elif tool == 'frame':
        a.r((11, y - 2, 15, y + 3), 'wood2')
        a.r((12, y - 1, 14, y + 2), 'transparent')
        a.l([(11, y - 2), (14, y - 2)], 'wood5')
    elif tool == 'ribbon':
        a.l([(11, y), (14, y - 2), (15, y - 1)], 'skin1')
        a.l([(14, y - 3), (12, y - 4), (14, y - 5)], trim)
        a.l([(3, 11), (1, 12), (0, 10)], trim)
