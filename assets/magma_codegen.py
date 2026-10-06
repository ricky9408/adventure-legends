#!/usr/bin/env python3
"""Emit a bounded, freestanding, immutable native Magma art module.

This module does not know gameplay, rendering, OAM, or palette upload policy.
Inputs are authored indexed Pillow images. Validation finishes before any file
is changed; output is deterministic UTF-8 C99 split at complete source lines.
"""
from pathlib import Path
import re

FORM_IDS = tuple(range(31, 49)) + tuple(range(95, 101))
MAX_INCLUDE_BYTES = 30000
DATA_BYTES = 24 + 24 * 4 * 4 * 256 + 24 * 4 * 2 * 256 + 24 * 1024
ROM_BUDGET_BYTES = 170 * 1024


def _validate_tensor(value, dimensions, image_size, label):
    if dimensions:
        if len(value) != dimensions[0]:
            raise ValueError(f"{label}: expected {dimensions[0]} entries")
        for i, child in enumerate(value):
            _validate_tensor(child, dimensions[1:], image_size, f"{label}[{i}]")
        return
    if getattr(value, "mode", None) != "P" or value.size != image_size:
        raise ValueError(f"{label}: expected indexed {image_size} image")
    if max(value.tobytes(), default=0) >= 178:
        raise ValueError(f"{label}: index outside the existing 178-color palette")


def _tensor_lines(symbol, tensor, shape):
    yield f"const unsigned char {symbol}" + "".join(f"[{n}]" for n in shape) + " = {\n"

    def rows(value, depth):
        indent = "  " * depth
        if hasattr(value, "tobytes"):
            yield indent + "{\n"
            pixels = value.tobytes()
            for pos in range(0, len(pixels), 32):
                yield indent + "  " + ",".join(map(str, pixels[pos:pos + 32])) + ",\n"
            yield indent + "},\n"
        else:
            yield indent + "{\n"
            for child in value:
                yield from rows(child, depth + 1)
            yield indent + "},\n"

    for entry in tensor:
        yield from rows(entry, 1)
    yield "};\n\n"


def emit_code(root, form_ids, names, fields, abilities, portraits):
    """Write src/magma_creature_art.{c,h}, return include chunk byte sizes.

    fields is [24][4][4] of 16x16 indexed images, abilities [24][4][2],
    portraits [24] of independently authored 32x32 indexed images.
    """
    form_ids = tuple(form_ids)
    names = tuple(names)
    if form_ids != FORM_IDS:
        raise ValueError("Magma art requires exactly IDs 31-48 and 95-100 in order")
    if (len(names) != 24 or len(set(names)) != 24 or
            any(not isinstance(n, str) or not re.fullmatch(r"[A-Za-z][A-Za-z0-9]*", n)
                for n in names) or len({n.upper() for n in names}) != 24):
        raise ValueError("Magma art requires 24 unique C-safe creature names")
    _validate_tensor(fields, (24, 4, 4), (16, 16), "fields")
    _validate_tensor(abilities, (24, 4, 2), (16, 16), "abilities")
    _validate_tensor(portraits, (24,), (32, 32), "portraits")

    enum_values = ", ".join("MAGMA_CREATURE_" + name.upper() for name in names)
    header = f'''/* Generated native art; edit assets/generate_magma_creatures.py. */
#ifndef EMBERBOND_MAGMA_CREATURE_ART_H
#define EMBERBOND_MAGMA_CREATURE_ART_H
#define MAGMA_CREATURE_ART_COUNT 24
#define MAGMA_CREATURE_ART_FRAME_BYTES 256
#define MAGMA_CREATURE_ART_PORTRAIT_BYTES 1024
#define MAGMA_CREATURE_ART_DIRECTION_COUNT 4
#define MAGMA_CREATURE_ART_WALK_FRAME_COUNT 4
#define MAGMA_CREATURE_ART_ABILITY_FRAME_COUNT 2
#define MAGMA_CREATURE_ART_DATA_BYTES {DATA_BYTES}
#define MAGMA_CREATURE_ART_ROM_BUDGET_BYTES {ROM_BUDGET_BYTES}
enum {{ {enum_values} }};
/* Stable form IDs: 31-48,95-100. No catalog or unlock changes.
 * Directions: down/up/left/right; four walk beats, two ability poses.
 * Native row-major 8bpp existing game_palette indices; zero is transparent.
 * Field anchor is (8,8). All pixel arrays and IDs are const ROM.
 * No heap, mutable RAM, BSS, IWRAM, palette upload, or persistent OBJ allocation.
 * These functions return pixels only. The caller's renderer owns signed
 * screen-coordinate clipping before any framebuffer or OBJ write.
 */
extern const unsigned char magma_creature_form_ids[MAGMA_CREATURE_ART_COUNT];
extern const unsigned char magma_creature_direction_frames[MAGMA_CREATURE_ART_COUNT][4][4][256];
extern const unsigned char magma_creature_ability_frames[MAGMA_CREATURE_ART_COUNT][4][2][256];
extern const unsigned char magma_creature_portraits[MAGMA_CREATURE_ART_COUNT][1024];
/* Unsupported IDs return -1/NULL. Invalid directions/frames return NULL.
 * Unsigned arguments deliberately reject wrapped negative int inputs too.
 * Returned pointers are immutable, with static ROM lifetime.
 */
int magma_creature_art_index(unsigned int form_id);
const unsigned char *magma_creature_art_frame(unsigned int form_id, unsigned int direction, unsigned int frame);
const unsigned char *magma_creature_art_ability_frame(unsigned int form_id, unsigned int direction, unsigned int pose);
const unsigned char *magma_creature_art_portrait(unsigned int form_id);
#endif
'''
    lines = ["const unsigned char magma_creature_form_ids[24] = {" +
             ",".join(map(str, form_ids)) + "};\n\n"]
    lines.extend(_tensor_lines("magma_creature_direction_frames", fields, (24, 4, 4, 256)))
    lines.extend(_tensor_lines("magma_creature_ability_frames", abilities, (24, 4, 2, 256)))
    lines.extend(_tensor_lines("magma_creature_portraits", portraits, (24, 1024)))
    chunks, current, size = [], [], 0
    for line in lines:
        line_size = len(line.encode("utf-8"))
        if line_size > MAX_INCLUDE_BYTES:
            raise ValueError("A generated source line exceeds the include-file budget")
        if current and size + line_size > MAX_INCLUDE_BYTES:
            chunks.append("".join(current))
            current, size = [], 0
        current.append(line)
        size += line_size
    if current:
        chunks.append("".join(current))

    code = '#include "magma_creature_art.h"\n/* Original immutable native pixel arrays. */\n'
    code += "".join(f'#include "magma_creature_art_data/part_{i:03d}.inc"\n'
                    for i in range(len(chunks)))
    code += "\nint magma_creature_art_index(unsigned int form_id) {\n    switch (form_id) {\n"
    code += "".join(f"    case {id}: return MAGMA_CREATURE_{name.upper()};\n"
                    for id, name in zip(form_ids, names))
    code += '''    default: return -1;
    }
}
const unsigned char *magma_creature_art_frame(unsigned int form_id, unsigned int direction, unsigned int frame) {
    int i = magma_creature_art_index(form_id);
    if (i < 0 || direction >= 4 || frame >= 4) return (const unsigned char *)0;
    return magma_creature_direction_frames[i][direction][frame];
}
const unsigned char *magma_creature_art_ability_frame(unsigned int form_id, unsigned int direction, unsigned int pose) {
    int i = magma_creature_art_index(form_id);
    if (i < 0 || direction >= 4 || pose >= 2) return (const unsigned char *)0;
    return magma_creature_ability_frames[i][direction][pose];
}
const unsigned char *magma_creature_art_portrait(unsigned int form_id) {
    int i = magma_creature_art_index(form_id);
    return i < 0 ? (const unsigned char *)0 : magma_creature_portraits[i];
}
'''
    src = Path(root) / "src"
    folder = src / "magma_creature_art_data"
    folder.mkdir(parents=True, exist_ok=True)
    (src / "magma_creature_art.h").write_text(header, encoding="utf-8")
    for i, chunk in enumerate(chunks):
        (folder / f"part_{i:03d}.inc").write_text(chunk, encoding="utf-8")
    # Remove stale generated chunks only, leaving all unrelated files alone.
    expected = {f"part_{i:03d}.inc" for i in range(len(chunks))}
    for old in folder.glob("part_*.inc"):
        if old.name not in expected:
            old.unlink()
    (src / "magma_creature_art.c").write_text(code, encoding="utf-8")
    return [len(chunk.encode("utf-8")) for chunk in chunks]
