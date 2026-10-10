/* Readable Gear prototype: independently specified 4x7 digits and layout.
 * Real generated UiRun masks plus an independent decimal/color/layout oracle.
 * UI fixtures isolate the production menu draw from gameplay, covered by the
 * effective-preview test. No GBA RAM, generated-text edits, or font substitutes.
 */
#include <assert.h>
#include <limits.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "../src/gear_menu.c"

enum { WIDTH = 240, HEIGHT = 160, PIXELS = WIDTH * HEIGHT };
static union { unsigned short words[PIXELS / 2]; unsigned char pixels[PIXELS]; } actual;
static unsigned char expected[PIXELS];
unsigned short *screen = actual.words;
Save5State adventure_save;
static EquipmentComparison fixture_comparison;
static GearPreview fixture_before, fixture_after;
static unsigned selected_command = 1, projection_calls;
static int render_card_background;

/* Individual components can vary independently. Alternatives within one group
 * are unioned; BUSY replaces TITLE and STATUS. Background/highlight fills are
 * intentionally excluded from foreground-intersection checks.
 */
enum {
    TITLE, STATUS, BUSY, TAB0, TAB1, TAB2, TAB3, TAB4,
    LEFT, RIGHT, UP, DOWN, NAME, CONTEXT, FOOTER, FIRST_STAT,
    GROUPS = FIRST_STAT + 7 * 4
};
static unsigned char unions[GROUPS][PIXELS];
static const char *const chrome_names[] = {
    "title", "status", "busy", "weapon tab", "body tab", "boots tab", "belt tab", "ring tab",
    "left", "right", "up", "down", "candidate name", "context", "footer"
};
static const char *const stat_names[] = {"attack", "defense", "hearts", "walk", "recovery", "distance", "stagger"};
static const char *const parts[] = {"label", "before", "arrow", "after"};
static unsigned helper_cases, menu_cases, text_cases, synthetic_cases;

static void describe(unsigned group, char *buffer, size_t length) {
    if (group < FIRST_STAT) snprintf(buffer, length, "%s", chrome_names[group]);
    else snprintf(buffer, length, "%s %s", stat_names[(group - FIRST_STAT) / 4], parts[(group - FIRST_STAT) % 4]);
}

/* Per-component rectangles enforce spacing even when glyph silhouettes happen
 * not to intersect. Coordinates are specification constants, not runtime reads. */
static void component_bounds(unsigned group, int x, int y) {
    if (group >= FIRST_STAT) {
        unsigned which = (group - FIRST_STAT) / 4, part = (group - FIRST_STAT) % 4;
        int detail = which >= 4;
        int cell_left = detail ? 12 + (int)(which - 4) * 72 : 12 + (int)which * 54;
        int cell_right = cell_left + (detail ? 72 : 54);
        int top = detail ? 102 : 80, bottom = detail ? 115 : 93;
        int left = cell_left, right = cell_right;
        if (part) {
            top = detail ? 115 : 93;
            bottom = top + 7;
            if (part == 1) right = cell_left + (detail ? 32 : 23);
            else if (part == 2) {
                left = cell_left + (detail ? 33 : 24);
                right = left + 7;
                ++top; --bottom;
            } else left = cell_left + (detail ? 41 : 32);
        }
        if (x < left || x >= right || y < top || y >= bottom) {
            char description[80];
            describe(group, description, sizeof description);
            fprintf(stderr, "Outside dedicated cell area: %s at %d,%d; expected [%d,%d)x[%d,%d)\n",
                    description, x, y, left, right, top, bottom);
            abort();
        }
    }
}

static void pixel(unsigned char *canvas, int x, int y, unsigned char color, int group) {
    assert(x >= 0 && x < WIDTH && y >= 0 && y < HEIGHT);
    canvas[y * WIDTH + x] = color;
    if (group >= 0) {
        if (x < 8 || x >= 232 || y < 31 || y >= 154) {
            char description[80];
            describe((unsigned)group, description, sizeof description);
            fprintf(stderr, "Outside gear panel: %s at %d,%d\n", description, x, y);
            abort();
        }
        component_bounds((unsigned)group, x, y);
        unions[group][y * WIDTH + x] = 1;
    }
}

void rect(int x, int y, int w, int h, unsigned char color) {
    int row, column;
    assert(w > 0 && h > 0);
    for (row = 0; row < h; ++row) for (column = 0; column < w; ++column) {
        int px = x + column, py = y + row;
        if (px >= 0 && px < WIDTH && py >= 0 && py < HEIGHT)
            pixel(actual.pixels, px, py, color, -1);
    }
}

/* Exactly the public paired-pixel semantics used by game.c, including both
 * partial-halfword masks and preservation of the neighboring pixel.
 */
void text_spans(const UiText *value, int x, int y, int color) {
    const UiRun *run = value->runs[x & 1];
    unsigned count = value->count[x & 1];
    assert(x >= 0 && y >= 0);
    while (count--) {
        unsigned i;
        assert(run->count && run->mask >= 1 && run->mask <= 3);
        for (i = 0; i < run->count; ++i) {
            unsigned offset = (unsigned)y * 120 + (unsigned)x / 2 + run->offset + i;
            unsigned short *destination;
            assert(offset < PIXELS / 2);
            destination = screen + offset;
            if (run->mask == 3) *destination = (unsigned short)(color | (color << 8));
            else if (run->mask == 1) *destination = (unsigned short)((*destination & 0xff00) | color);
            else *destination = (unsigned short)((*destination & 0xff) | (color << 8));
        }
        ++run;
    }
}

void text(int id, int x, int y, int color) { text_spans(&ui_texts[id], x, y, color); }
void centered(int id, int y, int color) { text(id, (WIDTH - ui_texts[id].width) / 2, y, color); }
void box(int x, int y, int w, int h) {
    assert(x == 8 && y == 31 && w == 224 && h == 123);
    /* Foreground tests omit opaque fills; optional synthetic screenshots use
     * exactly game.c's ordinary UI_BG/PAL_GOLD2 panel and border colors. */
    if (render_card_background) {
        rect(x, y, w, h, PAL_INK);
        rect(x, y, w, 1, PAL_GOLD2);
        rect(x, y + h - 1, w, 1, PAL_GOLD2);
        rect(x, y, 1, h, PAL_GOLD2);
        rect(x + w - 1, y, 1, h, PAL_GOLD2);
    }
}

unsigned game_gear_base_hp(void) { return 96; }
unsigned game_gear_hp(void) { return 96; }
void game_gear_bonus_stats(EquipmentStats *stats) { (void)stats; }
unsigned progression_command(void) { return selected_command; }
unsigned economy_power_reduction(const Save5State *save) { return save->economy.relics & 2u ? 8u : 0u; }
unsigned equipment_preview(const EquipmentState *state, unsigned slot, unsigned ref,
                           unsigned base, unsigned hp_value, unsigned flags, EquipmentComparison *out) {
    (void)state; (void)slot; (void)ref; (void)base; (void)hp_value; (void)flags;
    *out = fixture_comparison;
    return EQUIPMENT_OK;
}
void gear_preview_project(const EquipmentStats *stats, unsigned command, GearPreview *out) {
    assert(command == selected_command);
    assert(projection_calls < 2);
    assert(!memcmp(stats, projection_calls ? &fixture_comparison.after : &fixture_comparison.before, sizeof *stats));
    *out = projection_calls++ ? fixture_after : fixture_before;
}

/* Decode canonical even-aligned mask pixels independently, then translate.
 * Production text_spans instead uses the generated parity-specific runs.
 */
static void oracle_text(const UiText *value, int x, int y, int color, int group) {
    unsigned index;
    for (index = 0; index < value->count[0]; ++index) {
        const UiRun *run = &value->runs[0][index];
        unsigned i, bit;
        for (i = 0; i < run->count; ++i) for (bit = 0; bit < 2; ++bit) if (run->mask & (1u << bit)) {
            unsigned offset = run->offset + i;
            unsigned column = (offset % 120) * 2 + bit, row = offset / 120;
            assert(column < value->width && row < value->height);
            pixel(expected, x + (int)column, y + (int)row, (unsigned char)color, group);
        }
    }
}

static void oracle_label(unsigned id, int x, int y, int color, int group) {
    oracle_text(&gear_preview_texts[id], x, y, color, group);
}
static void oracle_center(unsigned id, int y, int color, int group) {
    oracle_label(id, (WIDTH - gear_preview_texts[id].width) / 2, y, color, group);
}

/* This human-readable glyph specification is independent of production's
 * packed row representation and halfword stores. Exact shapes are deliberate. */
static const char *const oracle_digits[11] = {
    ".##." "#..#" "#..#" "#..#" "#..#" "#..#" ".##.",
    "..#." ".##." "..#." "..#." "..#." "..#." ".###",
    ".##." "#..#" "...#" "..#." ".#.." "#..." "####",
    "###." "...#" "...#" ".##." "...#" "...#" "###.",
    "..#." ".##." "#.#." "#.#." "####" "..#." "..#.",
    "####" "#..." "#..." "###." "...#" "...#" "###.",
    ".##." "#..." "#..." "###." "#..#" "#..#" ".##.",
    "####" "...#" "...#" "..#." "..#." ".#.." ".#..",
    ".##." "#..#" "#..#" ".##." "#..#" "#..#" ".##.",
    ".##." "#..#" "#..#" ".###" "...#" "...#" ".##.",
    ".##." "#..#" "...#" "..#." "..#." "...." "..#."
};

static void oracle_string(unsigned value, unsigned format, char output[32]) {
    if (format == 0) snprintf(output, 32, "%u", value);
    else if (format == 1) {
        unsigned remainder = value % 16;
        snprintf(output, 32, "%u", value / 16);
        if (remainder) {
            char fraction[8];
            snprintf(fraction, sizeof fraction, ".%04u", remainder * 625);
            while (fraction[strlen(fraction) - 1] == '0') fraction[strlen(fraction) - 1] = 0;
            strcat(output, fraction);
        }
    } else if (format == 2) snprintf(output, 32, "%u.%u", value / 10, value % 10);
    else { assert(format == 3); snprintf(output, 32, "%u.%02u", value / 100, value % 100); }
}

static unsigned oracle_width(const char *value) {
    unsigned width = 0;
    assert(*value);
    for (; *value; ++value) width += *value == '.' ? 3u : 5u;
    return width - 1;
}

static void oracle_value(unsigned value, unsigned format, int x, int y, int color, int group) {
    char buffer[32];
    const char *cursor;
    oracle_string(value, format, buffer);
    for (cursor = buffer; *cursor; ++cursor) {
        if (*cursor == '.') {
            unsigned row, column;
            for (row = 5; row < 7; ++row) for (column = 0; column < 2; ++column)
                pixel(expected, x + (int)column, y + (int)row, (unsigned char)color, group);
            x += 3;
        }
        else {
            unsigned row, column;
            for (row = 0; row < 7; ++row) for (column = 0; column < 4; ++column)
                if (oracle_digits[(unsigned)(*cursor - '0')][row * 4 + column] == '#')
                    pixel(expected, x + (int)column, y + (int)row, (unsigned char)color, group);
            x += 5;
        }
    }
}

static unsigned oracle_value_width(unsigned value, unsigned format) {
    char buffer[32];
    oracle_string(value, format, buffer);
    return oracle_width(buffer);
}

static void oracle_arrow(int x, int y, int group) {
    static const char shape[] = "....#.." "....##." "#######" "....##." "....#..";
    int row, column;
    for (row = 0; row < 5; ++row) for (column = 0; column < 7; ++column)
        if (shape[row * 7 + column] == '#')
            pixel(expected, x + column, y + row, TEAL, group);
}

static void exact_canvas(const char *context, unsigned before, unsigned after) {
    unsigned offset;
    for (offset = 0; offset < PIXELS; ++offset) if (actual.pixels[offset] != expected[offset]) {
        fprintf(stderr, "%s %u -> %u: pixel %u,%u actual=%u expected=%u\n",
                context, before, after, offset % WIDTH, offset / WIDTH, actual.pixels[offset], expected[offset]);
        abort();
    }
}

typedef struct { unsigned id, first, last, step, format; int x, lower; } StatCase;
static const StatCase stats[7] = {
    {GP_ATTACK, 32, 80, 1, 0, 12, 0}, {GP_DEFENSE, 0, 8, 1, 0, 66, 0},
    {GP_HEART, 96, 192, 4, 1, 120, 0}, {GP_WALK, 900, 1100, 1, 2, 174, 0},
    {GP_RECOVERY, 0, 402, 1, 3, 12, 1}, {GP_DISTANCE, 29, 156, 1, 0, 84, 0},
    {GP_STAGGER, 0, 3, 1, 0, 156, 0}
};

static void oracle_dash(int x, int y, int group) {
    int row, column;
    for (row = 3; row < 5; ++row) for (column = 0; column < 6; ++column)
        pixel(expected, x + column, y + row, CREAM, group);
}

/* Unknown values are a neutral, standalone question mark, never a rounded,
 * clamped or mixed "?.0" representation. Large integer parts are unsupported
 * even where their question mark would be narrower than the numeric value. */
static int oracle_supported(unsigned n, unsigned format, unsigned limit) {
    if (format > 3 || n > 65535) return 0;
    if ((format == 0 && n > 999) || (format == 1 && n / 16 > 999) ||
        (format == 2 && n / 10 > 999) || (format == 3 && n / 100 > 999)) return 0;
    return oracle_value_width(n, format) <= limit;
}

static unsigned oracle_cell_width(unsigned n, unsigned format, unsigned limit) {
    return oracle_supported(n, format, limit) ? oracle_value_width(n, format) : 4;
}

static void oracle_cell(unsigned n, unsigned format, int x, int y, int color, int group, unsigned limit) {
    if (oracle_supported(n, format, limit)) oracle_value(n, format, x, y, color, group);
    else {
        unsigned row, column;
        for (row = 0; row < 7; ++row) for (column = 0; column < 4; ++column)
            if (oracle_digits[10][row * 4 + column] == '#')
                pixel(expected, x + (int)column, y + (int)row, CREAM, group);
    }
}

static void expected_stat(unsigned which, unsigned before, unsigned after, int missing, int collect) {
    const StatCase *entry = &stats[which];
    int group = collect ? FIRST_STAT + (int)which * 4 : -1;
    int color = before == after ? CREAM : ((after > before) != entry->lower ? GOLD : PAL_HEART);
    int detail = which >= 4;
    int cell_width = detail ? 72 : 54, value_y = detail ? 115 : 93;
    int before_right = entry->x + (detail ? 32 : 23), after_left = entry->x + (detail ? 41 : 32);
    oracle_label(entry->id, entry->x + (cell_width - gear_preview_texts[entry->id].width) / 2,
                 detail ? 102 : 80, CREAM, group);
    oracle_arrow(entry->x + (detail ? 33 : 24), value_y + 1, collect ? group + 2 : -1);
    if (missing) {
        assert(which == 4);
        oracle_dash(before_right - 6, value_y, collect ? group + 1 : -1);
        oracle_dash(after_left, value_y, collect ? group + 3 : -1);
    } else {
        unsigned limit = detail ? 31 : 22;
        oracle_cell(before, entry->format, before_right - (int)oracle_cell_width(before, entry->format, limit),
                    value_y, CREAM, collect ? group + 1 : -1, limit);
        oracle_cell(after, entry->format, after_left, value_y, color, collect ? group + 3 : -1, limit);
    }
}

static void check_helper(unsigned which, unsigned before, unsigned after, int missing, unsigned background) {
    const StatCase *entry = &stats[which];
    memset(actual.pixels, (int)background, PIXELS);
    memset(expected, (int)background, PIXELS);
    if (which < 4) stat(before, after, (int)entry->id, entry->x, entry->format);
    else detail_stat(before, after, entry->id, entry->x, entry->format, entry->lower, missing);
    expected_stat(which, before, after, missing, 1);
    exact_canvas(stat_names[which], before, after);
    ++helper_cases;
}

static void check_values(void) {
    unsigned format, value, parity, background, which;
    for (format = 0; format < 4; ++format) {
        unsigned first = format == 1 ? 0 : format == 2 ? 900 : 0;
        unsigned last = format == 1 ? 196 : format == 2 ? 1100 : format == 3 ? 402 : 999;
        for (value = first; value <= last; ++value) for (parity = 0; parity < 2; ++parity) for (background = 0; background < 2; ++background) {
            memset(actual.pixels, background ? 0x5a : 0, PIXELS);
            memset(expected, background ? 0x5a : 0, PIXELS);
            value_number(value, format, 10 + (int)parity, 10, GOLD);
            oracle_value(value, format, 10 + (int)parity, 10, GOLD, -1);
            assert(value_width(value, format) == oracle_value_width(value, format));
            exact_canvas("decimal", value, format);
            ++helper_cases;
        }
    }
    assert(number_width(0) == 4 && number_width(9) == 4 && number_width(10) == 9);
    assert(number_width(99) == 9 && number_width(100) == 14 && number_width(999) == 14);
    assert(heart_width(180) == 22 && heart_width(196) == 22); /* Widest authored fraction and a future-capacity regression case. */
    for (value = 96; value <= 196; value += 4) assert(heart_width(value) <= 22);
    assert(fixed_width(988, 1) == 17 && fixed_width(994, 1) == 17);
    assert(fixed_width(1100, 1) == 22 && fixed_width(1000, 1) == 22);
    for (which = 0; which < 7; ++which) {
        const StatCase *entry = &stats[which];
        for (value = entry->first; value <= entry->last; value += entry->step) for (background = 0; background < 2; ++background) {
            unsigned other;
            unsigned alternatives[5] = {value, entry->first, entry->last,
                value > entry->first ? value - entry->step : value,
                value < entry->last ? value + entry->step : value};
            for (other = 0; other < 5; ++other)
                check_helper(which, value, alternatives[other], 0, background ? 0x5a : 0);
        }
    }
    /* Defensive future quarter, alongside the authored 11.25 fractional value. */
    check_helper(2, 180, 196, 0, 0);
    check_helper(2, 196, 180, 0, 0x5a);
    check_helper(4, 0, 402, 1, 0);
    check_helper(4, 402, 0, 1, 0x5a);
}

static void check_digit_edges(void) {
    static const int xs[] = {-4, -3, -1, 0, 1, 235, 236, 237, 239, 240};
    static const int ys[] = {-7, -6, -1, 0, 1, 152, 153, 154, 159, 160};
    unsigned digit, xi, yi, background;
    for (digit = 0; digit < 11; ++digit)
        for (xi = 0; xi < sizeof xs / sizeof xs[0]; ++xi)
            for (yi = 0; yi < sizeof ys / sizeof ys[0]; ++yi)
                for (background = 0; background < 2; ++background) {
                    int row, column;
                    memset(actual.pixels, background ? 0x5a : 0, PIXELS);
                    memset(expected, background ? 0x5a : 0, PIXELS);
                    digit_blit(digit, xs[xi], ys[yi], GOLD);
                    for (row = 0; row < 7; ++row) for (column = 0; column < 4; ++column) {
                        int x = xs[xi] + column, y = ys[yi] + row;
                        if (x >= 0 && x < WIDTH && y >= 0 && y < HEIGHT &&
                            oracle_digits[digit][row * 4 + column] == '#')
                            pixel(expected, x, y, GOLD, -1);
                    }
                    exact_canvas("clipped digit", digit, xi * 10 + yi);
                    ++helper_cases;
                }
}

static void check_synthetic(void) {
    static const unsigned boundaries[] = {
        0, 4, 96, 97, 98, 100, 156, 159, 160, 161, 180, 192, 196,
        402, 999, 1000, 1100, 9999, 10000, 15999, 16000, 65535, 65536, UINT_MAX
    };
    unsigned which, i, side, format, parity, limit, background;
    for (which = 0; which < 7; ++which)
        for (i = 0; i < sizeof boundaries / sizeof boundaries[0]; ++i)
            for (side = 0; side < 3; ++side) {
                unsigned before = side == 1 ? stats[which].first : boundaries[i];
                unsigned after = side == 0 ? stats[which].last : boundaries[i];
                check_helper(which, before, after, 0, side & 1 ? 0x5a : 0);
                ++synthetic_cases;
            }
    /* All quarter values through the three-digit integral limit are either
     * exact or explicitly unsupported. No synthetic overflow may round them. */
    for (i = 0; i <= 15996; i += 4) {
        check_helper(2, i, i, 0, 0);
        ++synthetic_cases;
    }
    /* Every exact sixteenth in the shipped capacity band, including widths
     * that cannot fit a primary cell, has a defined and safe cell fallback. */
    for (i = 96; i <= 196; ++i) {
        check_helper(2, i, 196, 0, 0x5a);
        ++synthetic_cases;
    }
    for (format = 0; format < 6; ++format)
        for (i = 0; i < sizeof boundaries / sizeof boundaries[0]; ++i)
            for (limit = 22; limit <= 31; limit += 9)
                for (parity = 0; parity < 2; ++parity)
                    for (background = 0; background < 2; ++background) {
                        unsigned n = boundaries[i];
                        memset(actual.pixels, background ? 0x5a : 0, PIXELS);
                        memset(expected, background ? 0x5a : 0, PIXELS);
                        cell_number(n, format, 10 + (int)parity, 10, GOLD, limit);
                        oracle_cell(n, format, 10 + (int)parity, 10, GOLD, -1, limit);
                        assert(cell_width(n, format, limit) == oracle_cell_width(n, format, limit));
                        exact_canvas("synthetic cell", n, format);
                        ++synthetic_cases;
                    }
}

static void check_text(const UiText *value) {
    unsigned parity, background;
    for (parity = 0; parity < 2; ++parity) for (background = 0; background < 2; ++background) {
        memset(actual.pixels, background ? 0x5a : 0, PIXELS);
        memset(expected, background ? 0x5a : 0, PIXELS);
        text_spans(value, 10 + (int)parity, 10, CREAM);
        oracle_text(value, 10 + (int)parity, 10, CREAM, -1);
        exact_canvas("text parity", parity, background);
        ++text_cases;
    }
}

static unsigned fixture_context(unsigned label_id) {
    unsigned expected_context = label_id;
    memset(&fixture_comparison, 0, sizeof fixture_comparison);
    fixture_comparison.before.power_cooldown = EQUIPMENT_BASE_POWER_COOLDOWN;
    fixture_comparison.after.power_cooldown = EQUIPMENT_BASE_POWER_COOLDOWN;
    fixture_before = (GearPreview){32, 0, 96, 988, 100, 167, 29, 0, EQUIPMENT_SWORD};
    fixture_after = (GearPreview){80, 8, 180, 994, 92, 154, 156, 3, EQUIPMENT_SWORD};
    selected_command = 1;
    adventure_save.economy.relics = 0;
    switch (label_id) {
        case GP_SWORD: break;
        case GP_LANCE: fixture_after.weapon_class = EQUIPMENT_LANCE; break;
        case GP_BOW: fixture_after.weapon_class = EQUIPMENT_BOW; break;
        case GP_RECOVERY_CAP:
            fixture_comparison.after.power_cooldown = EQUIPMENT_BASE_POWER_COOLDOWN - 8;
            fixture_after.recovery_updates = fixture_before.recovery_updates;
            fixture_after.recovery_hundredths = fixture_before.recovery_hundredths;
            break;
        case GP_STAGGER_CAP: fixture_before.stagger = fixture_after.stagger = 3; break;
        case GP_SAME: fixture_after = fixture_before; break;
        case GP_NO_COMMAND: selected_command = 0; break;
        default: abort();
    }
    if (gear_menu_slot == EQUIPMENT_WEAPON && (label_id == GP_RECOVERY_CAP || label_id == GP_STAGGER_CAP))
        expected_context = GP_SWORD;
    assert(context_label(&fixture_comparison, &fixture_before, &fixture_after, selected_command) == expected_context);
    return expected_context;
}

static void expected_menu(unsigned item_label, unsigned context, int header) {
    static const unsigned tabs[] = {TX_G_TAB_WEAPON, TX_G_TAB_BODY, TX_G_TAB_BOOTS, TX_G_TAB_BELT, TX_G_TAB_RING};
    unsigned i;
    if (header == 2) oracle_text(&ui_texts[TX_G_BUSY], (WIDTH - ui_texts[TX_G_BUSY].width) / 2, 33, GOLD, BUSY);
    else {
        oracle_label(GP_TITLE, 14, 33, GOLD, TITLE);
        oracle_label(header ? GP_PREVIEW : GP_EQUIPPED, 185, 33, TEAL, STATUS);
    }
    oracle_label(GP_LEFT, 12, 49, TEAL, LEFT);
    oracle_label(GP_RIGHT, 216, 49, TEAL, RIGHT);
    for (i = 0; i < 5; ++i) {
        int x = 30 + (int)i * 38;
        if ((int)i == gear_menu_slot) {
            int row, column;
            for (row = 49; row < 64; ++row) for (column = x - 3; column < x + 30; ++column)
                pixel(expected, column, row, PAL_STONE2, -1);
        }
        oracle_text(&ui_texts[tabs[i]], x, 49, (int)i == gear_menu_slot ? GOLD : CREAM, TAB0 + (int)i);
    }
    oracle_label(GP_UP, 12, 65, TEAL, UP);
    oracle_label(GP_DOWN, 216, 65, TEAL, DOWN);
    oracle_text(&ui_texts[item_label], (WIDTH - ui_texts[item_label].width) / 2, 65, GOLD, NAME);
    expected_stat(0, fixture_before.attack, fixture_after.attack, 0, 1);
    expected_stat(1, fixture_before.defense, fixture_after.defense, 0, 1);
    expected_stat(2, fixture_before.hearts, fixture_after.hearts, 0, 1);
    expected_stat(3, fixture_before.walk_tenths, fixture_after.walk_tenths, 0, 1);
    expected_stat(4, fixture_before.recovery_hundredths, fixture_after.recovery_hundredths, !selected_command, 1);
    expected_stat(5, fixture_before.distance, fixture_after.distance, 0, 1);
    expected_stat(6, fixture_before.stagger, fixture_after.stagger, 0, 1);
    oracle_center(context, 124, TEAL, CONTEXT);
    oracle_center(GP_FOOTER, 138, TEAL, FOOTER);
}

static void check_menus(void) {
    unsigned i, context, header;
    assert(EQUIPMENT_AUTHORED_COUNT == 48);
    for (i = 0; i < GP_COUNT; ++i) check_text(&gear_preview_texts[i]);
    check_text(&ui_texts[TX_G_BUSY]);
    check_text(&ui_texts[TX_PF_STARTER]);
    check_text(&ui_texts[TX_PF_UNEQUIP]);
    for (i = 0; i < 5; ++i) check_text(&ui_texts[TX_G_TAB_WEAPON + i]);
    for (i = 0; i < EQUIPMENT_AUTHORED_COUNT; ++i) {
        int id = name_id(equipment_authored_ids[i]);
        assert(id != TX_G_EMPTY);
        check_text(&ui_texts[id]);
    }
    for (i = 0; i < EQUIPMENT_AUTHORED_COUNT + 5; ++i) for (context = GP_SWORD; context <= GP_NO_COMMAND; ++context) for (header = 0; header < 3; ++header) {
        unsigned item_label, expected_context;
        memset(&adventure_save, 0, sizeof adventure_save);
        if (i < EQUIPMENT_AUTHORED_COUNT) {
            unsigned item = equipment_authored_ids[i];
            gear_menu_slot = equipment_definitions[item].slot;
            gear_menu_candidate = 0;
            adventure_save.equipment.bag[0].item_id = (EquipmentItemId)item;
            item_label = (unsigned)name_id(item);
        } else {
            gear_menu_slot = (int)(i - EQUIPMENT_AUTHORED_COUNT);
            gear_menu_candidate = EQUIPMENT_EMPTY_REF;
            item_label = gear_menu_slot == EQUIPMENT_WEAPON ? TX_PF_STARTER : TX_PF_UNEQUIP;
        }
        adventure_save.equipment.equipped[gear_menu_slot] = (EquipmentU8)(header ? 1 : gear_menu_candidate);
        notice = header == 2;
        expected_context = fixture_context(context);
        preview_cache.valid = 0;
        projection_calls = 0;
        memset(actual.pixels, 0, PIXELS);
        memset(expected, 0, PIXELS);
        gear_menu_draw();
        assert(projection_calls == 2);
        expected_menu(item_label, expected_context, (int)header);
        exact_canvas("complete menu", i, context);
        ++menu_cases;
    }
}

static void check_disjoint(void) {
    unsigned a, b, offset, pixels = 0;
    for (a = 0; a < GROUPS; ++a) {
        unsigned count = 0;
        for (offset = 0; offset < PIXELS; ++offset) count += unions[a][offset];
        assert(count); /* No silently missing label/value/component coverage. */
        pixels += count;
        for (b = a + 1; b < GROUPS; ++b) {
            if (b == BUSY && (a == TITLE || a == STATUS)) continue;
            for (offset = 0; offset < PIXELS; ++offset) if (unions[a][offset] && unions[b][offset]) {
                char left[80], right[80];
                describe(a, left, sizeof left); describe(b, right, sizeof right);
                fprintf(stderr, "Gear foreground overlap: %s / %s at %u,%u\n", left, right, offset % WIDTH, offset / WIDTH);
                abort();
            }
        }
    }
    printf("PASS %u nonempty component unions (%u possible pixels): no foreground overlap, all inside 8,31,224,123\n", GROUPS, pixels);
}

static void write_synthetic_screenshot(const char *directory, const char *name, unsigned fixture) {
    char path[4096];
    FILE *output;
    unsigned item = 0, i, context;
    int path_length;
    /* Stable authored weapon name, real menu chrome and projection-only values.
     * The fixture does not claim that 12.25 hearts is reachable in gameplay. */
    for (i = 0; i < EQUIPMENT_AUTHORED_COUNT; ++i)
        if (equipment_definitions[equipment_authored_ids[i]].slot == EQUIPMENT_WEAPON) {
            item = equipment_authored_ids[i];
            break;
        }
    assert(item);
    memset(&adventure_save, 0, sizeof adventure_save);
    gear_menu_slot = EQUIPMENT_WEAPON;
    gear_menu_candidate = 0;
    adventure_save.equipment.bag[0].item_id = (EquipmentItemId)item;
    adventure_save.equipment.equipped[gear_menu_slot] = 1;
    notice = 0;
    context = fixture_context(GP_SWORD);
    if (fixture == 0) {
        fixture_before.hearts = fixture_after.hearts = 196;
        fixture_before.walk_tenths = 1000;
        fixture_after.walk_tenths = 1100;
    } else {
        fixture_before.attack = 17; fixture_after.attack = 71;
        fixture_before.defense = 1; fixture_after.defense = 7;
        fixture_before.hearts = 116; fixture_after.hearts = 180;
        fixture_before.walk_tenths = 977; fixture_after.walk_tenths = 1017;
        fixture_before.recovery_hundredths = 177; fixture_after.recovery_hundredths = 117;
        fixture_before.distance = 71; fixture_after.distance = 117;
        fixture_before.stagger = 1; fixture_after.stagger = 3;
    }
    /* Assert the exact synthetic menu before adding its presentation backdrop. */
    preview_cache.valid = 0;
    projection_calls = 0;
    memset(actual.pixels, 0, PIXELS);
    memset(expected, 0, PIXELS);
    gear_menu_draw();
    assert(projection_calls == 2);
    expected_menu((unsigned)name_id(item), context, 1);
    exact_canvas("synthetic screenshot", fixture, 0);
    memcpy(actual.pixels, background_village, PIXELS);
    render_card_background = 1;
    projection_calls = 0;
    gear_menu_draw();
    assert(projection_calls == 2);
    render_card_background = 0;
    path_length = snprintf(path, sizeof path, "%s/%s.ppm", directory, name);
    assert(path_length > 0 && (unsigned)path_length < sizeof path);
    output = fopen(path, "wb");
    assert(output);
    assert(fprintf(output, "P6\n%d %d\n255\n", WIDTH, HEIGHT) > 0);
    for (i = 0; i < PIXELS; ++i) {
        unsigned packed = game_palette[actual.pixels[i]], channel;
        for (channel = 0; channel < 3; ++channel) {
            unsigned value = (packed >> (channel * 5)) & 31u;
            assert(fputc((int)((value << 3) | (value >> 2)), output) != EOF);
        }
    }
    assert(fclose(output) == 0);
    printf("SYNTHETIC host-rendered 240x160 menu: %s\n", path);
}

int main(int argc, char **argv) {
    assert(argc == 1 || argc == 2);
    assert(GOLD != CREAM && GOLD != PAL_HEART && CREAM != PAL_HEART && TEAL != CREAM);
    check_values();
    check_digit_edges();
    check_synthetic();
    check_menus();
    check_disjoint();
    printf("PASS %u decimal/color/helper cases, %u text parity/background cases, %u complete menus (48 names + 5 removal slots, 7 contexts, 3 headers)\n", helper_cases, text_cases, menu_cases);
    printf("PASS %u synthetic/fallback cases; exact quarter values remain unrounded; oversized/invalid fields are neutral question marks\n", synthetic_cases);
    puts("PASS exact helper Q4 0..196; quarter-heart 22px limit; tenths 900..1100 including 98.8/99.4; hundredths 0..402; neutral/up/down colors and lower-is-better recovery; absent-command dashes");
    if (argc == 2) {
        write_synthetic_screenshot(argv[1], "synthetic-gear-hearts-12p25-speed-100p0-to-110p0-native", 0);
        write_synthetic_screenshot(argv[1], "synthetic-gear-mixed-1-7-decimals-native", 1);
    }
    return 0;
}
