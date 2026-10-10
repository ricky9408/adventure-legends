/* Real generated UiRun masks plus an independent decimal/color/layout oracle.
 * UI fixtures isolate the production menu draw from gameplay, covered by the
 * effective-preview test. No GBA RAM, generated-text edits, or font substitutes.
 */
#include <assert.h>
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

/* Individual components can vary independently. Alternatives within one group
 * are unioned; BUSY replaces TITLE and STATUS. Background/highlight fills are
 * intentionally excluded from foreground-intersection checks.
 */
enum {
    TITLE, STATUS, BUSY, TAB0, TAB1, TAB2, TAB3, TAB4,
    LEFT, RIGHT, UP, DOWN, NAME, CONTEXT, HELP, FOOTER, FIRST_STAT,
    GROUPS = FIRST_STAT + 7 * 4
};
static unsigned char unions[GROUPS][PIXELS];
static const char *const chrome_names[] = {
    "title", "status", "busy", "weapon tab", "body tab", "boots tab", "belt tab", "ring tab",
    "left", "right", "up", "down", "candidate name", "context", "units", "footer"
};
static const char *const stat_names[] = {"attack", "defense", "hearts", "walk", "recovery", "distance", "stagger"};
static const char *const parts[] = {"label", "before", "arrow", "after"};
static unsigned helper_cases, menu_cases, text_cases;

static void describe(unsigned group, char *buffer, size_t length) {
    if (group < FIRST_STAT) snprintf(buffer, length, "%s", chrome_names[group]);
    else snprintf(buffer, length, "%s %s", stat_names[(group - FIRST_STAT) / 4], parts[(group - FIRST_STAT) % 4]);
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
        unions[group][y * WIDTH + x] = 1;
    }
}

void rect(int x, int y, int w, int h, unsigned char color) {
    int row, column;
    assert(w > 0 && h > 0);
    for (row = 0; row < h; ++row) for (column = 0; column < w; ++column)
        pixel(actual.pixels, x + column, y + row, color, -1);
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
    /* The panel fill is transparent in this foreground-only test canvas. */
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

static const unsigned char oracle_digits[10][5] = {
    {7,5,5,5,7}, {2,6,2,2,7}, {7,1,7,4,7}, {7,1,7,1,7}, {5,5,7,1,1},
    {7,4,7,1,7}, {7,4,7,5,7}, {7,1,1,1,1}, {7,5,7,5,7}, {7,5,7,1,7}
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
    for (; *value; ++value) width += *value == '.' ? 2u : 4u;
    return width - 1;
}

static void oracle_value(unsigned value, unsigned format, int x, int y, int color, int group) {
    char buffer[32];
    const char *cursor;
    oracle_string(value, format, buffer);
    for (cursor = buffer; *cursor; ++cursor) {
        if (*cursor == '.') { pixel(expected, x, y + 4, (unsigned char)color, group); x += 2; }
        else {
            unsigned row, column;
            for (row = 0; row < 5; ++row) for (column = 0; column < 3; ++column)
                if (oracle_digits[(unsigned)(*cursor - '0')][row] & (4u >> column))
                    pixel(expected, x + (int)column, y + (int)row, (unsigned char)color, group);
            x += 4;
        }
    }
}

static unsigned oracle_value_width(unsigned value, unsigned format) {
    char buffer[32];
    oracle_string(value, format, buffer);
    return oracle_width(buffer);
}

static void oracle_arrow(int x, int y, int group) {
    int column;
    for (column = 0; column < 5; ++column) pixel(expected, x + column, y + 1, TEAL, group);
    pixel(expected, x + 3, y, TEAL, group);
    pixel(expected, x + 3, y + 2, TEAL, group);
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
    {GP_ATTACK, 32, 80, 1, 0, 14, 0}, {GP_DEFENSE, 0, 8, 1, 0, 68, 0},
    {GP_HEART, 96, 192, 4, 1, 122, 0}, {GP_WALK, 900, 1100, 1, 2, 176, 0},
    {GP_RECOVERY, 0, 402, 1, 3, 14, 1}, {GP_DISTANCE, 29, 156, 1, 0, 86, 0},
    {GP_STAGGER, 0, 3, 1, 0, 158, 0}
};

static void expected_stat(unsigned which, unsigned before, unsigned after, int missing, int collect) {
    const StatCase *entry = &stats[which];
    int group = collect ? FIRST_STAT + (int)which * 4 : -1;
    int color = before == after ? CREAM : ((after > before) != entry->lower ? GOLD : PAL_HEART);
    int detail = which >= 4;
    oracle_label(entry->id, entry->x, detail ? 95 : 80, CREAM, group);
    oracle_arrow(entry->x + (detail ? 45 : 31), detail ? 101 : 86, collect ? group + 2 : -1);
    if (missing) {
        int column;
        assert(which == 4);
        for (column = 0; column < 3; ++column) {
            pixel(expected, entry->x + 39 + column, 103, CREAM, collect ? group + 1 : -1);
            pixel(expected, entry->x + 52 + column, 103, CREAM, collect ? group + 3 : -1);
        }
    } else {
        oracle_value(before, entry->format, entry->x + (detail ? 43 : 30) - (int)oracle_value_width(before, entry->format),
                     detail ? 101 : 86, CREAM, collect ? group + 1 : -1);
        oracle_value(after, entry->format, entry->x + (detail ? 52 : 37), detail ? 101 : 86,
                     color, collect ? group + 3 : -1);
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
        unsigned first = format == 1 ? 96 : format == 2 ? 900 : 0;
        unsigned last = format == 1 ? 192 : format == 2 ? 1100 : format == 3 ? 402 : 999;
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
    assert(heart_width(180) == 17); /* Actual authored maximum: 11.25 hearts. */
    for (value = 96; value <= 192; value += 4) assert(heart_width(value) <= 17);
    assert(fixed_width(988, 1) == 13 && fixed_width(994, 1) == 13);
    assert(fixed_width(1100, 1) == 17);
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
    check_helper(4, 0, 402, 1, 0);
    check_helper(4, 402, 0, 1, 0x5a);
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
    oracle_center(context, 110, TEAL, CONTEXT);
    oracle_center(GP_UNITS, 124, CREAM, HELP);
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

int main(void) {
    assert(GOLD != CREAM && GOLD != PAL_HEART && CREAM != PAL_HEART && TEAL != CREAM);
    check_values();
    check_menus();
    check_disjoint();
    printf("PASS %u decimal/color/helper cases, %u text parity/background cases, %u complete menus (48 names + 5 removal slots, 7 contexts, 3 headers)\n", helper_cases, text_cases, menu_cases);
    puts("PASS exact Q4 96..192; quarter-heart 17px limit; tenths 900..1100 including 98.8/99.4; hundredths 0..402; neutral/up/down colors and lower-is-better recovery; absent-command dashes");
    return 0;
}
