#!/usr/bin/env python3
"""Read-only, exact-ROM-paired ELF observations for Southern native tests."""
from collections import Counter
from pathlib import Path
import hashlib
import shutil
import struct

SOUTH_TRIAL_SIZES={'trial_index':1,'trial_slot':1,'trial_id':4,'trial_bits':1}

def paired_southern_symbols(rom, symbols, elf, output):
    """Return unique nm names plus verified south_game.c trial objects.

    Ambiguous nm names are never resolved by order. The only overrides are
    STB_LOCAL/STT_OBJECT records under the ELF's exact STT_FILE owner.
    """
    elf=Path(elf);output=Path(output)
    assert elf.is_file(),'Southern observation requires the candidate paired ELF'
    if elf.resolve()!=output.resolve():shutil.copyfile(elf,output)
    raw=output.read_bytes();target=Path(rom).read_bytes()
    assert raw[:6]==b'\x7fELF\x01\x01','Require little-endian ELF32'
    h=struct.unpack_from('<16sHHIIIIIHHHHHH',raw)
    assert h[2]==40 and h[9]>=32 and h[11]>=40,'Require ARM ELF headers'
    image=bytearray(len(target));covered=bytearray(len(target))
    for i in range(h[10]):
        kind,off,virt,physical,size,memsize,flags,align=struct.unpack_from('<IIIIIIII',raw,h[5]+i*h[9])
        if kind!=1 or not size:continue
        start=physical-0x08000000
        assert 0<=start<start+size<=len(target) and off+size<=len(raw)
        assert not any(covered[start:start+size]),'Overlapping ELF load images'
        image[start:start+size]=raw[off:off+size];covered[start:start+size]=b'\1'*size
    assert all(covered) and image[192:]==target[192:],'ELF does not pair with candidate ROM'
    sections=[struct.unpack_from('<IIIIIIIIII',raw,h[6]+i*h[11]) for i in range(h[12])]
    scoped={}
    for section in sections:
        if section[1]!=2:continue
        assert section[9]>=16 and section[5]%section[9]==0
        strings=sections[section[6]];strings=raw[strings[4]:strings[4]+strings[5]];owner=None
        for pos in range(section[4],section[4]+section[5],section[9]):
            ni,value,size,info,other,index=struct.unpack_from('<IIIBBH',raw,pos)
            name=strings[ni:].split(b'\0',1)[0].decode()
            if info&15==4:owner=name
            if owner=='south_game.c' and info>>4==0 and info&15==1 and name in SOUTH_TRIAL_SIZES:
                assert name not in scoped,'Duplicate file-scoped Southern object'
                assert index and size==SOUTH_TRIAL_SIZES[name],('Southern local type/size differs',name,size)
                scoped[name]={'address':value,'size':size}
    assert set(scoped)==set(SOUTH_TRIAL_SIZES),'Southern trial locals missing from candidate ELF'
    rows=[p for line in Path(symbols).read_text().splitlines() if len(p:=line.split())==3]
    counts=Counter(p[2] for p in rows)
    result={p[2]:int(p[0],16) for p in rows if counts[p[2]]==1}
    for name,record in scoped.items():
        assert any(p[2]==name and int(p[0],16)==record['address'] and p[1] in ('b','d','r') for p in rows),'ELF local differs from frozen symbols: '+name
        result[name]=record['address']
    return result,{'elf_sha256':hashlib.sha256(raw).hexdigest(),
        'rom_sha256':hashlib.sha256(target).hexdigest(),'matched_bytes':len(target)-192,
        'header_note':'Only first192bytes containing repaired cartridge metadata are excluded',
        'source_file':'south_game.c','locals':scoped}
