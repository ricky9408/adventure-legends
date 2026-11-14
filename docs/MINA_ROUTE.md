# Mina: playable conservatory route

The player is 22 and Mina is 23. Both are original adult characters. The
relationship ledger is hidden; dialogue and revisits show the change.

After reopening the Southern conservatory and claiming quest24's original
reward, Mina invites the player to the garden plot beside her. Interacting with
the plot plants together. On a later harbor visit, the first growth brings a
second shared scene. Another visit opens Mina's personal story about her fear
of failing the seedlings. Later visits offer explicit choices to date and then
to marry. Every relationship event requires the final A of its scene; B cancels
without recording it. A new visit is required between events, and already seen
events cannot be used to gain more affinity. The original quest report, receipt,
reward and chapter progression remain separate.

Current cross-partner consent is conservative: if another person's ledger says
dating or marriage, Mina's dating or marriage offer pauses with an explanatory
conversation. A full conversation and additional marriages await another
playable route. Edda has a separate playable harbor route; Ressa and Lyra do not
yet have playable relationship scenes.
There is no physical GBA hardware run.

## Reproduce the earned route

With the dependencies from [Gameplay CI](GAMEPLAY_CI.md), build the ROM and the
native bridge, then run `tests/mina_route_native.py` with the same ROM, symbols,
bridge and source-hash arguments used by `tools/run_gameplay_ci.py`. The normal
native CI lane does this automatically as `mina-earned-route`.

The dedicated `mina-summary.json` reports scoped acceptance, controller-only
input, zero game-RAM writes, zero machine-state or historical-progress imports,
presented-frame pacing, and banked SRAM relationship bytes at each checkpoint.
`regions/mina-*.png` shows the invitations and scene pages. The underlying
campaign driver's generic `summary.json` marks a deliberately stopped Southern
route as short of the entire nine-chapter campaign; `mina-summary.json` is the
acceptance record for this bounded route.

Host tests cover ordered and idempotent event recording, cancellation and scene
resets. The native test earns quest24 and every Mina event using controller input
from blank SRAM, then cold Continues on its own saved cartridge. A synthetic
ledger or host state setup is not evidence of earning this route.
