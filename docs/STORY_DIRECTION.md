# Emberbond: a light worth coming home to

The player leaves breakfast unfinished to find out why a familiar river has
fallen silent. A small flame and a growing root make the first path together.
Farther from home, the same powers let people bake, sail, plant, mend and visit
one another again. The journey ends with a longer table, not a bigger throne.

## The central question

What happens when protecting something means never letting it go?

The first guardians shut away wind and light because they remember a dangerous
night. Ryuma admits that he once made the same choice. Opening the paths gives
the player a practical answer: light keeps people warm by moving between them.
The underwater guardian echoes this idea, then speaks after its last opening
instead of disappearing into a completion notice.

Later chapters ask a harder version of the same question. A restored route must
leave room for people who move slowly, want quiet, or choose to stay home.
Companions can help without becoming possessions. The final porch is a place
to rest and welcome others; optional relationships retain their separate lives,
choices and deliberately paced visits.

## Chapter rhythm

| Place | What draws the player forward | What makes the return matter |
| --- | --- | --- |
| Village and forest | A silent river beyond an ordinary morning | Bread, soup and the promised seat remain |
| Sky | A guardian that fears the wind | Wind carries the village's warmth again |
| Lantern core | The cause of the closed paths | Ryuma owns his mistake; the four companions share the work |
| River workshops | Tools and small experiments | A repaired path lets the apprentice return |
| Northern harbor | Cargo and a missing sailing route | Edda can send the waiting cargo |
| Southern island | Light, shade and water | Mina can plant the seedlings she has kept alive |
| Magma mountain | Heat that can be carried and shared | Ressa can fire the waiting bricks |
| Nacreway | Two incomplete accounts of the same place | Keeper Shiori can welcome both processions home |
| Returning roads | Familiar places seen through the new map | Distant people have their own tables and homeward paths |
| Horizons market | Bring the towns' work together | Mira's mother's weaving travels beyond the sea |
| Covenants | Make space for the next person | The breakfast table and porch have room for others |

Every required puzzle keeps its concrete instruction. A person's wish belongs
before that instruction, and a visible or spoken consequence belongs after it.
Avoid putting a biography between the player and an experiment. Arrival,
achievement and return each need a different sentence.

## What this pass changes

The opening retains eight short, skippable beats and its existing actor staging.
It gives the player an everyday promise, an observable mystery, and a reason to
take the north road. Original chapter dialogue connects the guardians' fear to
Ryuma's admission. The underwater keeper gains the name Shiori, introduced in the
existing shell lesson; the final receipt sends the player to the village map
desk. Return, market and porch scenes pay off the breakfast motif.

The four chapter receipts still follow the existing earned-reward transaction.
Their aftermath plays once after continuing a fresh receipt. Recovery receipts,
cancelled receipts and repeated reports do not invent another first completion.
The underwater guardian speaks once on the third valid opening. Its earned
quest objective settles through the existing event scheduler while the dialogue
remains visible. No quest ID, reward, save byte or relationship event changes.

The only additional shared UI text ID is appended after the released namespace.
The generator validates the 214-pixel native text budget; historical proof trees
remain evidence of their historical versions.

## References and interpretation

[Miyamoto's 1998 interview](https://shmuplations.com/miyamotodesign/) informs the
emphasis on the pleasure of moving and exploring, generous rules, and expressive
representations of ordinary experience. This original world uses those ideas
without borrowing Nintendo characters, places, dialogue or music.

The [game-design reference](https://github.com/agent-skills-hub/agent-skills-hub/blob/main/skills/game-development/game-design/SKILL.md)
informs the short action–response–reward loop and quieter moments between
challenges. Here a repaired crossing should offer a satisfying experiment before
its wider story meaning becomes apparent.

[Sprite Fusion's effects article](https://www.spritefusion.com/blog/how-to-make-good-pixel-art-effects-with-claude)
informs the visual review process: motion and readable results need repeated
inspection. A written promise is only part of the design; the player must see
the bridge grow, the lantern relight and the road remain open.

## Verification

`tests/test_underwater_chapter_closure.py` exercises all four fresh-receipt
aftermaths and recovery exclusions against the real dispatch function.
`tests/test_underwater_game.py` plays the production host quest path through all
three guardian openings, checks the spoken goodbye, rejects a repeat hit, and
checks that objective processing preserves the dialogue. These are host tests,
not native controller timing or physical-device evidence.

The existing Sunlace welcome and village-homecoming tests cover their real
dialogue dispatch. Native Japanese corpus verification checks both alignments
against the generated text. Native capture and full-game performance are separate
release checks; automated checks cannot establish how moving the story feels.
