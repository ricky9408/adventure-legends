#!/usr/bin/env python3
"""Current-source Horizons camera, bitmap-copy and actor-coordinate regression.

The initial integration subtracted the camera in ra/rf before region_pixels_actor
and obj_add subtracted it again. A screen-coordinate host stub hid that defect.
This test extracts the real wrappers and engine functions on every invocation;
an isolated mutation restores the double subtraction and must fail the oracle.

Run: python3 tests/test_horizons_camera.py [--report path/to/report.json]
Requires Python 3 and a C++17 compiler (CXX, or c++), including ASan/UBSan.
Only temporary C++/executables and an explicitly requested report are written.
Patterned atlases and synchronous DMA stand in for hardware. This is not native
gameplay, actual artwork, VBlank/audio timing, or release-performance evidence.
"""

from pathlib import Path
import argparse
import hashlib
import json
import os
import re
import shlex
import subprocess
import tempfile


ROOT = Path(__file__).resolve().parents[1]
SOURCE_PATHS = (
    "src/game.c",
    "src/horizons_engine.inc",
    "src/modal_blit.inc",
    "src/horizons_game_draw.inc",
    "src/horizons_art.h",
    "src/obj_layout.h",
    "assets/horizons_region/geometry.json",
)


def c_mask(source):
    """Keep offsets/newlines while hiding braces in C comments and literals."""
    pattern = r'/\*.*?\*/|//[^\n]*|"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\''
    return re.sub(pattern, lambda m: re.sub(r"[^\n]", " ", m.group()), source,
                  flags=re.DOTALL)


def extract_function(source, name, filename):
    masked = c_mask(source)
    pattern = (r"^(?:static\s+)?(?:COLD\s+)?(?:int|void)\s+" + re.escape(name)
               + r"\s*\([^;{}]*\)\s*\{")
    matches = list(re.finditer(pattern, masked, re.MULTILINE))
    if len(matches) != 1:
        raise AssertionError(f"Expected one definition of {name} in {filename}")
    start = matches[0].start()
    cursor = masked.index("{", start) + 1
    depth = 1
    while depth and cursor < len(masked):
        depth += (masked[cursor] == "{") - (masked[cursor] == "}")
        cursor += 1
    if depth:
        raise AssertionError(f"Unclosed definition of {name} in {filename}")
    line = source.count("\n", 0, start) + 1
    return f'#line {line} "{filename}"\n' + source[start:cursor] + "\n"


def collect_sources():
    sources = {p: (ROOT / p).read_text() for p in SOURCE_PATHS}
    art_source = (ROOT / "src/horizons_art.c").read_text()
    sources["src/horizons_art.c"] = art_source
    tables = []
    for include in re.findall(r'^#include "(horizons_art_data/[^\"]+)"',
                              art_source, re.MULTILINE):
        path = "src/" + include
        text = (ROOT / path).read_text()
        if re.search(r"\bhorizons_art_rooms\s*\[", text):
            sources[path] = text
            tables.append(text)
    if len(tables) != 1:
        raise AssertionError("Expected one generated Horizons room table")
    table = re.search(r"horizons_art_rooms\s*\[\d+\]\s*=\s*\{(.*?)\};",
                      tables[0], re.DOTALL)
    if not table:
        raise AssertionError("Could not parse current generated room table")
    rows = re.findall(r"\{\s*(\d+)\s*,\s*(\d+)\s*,\s*"
                      r"horizons_background_room(\d+)\s*,\s*([^,]+),",
                      table.group(1))
    rooms = [(int(area), int(width), int(height), odd.strip() != "0")
             for width, height, area, odd in rows]
    assert [r[0] for r in rooms] == list(range(62, 70)), rooms
    geometry = json.loads(sources["assets/horizons_region/geometry.json"])["rooms"]
    assert [(r["id"], r["width"], r["height"]) for r in geometry] == [
        r[:3] for r in rooms], "Generated room dimensions differ from geometry"
    assert all(w in (240, 480) and h in (160, 320) and (w != 480 or odd)
               for _, w, h, odd in rooms), rooms
    return sources, rooms


HEAD = r'''
#include <algorithm>
#include <cstdio>
#include <cstdlib>
#include <cstdint>
#include <cstring>
#include <vector>
#include "horizons_art.h"
#include "covenants_art.h"
#include "obj_layout.h"
#define COLD
using u8 = unsigned char;
using u16 = unsigned short;
// Host pointers retain their width; native DMA byte counts remain unchanged.
using u32 = uintptr_t;
static void check(bool ok, const char *what) {
    if (!ok) { std::fprintf(stderr, "FAIL: %s\n", what); std::exit(1); }
}
int room, px, py, camera_x, camera_y, camera_fx, camera_fy, game_state, journal_tab;
int quickparty_open, obj_count, obj_depth[128], region_actor_cursor, frame, ticks;
// New chapter branches cannot execute in this historical62..69 oracle.
const CovenantsArtRoom covenants_art_rooms[8] = {};
unsigned covenants_creature_art_walk_index(unsigned, unsigned) { std::abort(); }
unsigned region_actor_keys[20];
u16 pixels[240 * 160 / 2];
u16 *screen = pixels;
struct ObjEntry { u16 a0, a1, a2, pad; };
ObjEntry obj_entries[128];
const u8 horizons_sprites[HORIZONS_SPR_COUNT][256] = {{0}};
static bool selected = true;
int ab(int value) { return value < 0 ? -value : value; }
void *progression_selected(void) { return selected ? pixels : nullptr; }
int save_notice_visible(void) { return 0; }
int save_notice_left(void) { return 0; }
void obj_upload(const u8 *, int, int, int) {}
const u8 *companion_form_pixels(unsigned, unsigned, unsigned) {
    return horizons_sprites[0];
}
static uintptr_t dma_source, dma_destination, bitmap_begin, odd_begin;
static size_t atlas_size;
struct Register {
    unsigned address;
    void operator=(uintptr_t value) const {
        if (address == 0x040000D4) { dma_source = value; return; }
        if (address == 0x040000D8) { dma_destination = value; return; }
        check(address == 0x040000DC && (value & 0x80000000), "DMA control");
        size_t bytes = (value & 65535) * ((value & 0x04000000) ? 4 : 2);
        uintptr_t screen_begin = reinterpret_cast<uintptr_t>(screen);
        check(bytes && dma_destination >= screen_begin &&
              dma_destination + bytes <= screen_begin + sizeof(pixels),
              "DMA destination bounds");
        check((dma_source >= bitmap_begin &&
               dma_source + bytes <= bitmap_begin + atlas_size) ||
              (odd_begin && dma_source >= odd_begin &&
               dma_source + bytes <= odd_begin + atlas_size),
              "DMA source bounds");
        std::memcpy(reinterpret_cast<void *>(dma_destination),
                    reinterpret_cast<const void *>(dma_source), bytes);
    }
};
#define REG32(address) Register{address}
'''


CHECKS = r'''
static std::vector<int> sample_cameras(int maximum, bool vertical) {
    std::vector<int> samples = vertical ? std::vector<int>{0, 1, 73, 79, 159, 160}
                                       : std::vector<int>{0, 1, 17, 119, 120, 239, 240};
    samples.push_back(maximum);
    std::sort(samples.begin(), samples.end());
    samples.erase(std::unique(samples.begin(), samples.end()), samples.end());
    samples.erase(std::remove_if(samples.begin(), samples.end(),
        [maximum](int n) { return n < 0 || n > maximum; }), samples.end());
    return samples;
}
static unsigned actor_checks(void) {
    unsigned checks = 0;
    for (room = 62; room < 70; ++room) {
        for (int xcam : sample_cameras(world_width() - 240, false)) {
            for (int ycam : sample_cameras(world_height() - 160, true)) {
                camera_x = xcam; camera_y = ycam; game_state = PLAY;
                for (int y = -10; y < 172; y += 7) {
                    for (int x = -10; x < 252; x += 7) {
                        obj_count = region_actor_cursor = 0;
                        ra(0, xcam + x, ycam + y);
                        rf(105, xcam + x, ycam + y);
                        bool visible = x > -8 && x < 248 && y > -8 && y < 168;
                        check(obj_count == (visible ? 2 : 0), "actor visible count");
                        if (visible) for (int n = 0; n < 2; ++n) {
                            check((obj_entries[n].a1 & 511) == ((x - 8) & 511),
                                  "actor x must subtract camera exactly once");
                            check((obj_entries[n].a0 & 255) == ((y - 8) & 255),
                                  "actor y must subtract camera exactly once");
                            check(obj_depth[n] == ycam + y, "actor world depth");
                        }
                        ++checks;
                    }
                }
            }
        }
    }
    return checks;
}
int main(void) {
    unsigned copies = 0, snaps = 0;
    for (room = 62; room < 70; ++room) {
        const HorizonsArtRoom &map = horizons_art_rooms[room - 62];
        int width = map.width, height = map.height;
        check(world_width() == width && world_height() == height,
              "engine dimensions match generated room table");
        check(!!scrolling_room() == (width > 240 || height > 160),
              "engine mixed-axis scrolling classification");
        // Writable patterned storage is created by this harness, never ROM art.
        u8 *bitmap = const_cast<u8 *>(map.bitmap);
        u8 *odd = const_cast<u8 *>(map.bitmap_odd);
        for (int y = 0; y < height; ++y) for (int x = 0; x < width; ++x)
            bitmap[y * width + x] = static_cast<u8>((x / 17 + y * 31) % 251);
        if (odd) for (int y = 0; y < height; ++y) for (int x = 0; x < width; ++x)
            odd[y * width + x] = bitmap[y * width + (x + 1) % width];
        bitmap_begin = reinterpret_cast<uintptr_t>(bitmap);
        odd_begin = reinterpret_cast<uintptr_t>(odd);
        atlas_size = width * height;
        for (px = -10; px <= width + 10; px += 7) {
            for (py = -10; py <= height + 10; py += 11) {
                camera_update(1);
                int x = std::clamp(px - 120, 0, width - 240);
                int y = std::clamp(py - 80, 0, height - 160);
                check(camera_x == x && camera_y == y, "camera snap clamp");
                check(camera_fx == x * 256 && camera_fy == y * 256,
                      "camera fixed-point snap");
                ++snaps;
            }
        }
        for (int xcam : sample_cameras(width - 240, false)) {
            for (int ycam : sample_cameras(height - 160, true)) {
                camera_x = xcam; camera_y = ycam;
                for (int state : {PLAY, PAUSE, SAVE_PENDING, EVOLVE_CONFIRM,
                                  EVOLVE_ANIM, EVENT_PENDING}) {
                    for (journal_tab = 0; journal_tab < 2; ++journal_tab) {
                        for (int has_selected = 0; has_selected < 2; ++has_selected) {
                            selected = has_selected; game_state = state;
                            std::memset(pixels, 253, sizeof(pixels));
                            copy_horizons();
                            const u8 *actual = reinterpret_cast<const u8 *>(pixels);
                            int left = 0, first = 0, last = 0;
                            if (width == 480 || (width == 240 && state == PAUSE && journal_tab == 0)) {
                                if (state == PAUSE && journal_tab == 0)
                                    { left = 8; first = 31; last = 150; }
                                else if (state == EVOLVE_CONFIRM)
                                    { left = 12; first = 42; last = 147; }
                                else if (state == EVOLVE_ANIM && selected)
                                    { left = 20; first = 38; last = 152; }
                                else if (state == SAVE_PENDING || state == EVENT_PENDING)
                                    { left = 38; first = 77; last = 111; }
                            }
                            for (int y = 0; y < 160; ++y) for (int x = 0; x < 240; ++x) {
                                bool covered = left && y >= first && y < last &&
                                               x >= left && x < 240 - left;
                                int expected = covered ? 253 :
                                    bitmap[(ycam + y) * width + xcam + x];
                                if (actual[y * 240 + x] != expected) {
                                    std::fprintf(stderr, "FAIL: bitmap room=%d camera=%d,%d "
                                        "state=%d tab=%d selected=%d pixel=%d,%d\n",
                                        room, xcam, ycam, state, journal_tab,
                                        has_selected, x, y);
                                    return 1;
                                }
                            }
                            ++copies;
                        }
                    }
                }
            }
        }
    }
    unsigned actors = actor_checks();
    std::printf("{\"camera_snap_cases\":%u,\"bitmap_copy_cases\":%u,"
                "\"actor_coordinate_cases\":%u}\n", snaps, copies, actors);
    return 0;
}
'''


def harness(sources, rooms, double_camera=False):
    game = sources["src/game.c"]
    defines = []
    for name in ("PLAY", "DIALOG", "PAUSE", "DEAD", "SAVE_PENDING",
                 "EVOLVE_CONFIRM", "EVOLVE_ANIM", "EVENT_PENDING",
                 "SAVE_NOTICE_Y", "SAVE_NOTICE_H"):
        found = re.findall(r"^#define " + name + r"\s+[^\n]+", game, re.MULTILINE)
        assert len(found) == 1, name
        defines.extend(found)
    storage, rows = [], []
    for i, (_, width, height, has_odd) in enumerate(rooms):
        storage.append(f"static u8 pattern_{i}[{width * height}];")
        odd = "nullptr"
        if has_odd:
            storage.append(f"static u8 shifted_{i}[{width * height}];")
            odd = f"shifted_{i}"
        rows.append(f"{{{width},{height},pattern_{i},{odd},nullptr,0,nullptr,nullptr}}")
    storage.append("const HorizonsArtRoom horizons_art_rooms[8] = {"
                   + ",".join(rows) + "};")
    parts = [HEAD, "\n".join(defines), "\n".join(storage)]
    for name in ("scrolling_room", "world_width", "world_height", "camera_update"):
        parts.append(extract_function(game, name, "src/game.c"))
    parts.append('#line 1 "src/modal_blit.inc"\n' + sources["src/modal_blit.inc"])
    parts.append(extract_function(sources["src/horizons_engine.inc"],
                                  "copy_horizons", "src/horizons_engine.inc"))
    for name in ("obj_add", "region_pixels_actor", "horizons_actor", "region_form_actor"):
        parts.append(extract_function(game, name, "src/game.c"))
    for name, target, argument in (("ra", "horizons_actor", "s"),
                                   ("rf", "region_form_actor", "f")):
        if double_camera:
            # Negative control only: recreate the original bug in temporary code.
            parts.append(f"static void {name}(unsigned {argument},int x,int y)"
                         f"{{{target}({argument},x-camera_x,y-camera_y);}}")
        else:
            parts.append(extract_function(sources["src/horizons_game_draw.inc"],
                                          name, "src/horizons_game_draw.inc"))
    parts.extend(['#line 1 "camera_oracle.cpp"', CHECKS])
    return "\n".join(parts)


def run(compiler, folder, name, source, sanitize=False, must_fail=False):
    cpp, executable = folder / (name + ".cpp"), folder / name
    cpp.write_text(source)
    flags = ["-std=c++17", "-O1", "-g", "-Wall", "-Wextra", "-Werror",
             "-Wno-misleading-indentation"]
    if sanitize:
        flags.extend(["-fsanitize=address,undefined", "-fno-omit-frame-pointer"])
    subprocess.run([*compiler, *flags, "-I", str(ROOT / "src"), str(cpp),
                    "-o", str(executable)], check=True, timeout=120)
    env = dict(os.environ)
    # This test owns no heap after process exit; LSan cannot run under some tracers.
    # Address and undefined-behavior checks remain enabled and fatal.
    env["ASAN_OPTIONS"] = "detect_leaks=0:halt_on_error=1"
    env["UBSAN_OPTIONS"] = "halt_on_error=1:print_stacktrace=1"
    result = subprocess.run([str(executable)], capture_output=True, text=True,
                            env=env, timeout=120)
    if must_fail:
        if result.returncode != 1 or "FAIL: actor" not in result.stderr:
            raise AssertionError(f"Mutation did not fail the actor oracle: {result}")
        return result.stderr.strip()
    if result.returncode:
        raise AssertionError(f"{name} failed ({result.returncode}):\n{result.stderr}")
    return json.loads(result.stdout)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, help="Optional JSON evidence output")
    args = parser.parse_args()
    compiler = shlex.split(os.environ.get("CXX", "c++"))
    if not compiler:
        parser.error("CXX must name a C++17 compiler")
    sources, rooms = collect_sources()
    pins = {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in sources}
    # Hash the exact text being extracted, so an edit between read/hash is detected.
    assert all(hashlib.sha256(text.encode()).hexdigest() == pins[p]
               for p, text in sources.items()), "Source changed while collecting inputs"
    current = harness(sources, rooms)
    with tempfile.TemporaryDirectory(prefix="horizons-camera-") as temporary:
        folder = Path(temporary)
        strict = run(compiler, folder, "strict", current)
        sanitized = run(compiler, folder, "sanitized", current, sanitize=True)
        assert strict == sanitized, (strict, sanitized)
        mutation = run(compiler, folder, "double-camera-negative-control",
                       harness(sources, rooms, double_camera=True), must_fail=True)
    assert all(hashlib.sha256((ROOT / p).read_bytes()).hexdigest() == digest
               for p, digest in pins.items()), "Reviewed source changed during the test"
    evidence = {
        "scope": "current-source host coordinate and synchronous DMA simulation",
        "not_native_gameplay_or_timing_evidence": True,
        "strict": strict,
        "address_and_undefined_sanitizers": sanitized,
        "initial_bug": "ra/rf subtracted the camera before the engine subtracted it again",
        "double_camera_mutation_rejected": mutation,
        "room_dimensions": [{"area": a, "width": w, "height": h}
                            for a, w, h, _ in rooms],
        "source_sha256": pins,
        "test_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    }
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(evidence, indent=2) + "\n")
    print("PASS:", json.dumps(strict, sort_keys=True))
    print("PASS: strict + ASan/UBSan; original double-camera mutation rejected")
    print("Scope: current-source host checks, not native gameplay or timing")


if __name__ == "__main__":
    main()
