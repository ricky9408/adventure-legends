# Optional companion trials

All art is original code-native indexed pixel art in the existing bright native GBA palette. Backgrounds are opaque 240×160; the hardware props use transparency index zero. Source is `assets/generate_trials.py`; all generated includes are below 32 KiB. `src/trials.h` is the stable engine contract.

These four authored side activities do not change enemies, mandatory routes, or boss health. Grove discoveries are noncolliding. Partial vane and parcel state is deliberately transient. Reset is safe, free and always reachable. Completing a room leaves its resolved arrangement intact; returning restores that arrangement.

## Persistence and rewards

- `lifetime_field_aid` bits 0–2 record the three restored hearths, bits 3–5 the root beds, bit 6 the wind loom, bit 7 the amber workshop
- Each field aid calls `progression_field` once, then is permanently guarded before any repeat call
- Completing a personal trial marks only the matching story-locked companion's `trial_flags` bit 1/2/4/8
- That companion receives 180 XP and 10 bond, capped at 100 bond. This is an explicit one-time personal-quest exception to the ordinary expedition participation cap
- The existing trial bit guards both rewards, including after leaving/re-entering and after species evolution
- No save5 quest or equipment reservation bytes are touched
- The module does not call `save_game`. Parent checks `trials_event_needs_save` and owns persistence initiation, messages, and optional-room save normalization

## Engine integration

Guard rooms 14/15 before all generic campaign array indexes. `trials_background` supplies an aligned, full 240×160 background for the engine's existing DMA copy. Draw floor effects after the copy, then floating HUD. Include `trials_revision` or `progression_revision` in static render cache keys. All trial mutations increment both.

`trials_draw_actors` uses existing hardware OBJ_PROP slots 0–5 in the grove and optional rooms. Only slot 5 is used in approach rooms 4/9, leaving their existing props alone. Call it after generic campaign props. `obj_add` performs grove camera conversion once; the trial actor API passes raw world coordinates. Grove background effects use x−camera_x,y−camera_y, with no reserved top HUD strip.

`trials_enter` resets partial state and invalidates prop uploads. Supply room 14/15 arrival (120,132). Returning to approach uses (204,86)/(208,140). `trials_exit` recognizes the optional south threshold; parent checks downward input and its existing transition lock. The A result can also request exit.

The parent owns text localization, cooldown/summoning checks, room changes, save5 normalization to the village/elder, and cartridge-level verification. The returned English room labels are lookup hints, not runtime rasterized text.

## Verification

Run `python tests/test_trials.py`. It compiles the actual trial logic plus real creature rules into a host library, then explores every reachable parcel state with integer-pixel navigation and every vane orientation. It proves reset/exit access in every state, one-time rewards, completion-state immutability, collision-safe pushes, unused reserved save bytes, grove routes, and approach entrance/return geometry. This is stronger than a 16px-grid solver: the top-row downward push needs legal y=44/45 standing positions, which a coarse grid would miss.

`validation.json` records the current results. Previews show assets and puzzle geometry; they are developer evidence and should not be used to reveal solutions in ordinary player updates. Integrated ROM/controller testing is a separate parent-owned check.
