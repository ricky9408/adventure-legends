# New-adventure confirmation

Southern development adds a title-screen confirmation before replacing an existing save.

- START still continues an existing adventure
- SELECT opens a clear overwrite warning when a valid save is present
- A must be freshly pressed after the prompt opens to confirm
- B, START or SELECT cancels; cancel wins over simultaneous A
- Holding A while opening the prompt cannot accept it
- Opening, waiting or cancelling leaves all 32 KiB of SRAM unchanged
- A cartridge without valid progress still starts directly

`tests/new_game_confirmation.py` checks these using only controller input and a
hash-authenticated prior cartridge SRAM fixture. It also observes the normal
transactional new-save commit and exact hardware update/presentation cadence.
This is not a change to the frozen Northern N5 release.
