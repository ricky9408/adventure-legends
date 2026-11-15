# Lantern keeper art direction

Emberbond's traveler carries a bronze satchel and a gold scarf. Warm cloth,
auburn hair and a cool coat remain readable against pale paths and dark trees.
Homura has an asymmetric ember tail. Midori is a green leaf canopy over a small
seed, so the first nature power looks like something that can grow a bridge.
Fuuri's separated sails and trailing ribbons communicate air. The first warden
has uneven moss-covered shoulders and a small hearth inside its stone chest.
Enemy shots use a bright central ember and balanced sparks; the same unrotated
sprite reads consistently in every firing direction.

The 49 resident definitions across the village and eight later regions use
different body shapes, hair, clothing and working tools. A person can be
recognized before their dialogue opens. Ressa carries pottery; Edda carries
rope; the gardener carries seeds. Recurring people keep their identity.

The six [traveler studies](candidate_studies_5x.png) compare a trail keeper,
rain cloak, brimmed surveyor, seed ranger, port lantern and night cowl on two
background values. Study 1 was selected: its scarf and small satchel leave
the face, feet and hands clear at 16 pixels. The wider cloak hides the walk;
the larger hat and lantern compete with the face. These alternatives are
review material, not additional playable costumes.

The selected pass also simplifies shared foliage and floor texture. The title
puts the traveling pair at the lower-left shore and a small lit beacon across
the water. The central wordmark and control text receive quiet dark planes;
the moon sits outside the wordmark. Existing paths and collision footprints
remain unchanged.

## Visual review

- [Before/after, native size](characters_comparison_native.png) and
  [integer 3× zoom](characters_comparison_3x.png).
- [Selected cast, native size](characters_after_native.png) and
  [integer 4× zoom](characters_after_4x.png).
- [Four-pose contact sheet](motion_contact_4x.png) and
  [four-pose motion preview](four_pose_walk.gif).
- [Early companions and wardens](allies_and_wardens_4x.png).
- [Enemy shot on dark ground, path and water](projectile_readability_4x.png).
- [Title backdrop](title_backdrop_4x.png), before runtime text composition.

These are authoring previews, not screenshots from the ROM or proof of
emulator timing. The baseline atlas was captured from the source before this
pass. All selected pixel art is drawn from code at its native dimensions;
the zoomed sheets use nearest-neighbor integer scaling. Regional companion
families outside the named early companions retain their existing authored
designs. This pass does not claim to replace every creature frame.

## Authoring and regeneration

`assets/redesign_characters.py` owns the selected core character drawings and
resident definitions. `assets/generate_assets.py` exposes them to the existing
exporters. The regional generators retain their sprite IDs and delegate only
resident drawing to that shared module. Campaign Fuuri uses the same authoring
module. Midori's evolved canopy and separate portrait use matching leaf colors.

The native limits are unchanged: 16×16 actors, four directions and four walk
poses for the core travelers, 32×32 bosses, 178 shared RGB555 palette entries,
palette index zero for transparency and the same streamed OBJ slots. No new runtime RAM,
VRAM slots or sprite dimensions are required. The full foreground/background
geometry and save identifiers stay with their existing generators and engine.

Run the project Python environment with Pillow 13:

```sh
make assets
python3 assets/redesign_preview.py
python3 tests/test_lantern_art.py
```

`make assets` explicitly selects the `lantern-trails-r1` art successor for the
two historical creature-prefix guards. `tools/author_redesign_art.py --author`
freezes reviewed identities after an intentional art review; normal generation
must not refresh those identities automatically. Historical source contracts
remain evidence of the earlier artwork, rather than being rewritten to make
new pixels appear unchanged. The opening backdrop and precompiled title patch
must be regenerated after the base scene, as ordered by the asset target.

The art checks require four distinct silhouettes in each core walk cycle,
different silhouettes for residents within each place, meaningful work/walk
poses, existing palette bounds, quiet title text planes, and exact agreement
between selected core drawing code and the shipped C arrays. Native timing and
playability checks are separate release gates.

## Design references

The [Sprite Fusion article](https://www.spritefusion.com/blog/how-to-make-good-pixel-art-effects-with-claude)
informed the small candidate studies, visible motion review and repeated pixel
adjustments. The [Miyamoto interview](https://shmuplations.com/miyamotodesign/)
informed the welcoming scale, expressive representation and walking-adventure
composition. The [game-design guide](https://github.com/agent-skills-hub/agent-skills-hub/blob/main/skills/game-development/game-design/SKILL.md)
informed the clear action/readable response relationship: a leafy companion,
a visible work tool and a readable changed state. These are original Emberbond
characters and compositions; the references supply principles, not copied
sprites or maps.
