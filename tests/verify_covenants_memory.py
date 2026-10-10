#!/usr/bin/env python3
"""Exact-candidate resource and negative-link gates; no native timing claim."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
BASE = dict(release='Shared Horizons C',rom_bytes=15274940, ewram_span=61124, iwram_bytes=27128,
            rom_sha256='4166bdafdba0bf689a8230d6d8d407ae7faf0271925df480b4e3b0aa917f1a91')


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--candidate-root', type=Path, default=ROOT)
    parser.add_argument('--expected-rom-sha', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    root = args.candidate_root.resolve()
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=False)
    rom, elf, mapping = [root/'build'/('emberbond.'+s) for s in ('gba', 'elf', 'map')]
    assert sha(rom) == args.expected_rom_sha
    manifest = json.loads((root/'build/source-hashes.json').read_text())
    assert all(sha(root/name) == value for name, value in manifest.items())
    text = mapping.read_text()
    sections = {}
    for name in ('text', 'iwram', 'data', 'bss'):
        m = re.search(r'^\.'+name+r'\s+(0x[0-9a-f]+)\s+(0x[0-9a-f]+)', text, re.M)
        assert m, name
        sections[name] = dict(start=int(m[1],16), bytes=int(m[2],16))
    span = sections['bss']['start'] + sections['bss']['bytes'] - 0x02000000
    size, iwram = rom.stat().st_size, sections['iwram']['bytes']
    gap = 0x03007000 - sections['iwram']['start'] - iwram
    checks = dict(rom_hardware=size<=32*1024*1024, ewram_hardware=span<=256*1024,
                  stack_floor=gap>=0, chapter_rom=size-BASE['rom_bytes']<=2*1024*1024,
                  chapter_ewram=span-BASE['ewram_span']<=2048,
                  chapter_iwram=iwram<=BASE['iwram_bytes'])
    assert all(checks.values()), checks
    prefix = os.environ.get('ARM_PREFIX')
    if not prefix:
        bundled = root/'tools/sysroot/usr/bin/arm-none-eabi-gcc'
        prefix = str(bundled)[:-3] if bundled.exists() else 'arm-none-eabi-'
    cc = prefix+'gcc'
    make = subprocess.check_output(['make','-pn','ARM_PREFIX='+prefix], cwd=root, text=True)
    object_line = next(line for line in make.splitlines() if line.startswith('OBJECTS := '))
    objects = [root/name for name in object_line.split(':= ',1)[1].split()]
    object_hashes = {str(p.relative_to(root)):sha(p) for p in objects}
    limits = []
    with tempfile.TemporaryDirectory(prefix='covenants-link-probes-', dir=out) as temp:
        temp = Path(temp)
        for name, section, flags, amount, expected in (
            ('iwram','.iwram.text.probe','ax',gap+64,'IWRAM code overlaps reserved stack space'),
            ('ewram','.bss.probe','aw',256*1024,'EWRAM'),
            ('rom','.rodata.probe','a',32*1024*1024,'ROM')):
            asm, obj = temp/(name+'.s'), temp/(name+'.o')
            kind = '%nobits' if name=='ewram' else '%progbits'
            asm.write_text(f'.section {section},"{flags}",{kind}\n.balign 4\n.space {amount}\n')
            subprocess.run([cc,'-mcpu=arm7tdmi','-mthumb-interwork','-marm','-c',str(asm),'-o',str(obj)],check=True)
            command = [cc,'-mcpu=arm7tdmi','-mthumb-interwork','-mthumb','-nostdlib',
                       '-Wl,-T,'+str(root/'linker.ld'), *map(str,objects),str(obj),
                       '-lgcc','-o',str(temp/(name+'.elf'))]
            result = subprocess.run(command,text=True,capture_output=True)
            log = result.stdout+result.stderr
            (out/(name+'-overflow.log')).write_text(log)
            assert result.returncode and expected in log, (name, log)
            limits.append(dict(name=name,added_bytes=amount,exit_code=result.returncode,
                               expected_rejection=expected,log_sha256=sha(out/(name+'-overflow.log'))))
    report = dict(scope='Static linked resources and intentional linker rejection; not native stack or pacing evidence',
                  candidate_rom_sha256=sha(rom),candidate_elf_sha256=sha(elf),
                  source_manifest_sha256=sha(root/'build/source-hashes.json'),
                  map_sha256=sha(mapping),linker_sha256=sha(root/'linker.ld'),
                  baseline=BASE,sections=sections,rom_bytes=size,ewram_occupied_span_bytes=span,
                  iwram_code_bytes=iwram,gap_to_system_stack_floor_bytes=gap,
                  system_stack_reserved_bytes=3840,irq_stack_reserved_bytes=160,svc_stack_reserved_bytes=64,
                  chapter_growth=dict(rom=size-BASE['rom_bytes'],ewram=span-BASE['ewram_span'],iwram=iwram-BASE['iwram_bytes']),
                  checks=checks,negative_link_probes=limits,object_sha256=object_hashes,
                  compiler=subprocess.check_output([cc,'--version'],text=True).splitlines()[0],
                  limitations=['Stack reserves are not observed stack usage or an exhaustive call-chain proof.',
                               'A source manifest alone does not prove reused objects match headers; use a fresh full build and exported rebuild.'])
    assert sha(rom)==args.expected_rom_sha and all(sha(root/k)==v for k,v in manifest.items())
    assert all(sha(root/k)==v for k,v in object_hashes.items())
    (out/'memory-budget.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:report[k] for k in ('rom_bytes','ewram_occupied_span_bytes','iwram_code_bytes','chapter_growth','checks')},indent=2))


if __name__ == '__main__':
    main()
