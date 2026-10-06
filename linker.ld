ENTRY(_start)
MEMORY {
 ROM (rx) : ORIGIN = 0x08000000, LENGTH = 32M
 EWRAM (rw) : ORIGIN = 0x02000000, LENGTH = 256K
 IWRAM (rw) : ORIGIN = 0x03000000, LENGTH = 32K
}
SECTIONS {
 .text : { KEEP(*(.text.startup)) *(.text.rom*) *(EXCLUDE_FILE (*/game.o */region_game.o */north_game.o) .text*) *(.rodata*) . = ALIGN(4); } > ROM
 /* Explicit filenames preserve reviewed legacy hot collision helpers. A broad
  * *game.o glob also matched every future chapter and silently filled IWRAM. */
 .iwram : { . = ALIGN(4); __iwram_start = .; */game.o(.text*) */region_game.o(.text*) */north_game.o(.text*) *(.iwram.text*) . = ALIGN(4); __iwram_end = .; } > IWRAM AT > ROM
 __iwram_lma = LOADADDR(.iwram);
 .data : { . = ALIGN(4); __data_start = .; *(.data*) . = ALIGN(4); __data_end = .; } > EWRAM AT > ROM
 __data_lma = LOADADDR(.data);
 .bss (NOLOAD) : { . = ALIGN(4); __bss_start = .; *(.bss*) *(COMMON) . = ALIGN(4); __bss_end = .; } > EWRAM
 /DISCARD/ : { *(.comment) *(.note*) *(.ARM.exidx*) *(.ARM.extab*) }
}
/* Keep a real stack reserve as the campaign grows. */
ASSERT(__iwram_end <= 0x03007000, "IWRAM code overlaps reserved stack space");
