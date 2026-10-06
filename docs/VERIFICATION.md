# Southern S3 release verification

Developer evidence, with progression spoilers. Player instructions and the default teaser remain spoiler-free. Reports were produced on 5 October 2026 UTC.

## Exact cartridge and save contract

- ROM: **5,858,700 bytes**, SHA-256 `87d16a0fc513d7e8a491e0b5ac5929f7951e1e44e18b7f534f1e5e0cc794d4de`
- Symbols: `ceedba1a6052fe450f17c91375eef6ddd5200d1a7bb01394c1eb95d2bc4f1305`
- Runtime-source manifest: `609104f75fa341bb67d0d1e2a362db7b03ed655ecb6eed41c101b0c799b2f089`, 707 inputs
- Save wire version 5, content revision 4; 24-byte instance records,160 slots and dual6144-byte banks remain unchanged
- IWRAM code: **27,944 /28,672 bytes**,728 bytes before the linker boundary
- Initialized data84 bytes plus BSS48,008 bytes; aligned EWRAM end48,096 bytes
- Runtime evidence: mGBA 0.10.5, GNU ARM GCC 14.2.1, native 240×160 Mode4/OBJ output

A clean independent rebuild reproduced ROM, ELF and symbols. Another clean final-QA checkout reproduced the same ROM/symbol pair. Asset regeneration checked 1,245 existing source/art files from the exported archive with no changes; only the four documented source-package-excluded River overview images were recreated. A packaging-only catalog normalization preserves parsed JSON and generated ROM tables while keeping individual public text files below 100 KB. The exported source archive was separately unpacked, rebuilt and bridge-smoke tested; its ROM and symbols match the exact cartridge above. Physical hardware is not claimed.

## Native Southern acceptance

Nine named controller suites pass **33,010 overlapping checks**, zero failures and zero gameplay-memory writes. Their original full-report hashes and bounded summaries are in [southern/index.json](southern/index.json). These are separate from synthetic host tests and the whole-game aggregate below.

| Suite | Checks |
|---|---:|
| Full acquisition, puzzles, trials, evolution, reboot and lifecycle |15,732|
| Minimal-prerequisite main route with starter sword |1,889|
| All18 reachable optical arrangements |4,708|
| Native initial controls/full-viewport pixels |448|
| Facing-sensitive conversation targeting |188|
| Earned21-individual storage/selector/journal/save stress |42|
| All20 new combat commands and controller edge cases |8,176|
| Crowd, cold UI, saving and companion-animation performance |1,484|
| Resumed actor tiles, cast identity and companion body/shadow anchors |343|

The journey earns all 41 historical forms while retaining 21 real individuals, all 25 gear and all 30 regional quest claims, then independently cold-boots the saved SRAM. It includes two guaranteed pre-gate bases, eight optional recruits, all ten personal trials/evolutions, decline/retry, three real boss weapon classes, older-region return and death/re-entry. Manual/reset routes never fabricate companion-gated objectives. Controller evidence covers 18 reachable optical states; the separate host oracle covers 24, and those counts are not conflated.

A separate genuine six-base-individual Northern source proves the main island route needs no optional River/Northern/Southern quest, Core/ending, evolution or trial. It acquires only guaranteed bases79/85, clears with starter sword1, independently reboots and returns by ferry; the six original individuals stay byte-identical. Two runs produce identical final SRAM.

The migration starts from the delivered Northern N5 cartridge SHA `302316c53d6fb9dafa0ecbf9f679c9c39af3a150af3aa78398c368312e50399e` and authenticated SRAM SHA `f4e853c85445b8567263a1a875eba967e552e0dcae30958ca42f39bfec4e4479`. Old identities, histories, quest/equipment data and payload bytes are preserved. The codec load is read-only; ordinary engine Continue/arrival subsequently autosaves revision 4. No prior-ROM machine state is imported. In-run branches pair same-ROM machine states with their exact SRAM.

Combat includes all five phase advantages; real sword/lance/arrow echoes including lethal source hits; actual-wall ricochet; one-generation-only guard grace; hostile-only interception; wrong facing; cooldown/lease/equipment restrictions; selector, dialogue and hit-stop freezes; and all 20 commands. A real boss warning/attack/open/recovery trace is unchanged across 260 updates with repeated ordinary-ranged-mark attempts. The separate native boss actor is not a target of the new ordinary-enemy-only hooks.

## Actual hardware-frame presentation

Tests sample the main-loop update counter and displayed Mode4 page after each emulated hardware frame. Host execution speed is never the frame-rate metric. Cycle readings cover input/update/render, **excluding** final VBlank wait and OAM commit; therefore a cycle number below 280,896 alone is insufficient.

| Window | Native updates / page flips | Peak measured cycles |
|---|---:|---:|
| Five visible bodies + hostile shot + two arrows + crescent |180/180 each|154,826|
| Same combined load, returning fan |180/180 each|261,957|
| Same combined load, expanding ring |180/180 each|253,878|
| Same combined load, arc projectile |180/180 each|208,870|
| Same combined load, switching guard |180/180 each|186,809|
| Cold town / field eight-page journal |95/95 each|272,365 /266,003|
| Full21-instance repeated rest/save |160/160 each|269,836|
| All21 owned storage candidates including EMPTY wrap |120/120 each|274,847|
| First journal open → all eight tabs → close |128/128 each|272,347|
| Four explicit L-direction releases |96/96 each|178,275|

Each crowd case contains nine frames with the full combination actually visible, rather than merely allocated offscreen. Independent earned-roster save coverage also passes 180/180 at 263,612 cycles. Long paired-target aim followed immediately by a one-hardware-frame A input passes 80/80 and samples the attack. Cold menus have limited remaining headroom; new content/audio needs renewed native tests.

Earlier candidates exposed real missed frames. Fixes preserve behavior rather than relaxing tests: exact collision-raster/LOS caches with explicit topology invalidation; equivalent full validation with exhaustive differential checks; queued frozen saving entry before snapshot copying; and removal of software modulo division from each empty storage-slot scan. Earlier failed reports are development history, not release acceptance.

## Independent core review and persistence stress

[SOUTHERN_RELEASE_REVIEW.md](SOUTHERN_RELEASE_REVIEW.md) approves the exact reviewed integration scope, conditional on the separate native tests above. It confirms source/ELF identity and contains 34 targeted tests plus strict/ASan/UBSan save, selection and power checks. An additional 16,000 randomized crescent scenes produce 192,000 reference-equivalent target comparisons.

Validation proof covers 23,531,642 XP/level pairs,301,510 party/reference cases,1,048,576 collection-byte pairs,36,720 instance corruptions and158,400 historical comparisons. Full records and standalone party APIs remain fully validated. Synthetic save stress covers 147,504 interrupted/success positions, full 160-instance/full 48-gear capacity, malformed CRC-valid records and bounded writer budgets. Synthetic capacity is not native obtainability. See the source-pinned files under `evidence/` and `SOUTHERN_SAVE4_VERIFICATION.json`.

The initial historical-policy review remains pinned separately in `SOUTHERN_CORE_REVIEW.md`. Later third-tier/current-policy changes require its explicit expansion gates; no incompatible change is enabled in this 41-form release.

## Whole-game regression and reproducibility

A clean `make test test-tools` completed with **exit0**, including all earlier story/exploration/save/evolution/quick-party/equipment/River/Northern suites and all current Southern targets. The complete log SHA-256 is `d0495b8781d46777532df1db743b81db5fdbb80a485fdd60af949595323121d0`. The bounded execution receipt and source hashes are in `southern/aggregate.json`. Host/synthetic and overlapping native counts are not combined into a single gameplay-coverage total.

Legacy tests now explicitly confirm title-screen replacement and use ordinary rest before a long puzzle itinerary. Northern private power fields are resolved through a ROM-paired ELF/STT_FILE scope, rather than ambiguous global nm names after another power module introduced matching private names. The prior observation failure is not hidden as a gameplay change; all original interception, wrong-facing and geometry assertions pass unchanged.

Run `make test test-tools` for the complete suite. `make test-southern` reproduces the current chapter's authoring, host and native controller tests on the exact built ROM, with a newly earned same-ROM source save. Tool lookup supports explicit ARM_PREFIX, DEVKITARM, the isolated extracted official toolchain or standard installed ARM tools. Invalid explicit selections fail clearly. No private credentials or extracted commercial assets are needed.

The source ZIP contains generated arrays, editable original assets, fixture provenance and test scripts, but no toolchain, emulator shared library, local gameplay saves or developer machine states. Prior release evidence remains available in [VERIFICATION-NORTHERN.md](VERIFICATION-NORTHERN.md) and [NORTHERN_VERIFICATION.md](NORTHERN_VERIFICATION.md).

## Player media and limits

The default teaser is a continuous 20.091-second opening-town stroll with a previously available companion. All 1,200 native frames update/flip once; maximum 179,386 measured cycles. It captures actual PSG samples with zero endpoint drift, no cuts, RAM writes, state loads or quest/ownership changes. The 240×160 preview is a real frame; the delivered 4× image/video use nearest-neighbor scaling. Media reports are capture evidence, not substitutes for full-game acceptance.

Physical GBA and alternate emulator/compiler releases remain untested. Runtime stack high-water is not measured; reviewed static call-chain bounds and the linker reserve are not a physical stress test. Audio is the existing original PSG phrase/effects. The complete 128-form game, legendary acquisition, Magma Mountain and underwater chapters remain unfinished. No commercial-game parity or unmeasured total playtime is claimed.
