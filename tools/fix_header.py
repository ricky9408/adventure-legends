#!/usr/bin/env python3
"""Set the GBA cartridge header needed for BIOS boot and flashcart recognition.

Header layout and fixed identification bytes verified against devkitPro gbafix:
https://github.com/devkitPro/gba-tools/blob/master/src/gbafix.c
This identification block is a boot compatibility requirement, not game artwork.
"""
from pathlib import Path
import sys

LOGO = bytes.fromhex('''
24 FF AE 51 69 9A A2 21 3D 84 82 0A 84 E4 09 AD
11 24 8B 98 C0 81 7F 21 A3 52 BE 19 93 09 CE 20
10 46 4A 4A F8 27 31 EC 58 C7 E8 33 82 E3 CE BF
85 F4 DF 94 CE 4B 09 C1 94 56 8A C0 13 72 A7 FC
9F 84 4D 73 A3 CA 9A 61 58 97 A3 27 FC 03 98 76
23 1D C7 61 03 04 AE 56 BF 38 84 00 40 A7 0E FD
FF 52 FE 03 6F 95 30 F1 97 FB C0 85 60 D6 80 25
A9 63 BE 03 01 4E 38 E2 F9 A2 34 FF BB 3E 03 44
78 00 90 CB 88 11 3A 94 65 C0 7C 63 87 F0 3C AF
D6 25 E4 8B 38 0A AC 72 21 D4 F8 07
''')
assert len(LOGO) == 156

def fix(path):
    data = bytearray(path.read_bytes())
    if len(data) < 192:
        raise ValueError('ROM is shorter than the GBA cartridge header')
    if data[3] != 0xEA:
        raise ValueError('ROM must begin with an ARM branch to startup code')
    data[4:160] = LOGO
    data[160:172] = b'EMBERBOND   '
    data[172:176] = b'EMBE'
    data[176:178] = b'00'
    data[178] = 0x96
    data[179:189] = bytes(10)
    data[189] = (-sum(data[160:189]) - 0x19) & 255
    data[190:192] = bytes(2)
    data.extend(bytes((-len(data)) % 4))
    assert (sum(data[160:190]) + 0x19) & 255 == 0
    path.write_bytes(data)
    print(f'{path}: {len(data)} bytes; valid header, complement 0x{data[189]:02x}')

if __name__ == '__main__':
    if len(sys.argv) != 2:
        raise SystemExit('Usage: fix_header.py ROM.gba')
    fix(Path(sys.argv[1]))
