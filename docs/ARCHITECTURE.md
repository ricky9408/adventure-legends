# Engine architecture

## Native execution and budgets

The cartridge is a freestanding ARM7TDMI program. `startup.s` enters ARM System mode, copies hot Thumb gameplay code to IWRAM, initializes EWRAM and calls `main`. Cold setup/save/dialogue functions stay in ROM using `.text.rom`. No target libc or libgba is required. The linker reserves at least 4 KiB of IWRAM for the stack and limits cartridge ROM to 32 MiB.

The GBA display cadence is approximately 59.7275 Hz (16,777,216 /280,896 cycles). Hardware timers measure input/update/render execution independently of VBlank wait. Tests also count actual bitmap page changes after each emulated frame; host execution speed is not used as a frame-rate claim.

## Rendering and original assets

Mode 4 uses two 240×160 indexed VRAM pages and a shared RGB555 palette. Moving actors use 8 bpp hardware OBJ tiles beginning at bitmap-mode tile index 512. Assets upload on pose/room/progress changes. Software y-sorting, shadow priority and foreground canopy masks provide depth; modal panels hide intersecting actors. OAM and the bitmap page commit at VBlank.

Static page caching compares exact fields, including room, state, companion, dialogue text/speaker, progression and camera; it does not pack growing identifiers into overlapping bit ranges. Floating status uses transparent hardware OBJ; modal UI remains cached per bitmap page. Long aligned rectangle spans use fixed-source DMA fills. Japanese text is generated into nonzero paired-pixel spans for both halfword alignments, with pixel-exact reconstruction assertions. This avoids decoding thousands of blank glyph bits on a cold menu opening. Generated data stays in deterministic text chunks below 32 KiB rather than giant C blobs.

The grove is a 480×320 continuous world. The current 240×160 viewport has no reserved HUD strip; camera clamps to x 0..240/y 0..160. Even/odd immutable source atlases permit aligned row DMA16 transfers at every camera-x parity. This consumes extra ROM but avoids costly per-frame shifts. Tests compare all four modulo 4 viewport alignments against source pixels.

## Movement, combat and content

Player movement uses Q8 positions: cardinal 320/256 pixels/update and diagonal 226/256 per component. Camera and companion follow ease at subpixel precision. Collision checks all four foot corners and sweeps dodge/lunge movement. Sword combat includes three strikes, bounded buffering, three intentional hit-stop updates on impact and visible particles. Enemy warnings lock aim before firing.

`campaign_rules.*` is generated from editable JSON: 10 new fixed rooms with blocks, gated exits, monotonic puzzle objects, enemies and dialogue; original rooms 0..3 remain separately implemented. Combined requirement masks use room bits 0..15 and chapter bits 16..19. Room transitions clear transient attacks/projectiles and use an entrance lock to prevent bouncing.

The four original story power families have distinct roles: fire projectiles/lighting/armor, nature roots/push/cooldown healing, wind vanes/projectile removal/stagger, and stone weights/one-hit guard/pulse. Power cooldown is shared across selection changes. Bosses expose only during explicitly timed recovery, cannot have vulnerability extended indefinitely, and reset living encounters on retreat. The final core clamps damage at each of its three phase boundaries. Cleared bosses do not respawn.

All content, sprites, dialogue and PSG music are original. Audio uses an ambient square-wave phrase and event effects, not streamed samples.

## Previous-format persistence compatibility

`save4.*` is retained for previous-format validation and migration; save5 below is the current writer. The prior cartridge contract used two 32-byte banks at SRAM 0x40 and 0x80 contain a version, sequence, progression, safe spawn, companion selection and CRC16-CCITT-FALSE. Writes commit an inactive bank and mark it valid last. The newest valid sequence wins using wrap-safe comparison; corruption falls back to the other bank. Legacy bytes 0..12 remain untouched.

Formats 2/3 are read and normalized without changing their source record. A former completed chapter becomes the first lantern plus the wind companion, not completion of the expanded campaign. Reward saves point to a safe village checkpoint before multi-page dialogue finishes. Ending completion and prior unlocks persist independently. Retry/load restores full health at a safe entrance or recorded camp, not an exact mid-combat snapshot.

Host serialization tests cover interrupted writes, every stored-bit corruption, invalid progression and sequence wrap. Real-ROM tests cover the gameplay timing of saves and migration from authenticated prior-ROM fixtures. Emulator save states are a different mechanism; test branches explicitly pair them with matching SRAM.

## Expansion boundaries

The prior 14-area/four-companion campaign is the foundation. Creature evolution/catalog/party, equipment, regional quests and 128 forms are not silently implied by this architecture. The current implementation has 65 forms, equipment and four regional extensions; the remaining 128-form expansion is unfinished. Stable IDs and the non-overwriting save schema are shared across chapters. Required traversal powers must survive evolution and party management. ROM/RAM/OBJ limits and cold as well as steady frame cadence remain release gates.

## Full-screen creature milestone

The newer renderer uses the complete 240×160 world viewport. Grove camera Y clamps to 0..160 and targets player Y−80; sprite transforms subtract camera Y with no 24-pixel offset. DMA copies all 160 source rows without stretching. Existing world art and collision definitions remain byte-identical. Hearts, selected companion, B/R hint and cooldown are small transparent OBJ in the corners. Area names are brief text on entry; the permanent HUD and boss text strips are removed. The old 38,400-byte HUD bitmap cache is no longer needed.

`creatures.*` owns stable form lookup, a bounded 160-record storage model, four active references, levels, bond, event credit, confirmed/deferred evolution and inherited field capabilities. The initial milestone enabled eight forms; the current catalog enables 65. Historical revision validation never consults the expanded live catalog. `progression.*` adapts the old four power families to actual owned forms, adds the growth journal and coordinates save state. The journal exposes party assignment from actual occupied roster records. It never derives new instances from historical obtained-form bits, and exposes no release operation. Unassigned story powers remain recoverable from the owned collection anywhere the journal opens.

`trials.*` provides optional first-aid discoveries, a rotating path puzzle and a resettable movable-object puzzle. Permanent discovery bits and completed personal trials persist separately from transient puzzle arrangements. Personal-trial completion has an explicit one-time +10 bond exception to ordinary expedition caps. Story compensation floors preserve that earned bonus and avoid forced replay after migration. Loading a checkpoint is distinct from actually departing a sanctuary; it does not reset expedition credit.

`advanced_powers.*` separates cast lifetime, per-enemy hit masks, root timers, reflected projectile effect tags and guard charges. Non-fire reflected projectiles cannot activate fire-only scenery. Origin/cell/target line-of-sight checks prevent effects crossing intervening walls. Commands persist through recall/switching until expiry, freeze with the world, and clear on room changes. Movement/guard tradeoffs are explicit; dodge cancels the braced guard.

Save5 uses two 6 KiB banks, immutable snapshots, incremental CRC/semantic validation/write/readback and final commit. The game renders a small saving panel while stepping the writer; actors outside that panel remain visible. Reward dialogue waits until commit. Current four-companion saves take about 18 updates. Checkpoint load decoding is intentionally blocking and separately reported from gameplay/save-writer frame cadence. Details and fault-test contract are in [SAVE5.md](SAVE5.md).

## Quick companion selection and assignment

`quickparty.*` stays in ROM. A held-L input owner runs before simulation timers, hit-stop, movement, combat and effect updates. Opening and release updates are consumed as well. Cardinal mapping is UP=party0, RIGHT=party1, DOWN=party2, LEFT=party3. A fresh single cardinal replaces the candidate; empty and ambiguous combinations clear it. Any direction suppresses tap fallback. A no-direction hold of at most12updates cycles assigned slots, while longer inspection preserves selection. Cancel and modal/room cleanup latch L until release, preventing stale commit/reopening across pause, dialogue, death or transitions.

Selection updates `roster.selected_party`, the legacy power-family `spirit` and `campaign.spirit` together. It does not change summoned status, companion position, cooldowns or active cast lifetime. Art uses owned form metadata; field powers retain family dispatch. A dedicated picker revision is an exact static-page cache key. When every other key matches, only its opaque panel is redrawn over the frozen world; a stale page reuses the other bitmap only when every world-state cache key matches, then repaints the opaque picker. Otherwise it uses the complete renderer. This avoids a camera-movement opening hitch without reusing stale world pixels. Dismissal restores the full world. Intersecting world OBJ and the boss health bar are hidden beneath the picker. The complete240×160 viewport returns on dismissal.

Journal assignment validates occupied roster references, swaps existing members instead of duplicating them and requires at least one assigned member. `creatures_party_set` retains selected instance identity when possible. Required capability mask0 is intentional: all owned instances remain recoverable in the journal, and no release/delete UI exists. Assignment requests the existing paused incremental save transaction. Ordinary field selection waits for a normal checkpoint. Save5 revision1 party bytes and legacy migration are unchanged.

Failed writes keep the prior committed bank intact. A separate modal failure notice survives toast expiry and unrelated feedback, renders above modal panels, and excludes intersecting HUD/world OBJ. Its visibility is an exact cache key independent from picker revisions. Explicit return to play acknowledges the notice without clearing the failure result; new save attempts clear stale feedback, and only successful completion clears the failed-write result. The party-panel assignment path has its own synthetic failure/wait/close/retry regression.

## River-region and equipment extension

- `weapon_actions` owns bounded transient sword/lance/bow clocks, one-hit ledgers and two swept arrows. Modal entry cancels an un-fired bow draw and preserves committed recovery.
- `gear_runtime` caches derived gear stats and uses authoritative sixteenths-of-heart health. The old `hp`, enemy `hp` and `boss_hp` symbols are ceiling-heart observation caches; `max_hp` remains the permanent6/8-heart base. New combat tests read the q4 fields directly.
- Friendly shots snapshot their phase separately from explicit field-effect tags. Mundane arrows cannot ignite a torch merely because they are friendly.
- `obj_layout.h` reserves non-overlapping region actor, partial-heart, arrow, Metal-pin, phase-marker and Water-effect tiles below the16KiB bitmap-mode OBJ limit.
- `region_art` supplies two480×320 aligned/parity worlds and four240×160 interiors. `region_game` owns interaction/puzzle state; `regional_quests` owns atomic in-memory reward/quest transitions; Save5 alone owns persistence.
- Transient unsolved crate/valve/roll arrangements reset on reentry; completed objectives and unique rewards persist. Every reachable crate configuration retains a reset and an exit.
- `progression`/`quickparty` render actual selected instances. Legacy campaign spirit0..3 is only a compatibility fallback; roster-selected Water/Metal remains authoritative after load.
- Yin/Yang and phases are independent catalog axes. Combat multipliers are original game rules, not a claim about canonical traditional numerical values.

Whole-ROM frame cadence, save interruption and source reproducibility remain release gates. Core host/fault fixtures, native controller gameplay and cold blocking load measurements are reported separately.


## Magma integration and performance-sensitive boundaries

`magma_game` owns rooms 38–45, local movable objects, the regulator clock and exact
bitmap revision changes. Every damaging sweep position advances that revision, so
visible geometry and collision stay synchronized. Completed repair objectives restore
the repaired screen after travel/load; unsolved local arrangements remain resettable.
The regulator latch remains usable through undamaged cycles and clears after a
successful open-window hit, avoiding a walk-speed-dependent puzzle lock.

`magma_quests` owns typed source/repeat/trial/discovery transactions. The power and
combat hooks in `magma_powers.c/.h` own bounded paths, distinct commands, effect provenance, identity,
leases and ordinary-enemy interaction. Hostile projectiles and player arrows retain
separate provenance. Normal R dispatch uses the authored default side; synthetic
alternate-side API tests do not imply another player control exists.

Expensive admission and full-state validation are event-only. Collision hot paths use
an inline regional range check; topology caches are refreshed at all necessary points,
without a redundant third full scan in unrelated rooms. The queued anchor preparation
in [SAVE5.md](SAVE5.md) preserves validation while isolating its cost from cold rendering.

Branch evolution UI operates on the actual individual and roster. Any direction
consumes its input frame before A confirmation; only exact left/right changes a branch.
The default branch prefers a roster-admitted target. Cancel, simultaneous directions,
identity changes and full capacity leave ownership intact. Four same-family pairs were
actually earned and exercised through journal assignment and the held-L selector.

The final linked image uses 28,120 bytes of IWRAM code, leaving 552 bytes before the
0x03007000 boundary. Data is 92 bytes and BSS 48,568 bytes. No new permanent OBJ region
was allocated; regional actor budget remains bounded. These are link/static budgets,
not a measured whole-engine stack high-water guarantee. Future audio or chapter code
must respect these limits and repeat native cold-menu and combined-load tests.
