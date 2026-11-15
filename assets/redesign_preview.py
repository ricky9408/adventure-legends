#!/usr/bin/env python3
"""Render authoring reviews at native size and integer zoom, without ROM writes."""
from pathlib import Path
import importlib
import json
from PIL import Image, ImageDraw
import generate_assets as base

OUT = Path(__file__).resolve().parent / 'redesign'
DIRECTIONS = ('down', 'up', 'left', 'right')
REGIONS = [('Reedhaven', 'generate_region'), ('Hearthwake', 'generate_northern_region'),
           ('Sunlace', 'southern_region.sprite_art'), ('Kilnstep', 'generate_magma_region'),
           ('Nacreway', 'generate_underwater_region'), ('Homecoming', 'generate_return_region'),
           ('Horizons', 'generate_horizons_region'), ('Covenants', 'generate_covenants_region')]


def paste(image, art, xy):
    mask = Image.frombytes('L', art.im.size, bytes(255 if p else 0 for p in art.im.tobytes()))
    image.paste(art.im.convert('RGB'), xy, mask)


def save_zoom(image, key, scale=4):
    image.save(OUT / f'{key}_native.png')
    image.resize((image.width * scale, image.height * scale), Image.Resampling.NEAREST).save(OUT / f'{key}_{scale}x.png')


def main():
    OUT.mkdir(exist_ok=True)
    rows = [('Traveler', [base.hero(d, 0) for d in DIRECTIONS]),
            ('Companions', [base.fox_direction('down', 0), base.leaf_direction('down', 0),
                            base.elder(), base.slime(0), base.flame(0), base.projectile()])]
    for region, key in REGIONS:
        module = importlib.import_module(key)
        if key == 'generate_region':
            sprites = [module.npc_sprite(i) for i in range(6)]
        else:
            count = 10 if region == 'Covenants' else 5 if region in ('Hearthwake', 'Nacreway', 'Homecoming', 'Horizons') else 6
            sprites = [module.sprite(n) for n in module.NAMES[:count]]
        rows.append((region, sprites))
    atlas = Image.new('RGB', (284, len(rows) * 24 + 12), base.rgb[base.P['deep']])
    draw = ImageDraw.Draw(atlas)
    for yy, (label, sprites) in enumerate(rows):
        y = yy * 24 + 8
        draw.text((4, y + 2), label, fill=base.rgb[base.P['white']])
        for x, art in enumerate(sprites):
            paste(atlas, art, (108 + x * 17, y))
    save_zoom(atlas, 'characters_after')
    before = OUT / 'characters_before_native.png'
    if before.exists():
        old = Image.open(before).convert('RGB')
        comparison = Image.new('RGB', (atlas.width * 2 + 8, atlas.height + 18), base.rgb[base.P['deep']])
        labels = ImageDraw.Draw(comparison)
        labels.text((4, 3), 'BEFORE', fill=base.rgb[base.P['white']])
        labels.text((atlas.width + 12, 3), 'LANTERN KEEPER', fill=base.rgb[base.P['gold3']])
        comparison.paste(old, (0, 18))
        comparison.paste(atlas, (atlas.width + 8, 18))
        save_zoom(comparison, 'characters_comparison', 3)
    candidates = Image.new('RGB', (216, 100), base.rgb[base.P['deep']])
    draw = ImageDraw.Draw(candidates)
    for i in range(6):
        x = i * 36 + 10
        for y, background in ((15, 'dirt4'), (51, 'pine0')):
            draw.rectangle((i * 36, y - 2, i * 36 + 35, y + 18), fill=base.rgb[base.P[background]])
            paste(candidates, base.characters.keeper(base.Art, 'down', 0, i), (x, y))
        paste(candidates, base.characters.flame(base.Art, 0, i), (x, 80))
        draw.text((x + 5, 1), str(i + 1), fill=base.rgb[base.P['gold4']])
    save_zoom(candidates, 'candidate_studies', 5)
    animations = []
    for frame in range(4):
        scene = Image.new('RGB', (160, 120), base.rgb[base.P['bg_sunlit_grass2']])
        for row, fn in enumerate((base.hero, base.fox_direction, base.leaf_direction)):
            for column, direction in enumerate(DIRECTIONS):
                pos = (column * 40 + 12, row * 40 + 12)
                paste(scene, base.shadow_sprite(), pos)
                paste(scene, fn(direction, frame), pos)
        animations.append(scene.resize((640, 480), Image.Resampling.NEAREST))
    animations[0].save(OUT / 'four_pose_walk.gif', save_all=True, append_images=animations[1:],
                       duration=[110, 100, 80, 100], loop=0, disposal=2)
    contact = Image.new('RGB', (128, 208), base.rgb[base.P['deep']])
    draw = ImageDraw.Draw(contact)
    for row, fn in enumerate((base.hero, base.fox_direction, base.leaf_direction)):
        for d, direction in enumerate(DIRECTIONS):
            for frame in range(4):
                paste(contact, fn(direction, frame), (frame * 32, row * 64 + d * 16))
    for i in range(4):
        paste(contact, base.flame(i & 1), (i * 32, 192))
    save_zoom(contact, 'motion_contact')
    projectile = Image.new('RGB', (96, 24))
    draw = ImageDraw.Draw(projectile)
    for i, background in enumerate(('pine0', 'dirt4', 'water2')):
        draw.rectangle((i * 32, 0, i * 32 + 31, 23), fill=base.rgb[base.P[background]])
        paste(projectile, base.projectile(), (i * 32 + 8, 4))
    save_zoom(projectile, 'projectile_readability')
    campaign = importlib.import_module('generate_campaign')
    campaign.Art, campaign.P, campaign.PAL, campaign.RGB = base.Art, base.P, base.PAL, base.rgb
    allies = Image.new('RGB', (160, 128), base.rgb[base.P['deep']])
    for index, fn in enumerate((campaign.fuuri, campaign.kohaku)):
        for direction, facing in enumerate(DIRECTIONS):
            for frame in range(4):
                paste(allies, fn(facing, frame), (index * 80 + frame * 16, direction * 16))
    paste(allies, base.golem(), (8, 80))
    paste(allies, campaign.kazane(), (64, 80))
    paste(allies, campaign.core_keeper(), (112, 80))
    save_zoom(allies, 'allies_and_wardens')
    title = base.color_background(base.title(), 'title')
    for art, pos in ((base.hero('up', 0), (12, 125)), (base.fox_direction('down', 0), (27, 131))):
        mask = Image.frombytes('L', art.im.size, bytes(255 if p else 0 for p in art.im.tobytes()))
        title.im.paste(art.im, pos, mask)
    save_zoom(title.im.convert('RGB'), 'title_backdrop')
    review = {'native_actor_size': [16, 16], 'native_boss_size': [32, 32],
              'palette_entries': len(base.COLORS), 'added_runtime_ram_bytes': 0,
              'selected_study': 1, 'selection': 'Teal coat, auburn crown and trailing gold scarf remain distinct on light paths and dark foliage; the small bronze satchel leaves both hands and feet readable.',
              'review_scope': 'Authoring previews; emulator capture and frame timing remain separate acceptance evidence.',
              'resident_count': sum(len(v) for v in base.characters.RESIDENTS.values()),
              'references': ['https://www.spritefusion.com/blog/how-to-make-good-pixel-art-effects-with-claude',
                             'https://shmuplations.com/miyamotodesign/',
                             'https://github.com/agent-skills-hub/agent-skills-hub/blob/main/skills/game-development/game-design/SKILL.md']}
    (OUT / 'review.json').write_text(json.dumps(review, indent=2) + '\n')
    print('Rendered native comparisons, six studies, all-region residents and four true walk poses.')


if __name__ == '__main__':
    main()
