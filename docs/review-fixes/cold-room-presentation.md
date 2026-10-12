# Existing-save room presentation

An authenticated, controller-earned prior-ROM checkpoint in Magma town (room 38,
spawn 3) exposed a remaining cold Continue stall in candidate `bb9a93a`.
The ordinary save writer was not responsible: its begin/step counters were zero
on the offending frame, and it began on a later warm frame.

| Measured work | Before | After |
| --- | ---: | ---: |
| Room reconstruction update | 249,043 cycles | 249,047 cycles |
| Paint sharing that update | 38,816 cycles | 4,737 cycles |
| Total presented frame | 290,579 cycles | 273,200 cycles |
| Missed update/page flip | 1 / 1 | 0 / 0 |

The GBA frame budget is 280,896 cycles. Reconstruction now keeps the cached
loading screen for its final expensive update, then publishes its resulting
PLAY or dialogue state on a separate cheap update. The following scene copy
therefore cannot share the constructor's cost. The existing phase variable
stores the pending result; no new state allocation, OBJ storage or IWRAM code
is introduced. The integrated ROM increases by 32 bytes.

The decoder, bank validation, migration and atomic publication are unchanged.
B still cancels before room reconstruction, including after decode and derived
refresh. Once reconstruction finishes, its committed local result is published
on the next update. SRAM remains unchanged throughout loading and cancellation.
Story dialogue remains pending until its normal A confirmation.

`tests/cold_continue_native.py` also measures the initial ordinary upgrade/visit
save through completion. Its trace distinguishes live sampled state from the
state of the completed presentation and records separate update, render, audio
and save costs. No pacing exceptions are used.

The local controller-only mGBA pass measured 5,837 presented frames across nine
inputs: shipped v2/v4 and revision-9 fixtures, a prepared full-160 roster, a
prepared pending-story save, and copied earned Magma/Lastwatch checkpoints.
There were no missed updates/flips, budget overruns, native faults or music
faults/recoveries. Every original source save remained unchanged. The prepared
inputs are codec/presentation evidence, not campaign acquisition. The bounded
reader's seven host tests also passed, comparing 68 shipped SRAM images.

The measured ROM SHA-256 was
`8833481e3712a2e90ec93c39942fb4cd2ddcdecaf1cbeefa9a6f14bb6028d191`.
IWRAM still ends at `0x03006f80`, retaining its 128-byte code margin.
Later integrated runtime changes require new native and hosted CI measurements.
