#!/usr/bin/env python3
"""Production evolution UI, with explicit synthetic host engine bridges.

Runs actual progression.c, creature catalog/admission, quest context, generated
UiText and portrait assets. Most states are intentionally synthetic valid
rosters, not claimed native acquisition or valid completed quest/save histories.
The frozen Southern save smoke test alone loads an actual delivered fixture.
Host pixel captures reconstruct the engine's UiRun/framebuffer contract; they
are not emulator screenshots. No native timing or hardware claim is made.

Run: python3 tests/test_magma_evolution_ui.py
Optional host images: MAGMA_EVOLUTION_CAPTURE_DIR=/tmp/evolution-ui ...
Optional sanitizers: MAGMA_EVOLUTION_SANITIZERS=address,undefined (preload ASan
when running under Python, with ASAN_OPTIONS=detect_leaks=0).
"""
from pathlib import Path
import ctypes as C
import hashlib
import json
import os
import re
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
TMP = tempfile.TemporaryDirectory(prefix="magma-evolution-ui-")
OUT = Path(TMP.name)
CC = os.environ.get("HOST_CC", "cc")
FLAGS = ["-std=c99", "-O1", "-g", "-Wall", "-Wextra", "-Werror", "-fPIC",
         "-DSAVE4_HOST_TEST", "-DSAVE5_HOST_TEST", "-Isrc"]
if os.environ.get("MAGMA_EVOLUTION_SANITIZERS"):
    FLAGS += ["-fsanitize=" + os.environ["MAGMA_EVOLUTION_SANITIZERS"], "-fno-omit-frame-pointer"]
# Function instrumentation is confined to the actual core object. It counts
# internal full-roster/catalog validation as well as UI-facing calls.
subprocess.run([CC, *FLAGS, "-finstrument-functions", "-fno-inline", "-c",
                "src/creatures.c", "-o", str(OUT / "creatures.o")], cwd=ROOT, check=True)
MODULES = ["progression", "creature_data", "equipment", "equipment_data", "save4", "save5",
           "magma_quests", "southern_quests", "northern_quests", "regional_quests",
           "campaign_rules", "progression_events", "evolution_art", "regional_creature_art",
           "northern_creature_art", "southern_creature_art", "magma_creature_art", "ui", "assets"]
subprocess.run([CC, *FLAGS, "-shared", "-Wl,-Bsymbolic", "tests/magma_evolution_ui_host.c",
                str(OUT / "creatures.o"), *[f"src/{m}.c" for m in MODULES],
                "-o", str(OUT / "test.so")], cwd=ROOT, check=True)
L = C.CDLL(str(OUT / "test.so"))

A, B, SELECT, START, RIGHT, LEFT, UP, DOWN = 1, 2, 4, 8, 16, 32, 64, 128
PAUSE, CONFIRM, ANIM = 3, 7, 8
READY, INVALID, NO_EDGE, LEVEL, BOND, STORY, TRIAL, SANCTUARY, DEFERRED, AMBIGUOUS, RESERVED = range(11)
MAGMA, CALDERA = 256, 512
BRANCHES = (37, 40, 43, 46)
PALETTE_IDS = {name: int(value) for name, value in re.findall(
    r"#define (PAL_\w+) (\d+)", (ROOT / "src/assets.h").read_text())}


class Draw(C.Structure):
    _fields_ = [(name, C.c_int) for name in ("kind", "id", "x", "y", "w", "h", "color")]


def u(name):
    return C.c_uint.in_dll(L, name).value


def iv(name, value=None):
    obj = C.c_int.in_dll(L, name)
    if value is not None:
        obj.value = value
    return obj.value


def draws(kind=None):
    result = list((Draw * 128).in_dll(L, "host_draws"))[:u("host_draw_count")]
    return [d for d in result if kind is None or d.kind == kind]


def capture(name):
    destination = os.environ.get("MAGMA_EVOLUTION_CAPTURE_DIR")
    if not destination:
        return
    from PIL import Image
    directory = Path(destination)
    directory.mkdir(parents=True, exist_ok=True)
    palette = (C.c_ushort * 256).in_dll(L, "game_palette")
    colors = [(v & 31, (v >> 5) & 31, (v >> 10) & 31) for v in palette]
    raw = bytes((C.c_ubyte * (240 * 160)).in_dll(L, "host_pixels"))
    rgb = bytes(c * 255 // 31 for index in raw for c in colors[index])
    Image.frombytes("RGB", (240, 160), rgb).save(directory / f"{name}.png")
    (directory / f"{name}.json").write_text(json.dumps({
        "evidence": "synthetic host raster, actual progression draw calls, generated UiText and art; not a native screenshot",
        "progression_sha256": hashlib.sha256((ROOT / "src/progression.c").read_bytes()).hexdigest(),
        "draws": [{n: getattr(d, n) for n, _ in Draw._fields_} for d in draws()],
    }, indent=2) + "\n")


class EvolutionUI(unittest.TestCase):
    def fresh(self, form=37, trial=3, context=MAGMA):
        self.assertEqual(L.host_fresh(form, trial, context), 1)
        self.assertEqual(L.progression_current_form(), form)

    def setUp(self):
        self.fresh()

    def open(self):
        self.assertEqual(L.progression_menu_input(SELECT), 1)
        self.assertEqual(iv("game_state"), CONFIRM)

    def unchanged(self):
        self.assertEqual(L.host_unchanged(), 1, "Save5State changed on a non-commit path")
        self.assertEqual(u("host_saves"), 0)

    def state(self, target, reason=READY, state=CONFIRM):
        self.assertEqual(u("progression_evolution_target"), target)
        self.assertEqual(u("progression_evolution_reason"), reason)
        self.assertEqual(iv("game_state"), state)

    def test_actual_frozen_southern_fixture_loads(self):
        fixture = ROOT / "tests/fixtures/v5-revision4/southern-minimal8-town.sav"
        data = fixture.read_bytes()
        self.assertEqual(len(data), 32768)
        (C.c_ubyte * 32768).in_dll(L, "save5_test_sram")[:] = data
        self.assertEqual(L.host_load_fixture(), 1)
        L.host_snapshot()
        L.progression_draw_tab()
        self.assertEqual(L.host_unchanged(), 1)
        self.assertEqual(u("host_bad_bounds"), 0)

    def test_all_branch_pairs_choose_actual_eligible_alternative(self):
        for base in BRANCHES:
            for trial, target in ((1, base + 1), (2, base + 2), (3, base + 1)):
                with self.subTest(base=base, trial=trial):
                    self.fresh(base, trial)
                    L.host_snapshot()
                    self.open()
                    self.state(target)
                    self.unchanged()
                    L.progression_confirm_input(A)
                    self.assertEqual(L.host_form(0), target)
                    self.assertEqual(iv("game_state"), ANIM)
                    self.assertEqual(L.host_valid(), 1)

    def test_locked_alternative_remains_visible_and_failure_is_atomic(self):
        for base in BRANCHES:
            self.fresh(base, 1)
            self.open()
            L.host_snapshot()
            L.progression_confirm_input(RIGHT)
            self.state(base + 2, TRIAL)
            self.unchanged()
            L.progression_confirm_input(A)
            self.state(base + 2, TRIAL)
            self.unchanged()
            L.host_reset_draw()
            L.progression_draw_confirm()
            self.assertEqual([d.id for d in draws(2)], [base + 1, base + 2])
            self.assertIn(L.host_reason_name(TRIAL), [d.id for d in draws(1)])
            L.progression_confirm_input(LEFT)
            self.state(base + 1)
            self.unchanged()

    def test_both_locked_branches_are_explorable(self):
        self.fresh(37, 0)
        L.host_snapshot()
        self.open()
        self.state(38, TRIAL)
        L.progression_confirm_input(LEFT)
        self.state(39, TRIAL)
        L.progression_confirm_input(A)
        self.unchanged()
        self.assertEqual(iv("game_state"), CONFIRM)

    def test_previously_locked_target_rechecks_new_trial_on_confirm(self):
        self.fresh(37, 1)
        self.open()
        L.progression_confirm_input(RIGHT)
        self.state(39, TRIAL)
        L.host_mutate(6, 0, 3)
        L.progression_confirm_input(A)
        self.assertEqual(L.host_form(0), 39)
        self.assertEqual(iv("game_state"), ANIM)

    def test_reopen_resets_choice_and_binds_current_individual(self):
        self.open()
        L.progression_confirm_input(RIGHT)
        self.state(39)
        L.progression_confirm_input(B)
        self.open()
        self.state(38)
        L.progression_confirm_input(START)
        other = L.host_add(40, 2)
        L.host_select(other)
        self.open()
        self.state(42)
        self.assertEqual(u("progression_evolution_slot"), other)
        L.progression_confirm_input(A)
        self.assertEqual(L.host_form(0), 37)
        self.assertEqual(L.host_form(other), 42)

    def test_actual_selected_individual_not_family_cache(self):
        self.fresh(37, 1)
        other = L.host_add(37, 2)
        grown = L.host_add(39, 2)
        self.assertEqual((other, grown), (1, 2))
        L.host_select(other)
        L.progression_refresh()
        identity = L.host_identity(other)
        self.assertEqual(L.progression_current_form(), 37)
        self.assertEqual((C.c_uint * 30).in_dll(L, "progression_forms")[23], 39)
        L.host_snapshot()
        L.progression_draw_tab()
        self.assertEqual([d.id for d in draws(2)], [37])
        self.assertIn(L.host_name(37), [d.id for d in draws(1)])
        L.progression_select(23)
        self.assertEqual(L.host_identity(other), identity)
        self.open()
        self.assertEqual(u("progression_evolution_slot"), other)
        self.state(39)
        L.progression_confirm_input(A)
        self.assertEqual(L.host_form(other), 39)
        self.assertEqual(L.host_identity(other), identity)
        self.assertEqual(L.host_instance_unchanged(0), 1)
        self.assertEqual(L.host_instance_unchanged(grown), 1)

    def test_cancel_keys_win_over_a_and_every_direction_chord(self):
        # Exhaust every combination containing at least one cancellation key.
        for mask in range(1, 1024):
            if not mask & (B | START | SELECT):
                continue
            with self.subTest(mask=mask):
                self.fresh()
                self.open()
                L.host_snapshot()
                L.host_reset_counts()
                L.progression_confirm_input(mask)
                self.assertEqual(iv("game_state"), PAUSE)
                self.unchanged()
                self.assertEqual(u("host_commits"), 0)
                self.assertEqual(u("host_roster_checks"), 0)

    def test_directions_never_authorize_same_frame_a(self):
        for form, trial in ((37, 3), (31, 1)):
            for directions in range(1, 16):
                for a in (0, A):
                    mask = (directions << 4) | a
                    with self.subTest(form=form, mask=mask):
                        self.fresh(form, trial)
                        self.open()
                        target = u("progression_evolution_target")
                        L.host_snapshot()
                        L.host_reset_counts()
                        L.progression_confirm_input(mask)
                        self.assertEqual(iv("game_state"), CONFIRM)
                        self.unchanged()
                        self.assertEqual(u("host_commits"), 0)
                        expected = 39 if form == 37 and directions in (1, 2) else target
                        self.assertEqual(u("progression_evolution_target"), expected)

    def test_stale_participant_form_and_missing_selection_fail_closed(self):
        for mutation in ("different_individual", "same_slot_replaced", "form_changed", "party_invalid", "unoccupied"):
            with self.subTest(mutation=mutation):
                self.fresh()
                other = L.host_add(37, 3)
                self.open()
                if mutation == "different_individual":
                    L.host_select(other)
                elif mutation == "same_slot_replaced":
                    L.host_mutate(0, 0, 1234)
                elif mutation == "form_changed":
                    L.host_mutate(1, 0, 38)
                elif mutation == "party_invalid":
                    L.host_mutate(2, 0, 255)
                else:
                    L.host_mutate(3, 0, 0)
                L.host_snapshot()
                L.host_reset_counts()
                L.progression_confirm_input(A)
                self.assertEqual(iv("game_state"), PAUSE)
                self.assertEqual(u("host_toast"), L.host_source_changed_name())
                self.unchanged()
                self.assertEqual(u("host_commits"), 0)

    def test_cancel_precedes_stale_participant_check(self):
        self.open()
        L.host_mutate(2, 0, 255)
        L.host_snapshot()
        L.progression_confirm_input(A | B)
        self.assertEqual(iv("game_state"), PAUSE)
        self.assertEqual(u("host_toast"), 0xffffffff)
        self.unchanged()

    def reserve_roster(self, pad_count):
        self.fresh()
        self.assertLess(L.host_add(38, 1), 160)
        for _ in range(pad_count):
            self.assertLess(L.host_add(1, 0), 160)
        self.assertEqual(L.host_valid(), 1)

    def test_admitted_branch_is_preferred_over_locally_ready_reserved_branch(self):
        self.reserve_roster(89)
        self.assertEqual(L.host_excess(), 88)
        self.assertEqual(L.host_status(0, 38), RESERVED)
        self.assertEqual(L.host_status(0, 39), READY)
        L.host_snapshot()
        L.host_reset_counts()
        self.open()
        self.state(39)
        self.assertEqual(u("host_admission_checks"), 2)
        self.assertEqual(u("host_roster_checks"), 2)
        self.unchanged()
        L.progression_confirm_input(LEFT)
        self.state(38, RESERVED)
        L.progression_confirm_input(A)
        self.state(38, RESERVED)
        self.unchanged()
        L.host_reset_draw()
        L.progression_draw_confirm()
        self.assertIn(L.host_reason_name(RESERVED), [d.id for d in draws(1)])
        capture("reserved-first-branch")
        L.progression_confirm_input(RIGHT)
        L.progression_confirm_input(A)
        self.assertEqual(L.host_form(0), 39)
        self.assertEqual(L.host_excess(), 88)

    def test_admission_is_rechecked_at_commit_not_cached_display_reason(self):
        self.reserve_roster(88)
        self.assertEqual(L.host_excess(), 87)
        self.open()
        self.state(38)
        self.assertLess(L.host_add(1, 0), 160)
        self.assertEqual(L.host_excess(), 88)
        self.assertEqual(L.host_status(0, 38), RESERVED)
        L.host_snapshot()
        L.progression_confirm_input(A)
        self.state(38, RESERVED)
        self.unchanged()

    def test_every_requirement_is_rechecked_at_commit(self):
        for issue, expected in (("level", LEVEL), ("bond", BOND), ("story", STORY),
                                ("trial", TRIAL), ("sanctuary", SANCTUARY), ("bad_roster", INVALID)):
            with self.subTest(issue=issue):
                self.fresh()
                other = L.host_add(1, 0)
                self.open()
                if issue == "level": L.host_mutate(4, 0, 25)
                elif issue == "bond": L.host_mutate(5, 0, 44)
                elif issue == "story": L.host_context(0)
                elif issue == "trial": L.host_mutate(6, 0, 0)
                elif issue == "sanctuary": iv("room", 40)
                else: L.host_mutate(0, other, L.host_identity(0))
                L.host_snapshot()
                L.progression_confirm_input(A)
                self.state(38, expected)
                self.unchanged()
                L.host_reset_draw()
                L.progression_draw_confirm()
                self.assertEqual(u("host_bad_bounds"), 0)
                for label in draws(1):
                    self.assertGreaterEqual(label.x, 10)
                    self.assertLessEqual(label.x + label.w, 230)
                    self.assertGreaterEqual(label.y, 37)
                    self.assertLessEqual(label.y + label.h, 153)

    def test_single_edge_locked_open_and_late_failure_are_atomic(self):
        for issue, expected in (("level", LEVEL), ("bond", BOND), ("story", STORY),
                                ("trial", TRIAL), ("sanctuary", SANCTUARY)):
            for late in (False, True):
                with self.subTest(issue=issue, late=late):
                    self.fresh(31, 1)
                    if late: self.open()
                    if issue == "level": L.host_mutate(4, 0, 25)
                    elif issue == "bond": L.host_mutate(5, 0, 44)
                    elif issue == "story": L.host_context(0)
                    elif issue == "trial": L.host_mutate(6, 0, 0)
                    else: iv("room", 40)
                    L.host_snapshot()
                    if late: L.progression_confirm_input(A)
                    else: self.assertEqual(L.progression_menu_input(SELECT), 1)
                    self.assertEqual(iv("game_state"), PAUSE)
                    self.assertEqual(u("host_toast"), L.host_reason_name(expected))
                    self.unchanged()

    def test_sequential_tier_three_keeps_instance_and_waits_for_second_trial(self):
        for base in (31, 34):
            self.fresh(base, 1)
            identity = L.host_identity(0)
            self.open()
            L.progression_confirm_input(A)
            self.assertEqual(L.host_form(0), base + 1)
            self.assertEqual(L.host_trial(0), 1)
            for _ in range(80): L.progression_evolution_tick()
            self.assertEqual(iv("game_state"), PAUSE)
            self.assertEqual(u("host_saves"), 1)
            L.host_context(MAGMA | CALDERA)
            self.assertEqual(L.progression_menu_input(SELECT), 1)
            self.assertEqual(iv("game_state"), PAUSE)
            self.assertEqual(u("host_toast"), L.host_reason_name(TRIAL))
            L.host_mutate(6, 0, 3)
            self.open()
            self.state(base + 2)
            L.progression_confirm_input(A)
            self.assertEqual(L.host_form(0), base + 2)
            self.assertEqual(L.host_identity(0), identity)
            self.assertEqual(L.host_valid(), 1)

    def test_three_single_step_magma_families_commit_exact_target(self):
        for base in (95, 97, 99):
            self.fresh(base, 1)
            self.open()
            self.state(base + 1)
            self.assertEqual(u("progression_evolution_count"), 1)
            L.progression_confirm_input(A)
            self.assertEqual(L.host_form(0), base + 1)
            self.assertEqual(L.host_valid(), 1)

    def test_branch_art_names_layout_and_highlight_at_240x160(self):
        for base in BRANCHES:
            for right in (False, True):
                self.fresh(base, 3)
                self.open()
                if right: L.progression_confirm_input(RIGHT)
                L.host_reset_draw()
                L.progression_draw_confirm()
                self.assertEqual(u("host_bad_bounds"), 0)
                self.assertEqual(u("host_fallbacks"), 0)
                self.assertEqual([d.id for d in draws(2)], [base + 1, base + 2])
                for index, portrait in enumerate(draws(2)):
                    self.assertEqual((portrait.x, portrait.y, portrait.w, portrait.h), (50 + 108 * index, 80, 32, 32))
                    name = next(d for d in draws(1) if d.id == L.host_name(base + index + 1))
                    self.assertGreaterEqual(name.x, 18 + 108 * index)
                    self.assertLessEqual(name.x + name.w, 114 + 108 * index)
                    self.assertLessEqual(name.y + name.h, portrait.y)
                bars = [d for d in draws(0) if d.y == 61 and d.h == 2]
                self.assertEqual(len(bars), 2)
                self.assertNotEqual(bars[0].color, bars[1].color)
                self.assertEqual(bars[int(right)].color, PALETTE_IDS["PAL_GOLD3"])
                self.assertEqual(bars[1 - int(right)].color, PALETTE_IDS["PAL_TEAL2"])
                for label in draws(1):
                    self.assertGreaterEqual(label.x, 10)
                    self.assertLessEqual(label.x + label.w, 230)
                    self.assertGreaterEqual(label.y, 37)
                    self.assertLessEqual(label.y + label.h, 153)
                capture(f"branch-{base}-choice-{int(right)}")

    def test_animation_uses_exact_before_and_selected_target_art(self):
        self.open()
        L.progression_confirm_input(RIGHT)
        L.progression_confirm_input(A)
        for tick, expected in ((0, 37), (35, 37), (36, 39), (79, 39)):
            if tick:
                for _ in range(tick - previous): L.progression_evolution_tick()
            L.host_reset_draw()
            L.progression_draw_evolution()
            self.assertEqual([d.id for d in draws(2)], [expected])
            self.assertEqual(u("host_bad_bounds"), 0)
            self.assertEqual(u("host_saves"), 0)
            previous = tick
        L.progression_evolution_tick()
        self.assertEqual(iv("game_state"), PAUSE)
        self.assertEqual(u("host_saves"), 1)
        self.assertEqual(u("host_sounds"), (1 << 2) | (1 << 4))

    def test_no_full_validation_or_admission_during_render_or_idle_frames(self):
        self.reserve_roster(89)
        self.open()
        L.host_reset_counts()
        L.host_snapshot()
        for _ in range(180):
            L.host_reset_draw()
            L.progression_draw_tab()
            L.progression_draw_confirm()
            L.progression_confirm_input(0)
        self.unchanged()
        for counter in ("host_roster_checks", "host_catalog_checks", "host_admission_checks", "host_commits"):
            self.assertEqual(u(counter), 0, counter)
        L.progression_confirm_input(LEFT)
        self.assertGreater(u("host_admission_checks"), 0)
        self.assertGreater(u("host_roster_checks"), 0)
        self.assertEqual(u("host_catalog_checks"), 0)

    def test_animation_render_and_ticks_do_not_repeat_core_validation(self):
        self.open()
        L.progression_confirm_input(A)
        L.host_reset_counts()
        L.host_snapshot()
        for _ in range(79):
            L.host_reset_draw()
            L.progression_draw_evolution()
            L.progression_evolution_tick()
        self.unchanged()
        for counter in ("host_roster_checks", "host_catalog_checks", "host_admission_checks", "host_commits"):
            self.assertEqual(u(counter), 0, counter)

    def test_no_selection_wrong_tab_and_terminal_form_do_not_open(self):
        for form in (33, 36, 38, 39, 41, 42, 44, 45, 47, 48, 96, 98, 100):
            self.fresh(form, 0)
            L.host_snapshot()
            self.assertEqual(L.progression_menu_input(SELECT), 1)
            self.assertEqual(iv("game_state"), PAUSE)
            self.unchanged()
        self.fresh()
        iv("journal_tab", 2)
        self.assertEqual(L.progression_menu_input(SELECT), 0)
        iv("journal_tab", 3)
        L.host_mutate(2, 0, 255)
        self.assertEqual(L.progression_menu_input(SELECT), 0)
        L.host_reset_draw()
        L.progression_draw_tab()
        self.assertEqual(u("host_bad_bounds"), 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
