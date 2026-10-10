.syntax unified
.cpu arm7tdmi
.arm
.section .text.startup,"ax",%progbits
.global _start
_start:
    b reset
    .space 188
reset:
    mov r0, #0xD3
    msr cpsr_c, r0
    ldr sp, =0x03007FE0
    mov r0, #0xD2
    msr cpsr_c, r0
    ldr sp, =0x03007FA0
    mov r0, #0x5F
    msr cpsr_c, r0
    ldr sp, =0x03007F00
    ldr r0, =__iwram_lma
    ldr r1, =__iwram_start
    ldr r2, =__iwram_end
4:  cmp r1, r2
    ldrlo r3, [r0], #4
    strlo r3, [r1], #4
    blo 4b
    ldr r0, =__data_lma
    ldr r1, =__data_start
    ldr r2, =__data_end
1:  cmp r1, r2
    ldrlo r3, [r0], #4
    strlo r3, [r1], #4
    blo 1b
    ldr r1, =__bss_start
    ldr r2, =__bss_end
    mov r3, #0
2:  cmp r1, r2
    strlo r3, [r1], #4
    blo 2b
    ldr r0, =main
    mov lr, pc
    bx r0
3:  b 3b
