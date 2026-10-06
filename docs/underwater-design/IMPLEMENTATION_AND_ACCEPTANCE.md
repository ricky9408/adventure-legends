# Underwater implementation and acceptance contract

Design only. The accompanying checks validate proposed data and a separate Python transaction model. They do not measure or execute Underwater cartridge code. This document contains developer-only solutions and must not appear in spoiler-free player media.

## 1. Exact authoring boundary

Read underwater_allocation.json for the source-pinned audit and catalog_delta.json for the proposed schema2 append. The delta is designed to merge in memory with the current catalog; do not overwrite the live catalog with a truncated fragment. Preserve every existing form, ability, evolution, trial, source and historical relationship. Identity-lock and terminal-topology stay byte-identical. Do not add a new family, change a tier or connect the two branch terminals.

Proposed revision6 totals:89 enabled forms,89 enabled commands,51 edges and142 learn pairs. Command IDs67–90 are unrelated to form IDs49–72. Areas46–53, quests38–45, item IDs6/13/38/54/68/86 and equipment sources31–36 are all separate namespaces. Generic creature reward IDs are not used for these regional grants.

The merged design catalog also contains the pre-existing disabled legendary121. That is why a structural merge has90 authored form rows while the proposed enabled manifest has89. Do not count121 or command12 as delivered content.

## 2. Save revision and immutable historical semantics

Keep wire version5, both6144-byte banks at0x0200 and0x1A00, the5056-byte used payload and1088-byte zero tail,24-byte instance records,160 slots,64 quests,32 region bytes and48 gear records. No Underwater state may be hidden in padding, cosmetic seeds, generic reward bits, event bits or another chapter's flags.

Before implementation, snapshot the finally accepted Magma revision5 policy. The parent is still verifying Magma's legacy-save correction. Its accepted result, not an earlier candidate or mutable live catalog, must become historical revision5 authority. Preserve original revisions1–4 and the final revision5 acceptance set. In particular, do not impose a stricter modern trial/source-causality check on old evolved forms that those revisions legally accepted. Decode old policy first, preserve all typed values, and add no companions, trials, levels, bond, visits, rewards or equipment on load. A current-only release snapshot cannot silently reinterpret old data.

Revision6 uses these new region bytes only:

- byte4: areas46–53 visited, bits0–7; any nonzero value requires town bit0
- byte10: first field sourcesF019–F024, bits0–5; high bits zero
- byte17: first extra individual forF017–F024, bits0–7; provenance, not repeat exhaustion
- byte20: F023 discovery prefix0/1/3
- byte21: F024 discovery prefix0/1/3/7
- anchor byte4: town46 bit0 and Commons47 bit1; each requires its visit

All Underwater bytes, quests and instances require Magma quest32 claimed and Nacreway visited. Areas50–53 require teaching quests38/39 claimed; areas51/52/53 require main quest40 objective prefixes1/3/7 respectively. Preserve those gates even through optional return passages. Spawn2 exists only at46/47 with the matching anchor; other rooms use explicit entrance and return spawn rows, never arbitrary coordinates loaded from a save.

A first-source receipt is quest38/39 or its field bit. It requires a real retained member of the exact family and appropriate obtained history. Current Underwater-family instances require their source receipt. An extra receipt additionally requires at least two retained members and evidence of a retained authored terminal branch. Trial bits require the exact current family mask0/1/2/3; new terminals require their own branch bit and personal training floor. New fields must be rejected in v1–v5 banks. Do not retroactively apply these new-family rules to old families.

Preserve prospective terminal admission:72 final opportunities plus88 extra copies fit160 slots. Obtained-history bits are not individuals. A safe action may spend spare capacity while keeping all missing opportunities reserved. A grandfathered unsafe state remains loadable/saveable; forward grants or evolutions are allowed only when they do not worsen excess or viable coverage. Do not convert the admission test into save validity. All denial paths are byte-identical and keep invitations READY.

Required migration tests: original fixtures and exact historical differential; all16-bit malformed masks for new families; recomputed-CRC cross-revision forms/commands/quests/items/flags; both-bank interruption/fallback; unknown revisions; no-write failures; old legal weakened trial/bond receipts; and current revision6 resave of every accepted historical fixture. Test every interrupted write offset through6144-byte banks with the final policy, not a candidate compiled before a fix.

## 3. Per-instance trial and branch receipts

The16 trial bindings are qualified by family plus local key1 or2. They use wire masks1 and2 with no mutual prerequisite. Both may be earned on one base, but the player explicitly chooses one terminal. Each branch retains completed bits and its inherited base command. Once evolved there is no lateral branch conversion or downgrade.

A transient trial lock records roster slot, instance_id, exact base form, family, local key, source token, base command and room-attempt generation. Geometry receipts are generated only by that selected individual's actual tagged casts and distinct objective interactions. Changing selected individual, party mapping, form, scene, load or death invalidates unfinished proof. A capability in storage, family history, global aid bit or another copy's completed trial cannot authorize completion.

Completion stages one individual, ORs exactly one qualified bit, raises only that individual's level to at least28 and bond to at least45, validates it, then commits. Never copy the full Save5State onto the stack. Completing an already-recorded key returns UNCHANGED before training floors or credit. A new individual's honest repeat trial can earn its personal floor even when global first-aid XP is already spent.

Evolution preview locks slot+instance_id+source+target. A revalidates all eligibility and prospective admission; B/Start/Select decline unchanged. Mixed direction+A never accidentally accepts. Left/right selects the displayed branch, and no legacy ambiguous lookup chooses the first edge. The full target identity and loss of the other path must be visible before confirmation.

Eight repeat flows in acquisition_contracts.json each have a distinct encounter demonstration. Availability needs first-source receipt and a retained terminal in that family. A successful solved attempt creates one genuine new base with fresh monotonic identity, zero trial flags, bounded grant level and bond20. It gives no duplicate gear, quest, XP, event or bond reward. The attempt-generation receipt is consumed on success. Held A and reopening the same solved interaction cannot grant again. A new explicit attempt after leaving/re-entering or RESET may grant another, subject to admission. The first-extra persistent bit never substitutes for an actual second individual and never blocks all further invitations.

## 4. Event and reward namespace

Preserve all ordinary IDs0–179, Southern180–191, Magma220–231 and240–247. Underwater encounter rows are47→256–259,48→260–261,50→262,51→263–264,52→265,53→266–267. Unknown area/slot returns512. Quest IDs38–45 map explicitly to ordinary XP events280–287. Neither event map uses unbounded area multiplication for new content.

Trial aids62–77 map to events446–461. First field sourcesF019–F024 use aids78–83, events462–467. First teaching recruits use their quest reward events. Ordinary events stay below384; field events are384+index with index below128. First-aid receipts protect XP only; they are never trial, quest, source or evolution authority. Repeating a source or already-completed trial does not clear or replay them.

Equipment sources31–36 are one-time, mapped to exact item IDs. Quest45 has an atomic two-item bundle. Stage the512-byte equipment state before any other reward mutation. Full bag leaves every reward/state byte unchanged; previously seen/discarded unique items can settle their source without creating a duplicate. No main quest grants gear, so a full bag cannot gate the two teaching companions or the archive ending.

## 5. World and controller behavior

Render the full240×160 world behind a small floating HUD. Preserve smooth diagonal movement, same input response and existing roll/sword behavior. Underwater is a visual/material setting, not an oxygen timer, slippery-control mode or punitive speed modifier. Layered depth is an explicit tagged puzzle state; no unbounded z-axis or water bypass of collision/story gates.

A interacts/inspects as currently taught. R starts the selected companion command. Existing L/Select/Start and two-command selection keep their current roles. Every new power works with its default facing parameters; optional direction input during its short startup changes only the documented side/orientation once. Direction input must not restart startup, reset cooldown or create a second cast. For Wicktrace only, a12-active-update sample records player positions; it never moves the player itself. Pause, dialogue, picker, hitstop and save transitions freeze action ages exactly as the existing command runtime requires.

The two teaching bases must solve every mandatory target. Tag source identity plus geometry, not phase alone: a Water command is not blanket permission to echo and an Earth weapon is not blanket permission to shift ballast. The correct base signature must actually reach the target. Retained base commands work after either branch. A weapon with matching phase carries no field magic.

RESET is always clearly drawn, safely reachable and outside movable-object collision. Wrong states give feedback without consuming resources. A solid-state change that overlaps the player is refused or delayed with an explanation; never shove them through scenery. Explicit RESET may return them to a verified safe landing. Re-entry restores a canonical unfinished room arrangement while keeping earned objective receipts. Main-room gates must validate current quest prefixes, including through optional passages and saved return spawns.

## 6. Combat implementation budget

Use one snapshotted Underwater cast. It owns at most two moving entities in this design, below the existing three-object ceiling. Procedural multi-tip shapes count as one shape but must still satisfy bounded collision/sample and OAM budgets. Six enemy slots each use a spawn-generation identity receipt; recycled slots cannot inherit damage immunity or receive stale repeated hits. Damage caps are16Q4 for bases and24Q4 for terminals per target per cast. Walls/line-of-sight clip every relevant sweep. No terrain drilling, boss displacement, boss windup retiming, general invulnerability, unlimited projectile reflection or hidden armor bypass.

Geometry changes invalidate the blocked portion of an active shape without extending age/cooldown or clearing hit receipts. Selection changes never reset an active cast. New room, death, load and new game clear transient casts/proofs. Each of24 handlers requires independent tests of startup, active interval, expiration, wall/corner clipping, ordinary foe, phased foe, armored foe, boss vulnerability, slot reuse, switch during cast, pause and death. Distinct prose primitives are not proof that the implemented hitboxes differ.

## 7. Native art and readability acceptance

Produce original pixel art for all24 forms: four directions × four walk frames at16×16, three ability poses per direction, and32×32 portraits. No rescaled base posing as an evolution; no palette-only families. Actual native-size pixels must make the listed limbs, negative spaces, materials and motion readable. Reject a silhouette if it cannot express the card at16 pixels; simplify its concept deliberately rather than stretching the sprite past allocated tiles.

Review all24 silhouettes in black, together and beside the existing65. Each pair of branches needs a different center of mass, at least one different major negative-space feature and a different locomotion cycle. Blind visual review must distinguish cuttlefish from the old planthopper, clam from snail, star from urchin, and comb-jelly from the existing medusa. Mechanical cards must be reviewed beside their explicitly named old ability cousins. Shapes and visual timing must communicate the actual hit regions; bright decoration must not fill intended safe gaps.

Region art needs distinct occupied town/exploration/room layouts, foreground/background separation, large landmarks, coherent light and water depth, warm points of life and low-noise combat ground. No repetitive arena backgrounds. Export previews at1× and nearest-neighbor enlargement. Player-facing captures show town, travel and early teaching only, with no trial solutions, secret routes, late forms or finale.

## 8. Native resource and cadence gates

The current source-pinned baseline is recorded in underwater_allocation.json. Estimated incremental ROM is1,890,304 bytes under a2,097,152-byte cap. New mutable EWRAM cap8192 bytes; single-cast512, room state256, trial proof192 and render staging1024 are explicit sub-budgets. Existing6144-byte save scratch and512-byte equipment stage are reused. No additional full-save snapshot or heap allocator.

Current IWRAM code is approximately27.95KB, close to the28,672-byte code ceiling. New code stays in ROM unless profiling proves a hot helper necessary; maximum additional IWRAM384 bytes, keeping at least4096 bytes reserved for stack. The linker must not use a broad *game.o pattern that silently pulls all new chapter code into IWRAM. Measure real stack high-water under max roster, branch picker, dual-item reward and save, including interrupt overhead.

OBJ VRAM already ends at16,256 of16,384 bytes. Allocate zero new resident OBJ bytes. Stream through the existing20 regional16×16 slots and existing effect glyph slots; preserve heart, arrow, command, phase and water glyph offsets. Hard Underwater OAM budget112 stays below the engine's120-object drop threshold; ambient decoration gets at most8 and yields before meaningful actors. Validate scanline limits and OAM peaks, not only total tile bytes.

Target one simulation update and one presented page flip per59.7275Hz hardware frame,280,896 cycles. Measure full update+save+draw+OAM timing at WAITCNT0x4317 on final ARM build. Hard active-play maximum280,896 cycles, representative p99 target267,000. Do not claim59.73Hz from the game's update counter alone. Track VBlank crossings and presented pages independently, including rapid scroll, maximum ordinary enemies/shots, each complex shape, HUD changes, menu reopen, trial reset, saving and50 real retained individuals. Capture max160 legal/48 gear stress separately. Never silently skip simulation or rendering to satisfy a reported counter.

Default incremental save budget1024, existing maximum3072; profile combined frames, not an isolated save-step benchmark. If a heavy cast plus save exceeds budget, reduce bounded save work while preserving action updates and eventual completion. Do not add mandatory timing puzzles before proving those controls at native speed. Actual hardware results and untested conditions must be labeled honestly.

## 9. Required acceptance runs and stopping conditions

1. Schema/topology/source audit, immutable released relations and every old host suite
2. New host behavior:32-bit inputs, wrong family/key/form, all branch masks, stale instance/attempt IDs, repeated/held confirm, full/reserved/id-exhausted failures, gear bundle rollback, no-write save failure
3. Controller-only minimal route from an eligible old save: starter sword1 plus guaranteed49/52, no optional old quest, no evolution, no grind; death/retry and independent reboot at each main checkpoint
4. Controller-only collection run:16 separately identified new individuals; all24 new history forms; all eight opposite branches; source repeats with no duplicate XP/gear; save/reboot50 retained/89 history; no game-RAM writes or fabricated receipts
5. All24 command scenarios, actual1× art and pixel/collision snapshots, all eight rooms, all optional returns and wrong-way gate attempts
6. Full-frame cadence, OAM/VRAM/ROM/RAM/stack budgets, cold menus and loaded collection sizes
7. Re-run after the final code or asset change; hash ROM/symbols/sources and freeze the exact accepted build

Do not call Underwater implemented or89 forms delivered before all seven stages pass. If a native gate fails, keep the new milestone unreleased, report the failing evidence and repair it. This proposal provides a bounded next task, not a claim that the remaining63 forms are already playable.
