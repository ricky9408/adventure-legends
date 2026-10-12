# Native text span storage

The native 12px font keeps its exact compiled pixels while storing each `UiRun`
in one halfword. The internal `UiRun` layout changes from four bytes to two;
`UiText` remains 16 bytes on ARM, text IDs and save formats remain unchanged.

The little-endian ARM word contains an 11-bit halfword offset, a 3-bit positive
run count and a 2-bit pixel-pair mask, in that order. Offsets address the existing
120-halfword row stride. Counts are 1–7; the compiler splits longer uniform runs
without adding or removing pixels. Empty labels retain an unused `{0,0,0}`
placeholder with a table count of zero. No TTF, glyph-bit decoder, runtime font
cache or new allocation is added. C field access extracts packed span metadata.

All nine text generators enforce the same count limit and reject offset, count
or mask overflow before generating C. Host and ARM builds assert two-byte size
and alignment. The compiled font test checks every table descriptor, pointer
alignment, decoded field tuple and both pixel alignments against the original
font rasters. Its wrong-endian control uses a real compiled array; malformed
offset/count/mask controls are rejected separately.

The same toolchain build shrinks from 33,416,216 to 30,999,544 ROM bytes, leaving
2,554,888 bytes beneath the 32 MiB hardware limit. The existing one-MiB reserve
gate is unchanged. These sizes include linked code and data, excluding debug
sections and external font source files. IWRAM still ends at `0x03006f80`.

Targeted native replay is diagnostic evidence. The complete fresh campaign,
cold loads and hosted host/native suites must pass on the final combined commit
before accepting the release.
