#!/usr/bin/env python3
"""Emit a bounded, freestanding, immutable native Return I art module.

This module does not know gameplay, rendering, OAM, or palette upload policy.
Inputs are authored indexed Pillow images. Validation finishes before any file
is changed; output is deterministic UTF-8 C99 split at complete source lines.
"""
from pathlib import Path
import re

FORM_IDS = (3, 6, 9, 12, 15, 17, 18, 21, 24, 27, 30, 101, 102, 103, 104)
MAX_INCLUDE_BYTES = 30000
DATA_BYTES = 15 + 15 * 4 * 4 * 256 + 15 * 4 * 3 * 256 + 15 * 1024
ROM_BUDGET_BYTES = 128 * 1024


def _validate_tensor(value, dimensions, image_size, label):
    if dimensions:
        if len(value) != dimensions[0]:
            raise ValueError(f"{label}: expected {dimensions[0]} entries")
        for i, child in enumerate(value):
            _validate_tensor(child, dimensions[1:], image_size, f"{label}[{i}]")
        return
    if getattr(value, "mode", None) != "P" or value.size != image_size:
        raise ValueError(f"{label}: expected indexed {image_size} image")
    if max(value.tobytes(), default=0) >= 97:
        raise ValueError(f"{label}: index outside the existing 97-color actor palette")


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
    """Write src/return_creature_art.{c,h}, return include chunk byte sizes.

    fields is [15][4][4] of 16x16 indexed images, abilities [15][4][3],
    portraits [15] of independently authored 32x32 indexed images.
    """
    form_ids = tuple(form_ids)
    names = tuple(names)
    if form_ids != FORM_IDS or any(type(fid) is not int for fid in form_ids):
        raise ValueError("Return I art requires exactly IDs 3,6,9,12,15,17,18,21,24,27,30,101-104 in order")
    if (len(names) != 15 or len(set(names)) != 15 or
            any(not isinstance(n, str) or not re.fullmatch(r"[A-Za-z][A-Za-z0-9]*(?: [A-Za-z0-9]+)*", n)
                for n in names) or len({n.upper() for n in names}) != 15):
        raise ValueError("Return I art requires 15 unique C-safe creature names")
    _validate_tensor(fields, (15, 4, 4), (16, 16), "fields")
    _validate_tensor(abilities, (15, 4, 3), (16, 16), "abilities")
    _validate_tensor(portraits, (15,), (32, 32), "portraits")

    enum_values = ", ".join("RETURN_CREATURE_" + name.upper().replace(" ", "_") for name in names)
    header = f'''/* Generated native art; edit assets/generate_return_creatures.py. */
#ifndef EMBERBOND_RETURN_CREATURE_ART_H
#define EMBERBOND_RETURN_CREATURE_ART_H
#define RETURN_CREATURE_ART_COUNT 15
#define RETURN_CREATURE_ART_FRAME_BYTES 256
#define RETURN_CREATURE_ART_PORTRAIT_BYTES 1024
#define RETURN_CREATURE_ART_DIRECTION_COUNT 4
#define RETURN_CREATURE_ART_WALK_FRAME_COUNT 4
#define RETURN_CREATURE_ART_ABILITY_FRAME_COUNT 3
#define RETURN_CREATURE_ART_DATA_BYTES {DATA_BYTES}
#define RETURN_CREATURE_ART_ROM_BUDGET_BYTES {ROM_BUDGET_BYTES}
enum {{ {enum_values} }};
/* Stable form IDs: 3,6,9,12,15,17,18,21,24,27,30,101-104. No catalog or unlock changes.
 * Directions: down/up/left/right; four walk beats, three ability poses (anticipation/release/settle).
 * Native row-major 8bpp existing game_palette indices; zero is transparent.
 * Field anchor is (8,8). All pixel arrays and IDs are const ROM.
 * No heap, mutable RAM, BSS, IWRAM, palette upload, or persistent OBJ allocation.
 * These functions return pixels only. The caller's renderer owns signed
 * screen-coordinate clipping before any framebuffer or OBJ write.
 */
extern const unsigned char return_creature_form_ids[RETURN_CREATURE_ART_COUNT];
extern const unsigned char return_creature_direction_frames[RETURN_CREATURE_ART_COUNT][4][4][256];
extern const unsigned char return_creature_ability_frames[RETURN_CREATURE_ART_COUNT][4][3][256];
extern const unsigned char return_creature_portraits[RETURN_CREATURE_ART_COUNT][1024];
/* Unsupported IDs return -1/NULL. Invalid directions/frames return NULL.
 * Unsigned arguments deliberately reject wrapped negative int inputs too.
 * Returned pointers are immutable, with static ROM lifetime.
 */
int return_creature_art_index(unsigned int form_id);
const unsigned char *return_creature_art_frame(unsigned int form_id, unsigned int direction, unsigned int frame);
const unsigned char *return_creature_art_ability_frame(unsigned int form_id, unsigned int direction, unsigned int pose);
const unsigned char *return_creature_art_portrait(unsigned int form_id);
#endif
'''
    lines = ["const unsigned char return_creature_form_ids[15] = {" +
             ",".join(map(str, form_ids)) + "};\n\n"]
    lines.extend(_tensor_lines("return_creature_direction_frames", fields, (15, 4, 4, 256)))
    lines.extend(_tensor_lines("return_creature_ability_frames", abilities, (15, 4, 3, 256)))
    lines.extend(_tensor_lines("return_creature_portraits", portraits, (15, 1024)))
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

    code = '#include "return_creature_art.h"\n/* Original immutable native pixel arrays. */\n'
    code += "".join(f'#include "return_creature_art_data/part_{i:03d}.inc"\n'
                    for i in range(len(chunks)))
    code += "\nint return_creature_art_index(unsigned int form_id) {\n    switch (form_id) {\n"
    code += "".join(f"    case {id}: return RETURN_CREATURE_{name.upper().replace(chr(32), chr(95))};\n"
                    for id, name in zip(form_ids, names))
    code += '''    default: return -1;
    }
}
const unsigned char *return_creature_art_frame(unsigned int form_id, unsigned int direction, unsigned int frame) {
    int i = return_creature_art_index(form_id);
    if (i < 0 || direction >= 4 || frame >= 4) return (const unsigned char *)0;
    return return_creature_direction_frames[i][direction][frame];
}
const unsigned char *return_creature_art_ability_frame(unsigned int form_id, unsigned int direction, unsigned int pose) {
    int i = return_creature_art_index(form_id);
    if (i < 0 || direction >= 4 || pose >= 3) return (const unsigned char *)0;
    return return_creature_ability_frames[i][direction][pose];
}
const unsigned char *return_creature_art_portrait(unsigned int form_id) {
    int i = return_creature_art_index(form_id);
    return i < 0 ? (const unsigned char *)0 : return_creature_portraits[i];
}
'''
    src = Path(root) / "src"
    folder = src / "return_creature_art_data"
    folder.mkdir(parents=True, exist_ok=True)
    (src / "return_creature_art.h").write_text(header, encoding="utf-8")
    for i, chunk in enumerate(chunks):
        (folder / f"part_{i:03d}.inc").write_text(chunk, encoding="utf-8")
    # Remove stale generated chunks only, leaving all unrelated files alone.
    expected = {f"part_{i:03d}.inc" for i in range(len(chunks))}
    for old in folder.glob("part_*.inc"):
        if old.name not in expected:
            old.unlink()
    (src / "return_creature_art.c").write_text(code, encoding="utf-8")
    return [len(chunk.encode("utf-8")) for chunk in chunks]
