# Regional quest transaction contract

The C implementation in `src/regional_quests.c` shares the exact fixed ledger
in `assets/region/contract.json` and content-revision2 of Save5. This is a core
and serialization result; native room/quest gameplay integration is separate.

Eleven quests use inactive → active → ready → claimed states. An objective is
one explicit authored bit, set by the engine only after the real condition has
occurred. Repeated interactions, objectives and reward claims change no byte.
The engine must actually offer a quest before its objectives advance. Full bags
or rosters leave the quest ready, with no partial reward, for a later retry.

The town becomes available after the Grove chapter. Visiting another regional
room requires prior town visitation. Bellfoundry and the tide courtyard require
the completed Water bond quest; spawn and rest-anchor flags are stamped before
a checkpoint is written. The fixed Save5 codec checks these relationships.

Practice lance and travel bow racks use equipment sources2/4, once each. The
other authored equipment comes from its matching quest. The four-friendships
reward is an atomic lance/ring bundle. These APIs never access SRAM themselves;
the engine requests one normal incremental save after the transaction commits.
No dialogue or pause may interrupt an in-memory reward/claim operation.

Water bond quest2 recruits form13 through creature reward5. Metal bond quest3
recruits form16 through reward6. Both start at level10/bond20. Recruits are owned
collection instances, not silently swapped into an occupied party. Base Water's
fill ability can solve the paired pools without its evolved link ability.
Completing the paired-pool personal quest marks trial16 and trains that Water
instance to at least level15/bond45, never lowering an already higher value.
This one-time floor avoids a repeated-kill requirement for the new evolution.
Evolution still requires the restored-basin context, a sanctuary, and the
player's confirmation. The original Water command remains available afterward.

Core host coverage currently exercises571 assertions twice (strict and
ASan/UBSan), all eleven quest/reward paths, all thirteen equipment grants, actual
new recruit rows, duplicate/no-op behavior, locked/invalid inputs, full160-slot
collection rollback and save/load of the complete joined state. No game RAM was
injected because these are host C tests, not emulator route evidence. ARM Thumb
object1354ROM bytes, zero mutable globals, maximum individual stack80bytes;
reward helper calls additionally use their documented bounded stack frames.
