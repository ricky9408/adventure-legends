#!/usr/bin/env python3
"""Controller-only PR5 quick-party SRAM -> current save5 current content revision migration.

The checked-in 32KiB fixture is an unmodified, hash-pinned PR5 cartridge save.
Only SRAM crosses ROM versions. No machine state is loaded, no game RAM is
written, and no host-created roster is injected. The explicit wire decoder is
an observation oracle, cross-checked against matching PR5 native Continue when
this fixture was captured. Sibling checkouts are provenance-only, never needed.
"""
from __future__ import annotations
import argparse
import ctypes as C
import hashlib
import json
from pathlib import Path
import struct
import zlib
import re

from evolution_tests import EvolutionRun, ROOT, PLAY, DIALOG
from test_save5 import Save, Roster, Equipment

PR5_ROM_SHA256='1e76b1d5f3a65557b47f7445710d448b0a316fdd9e810a2d1dcc49ea4f7a45aa'
PR5_SYMBOLS_SHA256='c68705786801aefb8b84dd0cf5e1b1193f7cf327fd941e3448d3139be6326064'
PR5_FIXTURE_SHA256='806283f8ee36f4eb139822d74e8c176cf4c2e08f30c9e27ed5da82ae5f21d4d1'
FIXTURES=ROOT/'tests/fixtures/v5-revision1'
FIXTURE=FIXTURES/'pr5-evolved-reversed-party.sav'
PROVENANCE=FIXTURES/'pr5-evolved-reversed-party-provenance.json'
BANKS=(0x200,0x1a00)
BANK_SIZE=6144
TARGET_REVISION=int(re.search(r'SAVE5_CONTENT_REVISION\s*=\s*(\d+)',(ROOT/'src/save5.h').read_text()).group(1))
FORM_SET={1,2,4,5,7,8,10,11}


def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def sha(data):return hashlib.sha256(data).hexdigest()
def bits(data):return [i+1 for i in range(128) if data[i//8]&(1<<(i%8))]

def banks(data):
    result=[]
    for offset in BANKS:
        block=bytes(data[offset:offset+BANK_SIZE])
        if len(block)!=BANK_SIZE or block[:4]!=b'EB\x05\x20' or block[20]!=0xa5:continue
        check=bytearray(block);check[16:21]=bytes(5)
        if zlib.crc32(check)&0xffffffff!=int.from_bytes(block[16:20],'little'):continue
        result.append({'offset':offset,'sequence':int.from_bytes(block[8:12],'little'),
                       'revision':int.from_bytes(block[12:14],'little'),'block':block})
    return result

def newest(entries):
    assert entries,'no CRC-valid committed save5 bank'
    result=entries[0]
    for entry in entries[1:]:
        delta=(entry['sequence']-result['sequence'])&0xffffffff
        if 0<delta<0x80000000:result=entry
    return result

def wire_roster(block):
    """Decode explicit revision1/2 roster bytes; never alter input or game RAM."""
    r=Roster()
    for i in range(160):
        row=block[160+i*24:184+i*24]
        c=r.instances[i]
        c.form_id,c.flags,c.level,c.bond=row[:4]
        c.xp,c.instance_id=struct.unpack_from('<II',row,4)
        c.nickname_id,c.trial_flags=struct.unpack_from('<HH',row,12)
        c.equipped[:]=row[16:18];c.polarity=row[18];c.selected_command=row[19]
        c.cosmetic_seed=int.from_bytes(row[20:24],'little')
    r.party[:]=block[4000:4004];r.selected_party=block[4004]
    r.next_instance_id=int.from_bytes(block[4008:4012],'little')
    r.seen[:]=block[96:112];r.obtained[:]=block[112:128];r.rewards[:]=block[128:144]
    r.expedition_bond[:]=block[4296:4456];r.expedition_events[:]=block[4456:4520]
    r.lifetime_field_aid[:]=block[4520:4536]
    return r

def starter_equipment():
    result=Equipment();result.bag[0].item_id=1
    result.bag[0].flags=1;result.bag[0].quantity=1
    result.equipped[:]=(0,255,255,255,255)
    result.seen[0]=2;result.reward_claims[0]=1
    return result


class QuickPartyMigration(EvolutionRun):
    def __init__(self,rom,symbols,output):
        super().__init__(rom,symbols,output,optional=False,exhaustive=False)
        self.provenance={};self.migration_samples=[]

    def state(self):return Save.from_buffer_copy(self.e.bytes(self.sym['adventure_save'],C.sizeof(Save)))

    def assert_preserved(self,expected,label):
        current=self.state();r=current.roster
        self.check(bytes(r)==bytes(expected),label+': complete roster bytes, including credit ledgers, are preserved')
        self.check(list(r.party)==[3,2,1,0] and r.selected_party==3,
                   label+': reversed quick slots and selected position3 survive')
        self.check(self.get('spirit')==0 and current.campaign.spirit==0 and r.party[r.selected_party]==0,
                   label+': selected slot3 still means Homura instance1, not legacy family3')
        for i,form in enumerate((2,5,8,11)):
            c=r.instances[i];old=expected.instances[i]
            self.check(c.form_id==form and c.instance_id==i+1 and c.flags==3,
                       label+f': evolved story instance{i+1} retains its form/identity/ownership')
            self.check(bytes(c)==bytes(old),label+f': instance{i+1} retains XP, level, bond, trials, commands and cosmetics')
            self.check(c.equipped[c.selected_command]==i+5,
                       label+f': instance{i+1} retains advanced command{i+5}')
        self.check(not any(c.form_id for c in r.instances[4:]),label+': no old-form copies or regional recruits fabricated')
        self.check(set(bits(r.obtained))==FORM_SET and bytes(r.seen)==bytes(expected.seen),
                   label+': all eight historical forms remain exactly recorded')
        self.check(r.next_instance_id==5,label+': next-instance identity is unchanged')
        self.check(bytes(current.quests)==bytes(C.sizeof(current.quests)),label+': regional quest/reward/anchor state starts and remains empty')
        self.check(bytes(current.equipment)==bytes(starter_equipment()),label+': only canonical protected starter sword is present')
        self.check(self.get('chapter_flags')==7 and self.get('room_flags')==65535 and self.get('story_seen')==62,
                   label+': old campaign completion and story flags are not fabricated or lost')
        self.check(self.e.bytes(0x0e000000,512)==self.fixture_bytes[:512],label+': every legacy SRAM byte remains intact')
        latest=newest(banks(self.e.bytes(0x0e000000,32768)))
        self.migration_samples.append({'label':label,'status':self.status(),'roster_sha256':sha(bytes(r)),
            'quests_sha256':sha(bytes(current.quests)),'equipment_sha256':sha(bytes(current.equipment)),
            'bank':{k:v for k,v in latest.items() if k!='block'}})

    def run(self):
        self.provenance=json.loads(PROVENANCE.read_text())
        self.fixture_bytes=FIXTURE.read_bytes()
        p=self.provenance
        self.check(digest(FIXTURE)==PR5_FIXTURE_SHA256==p['sram_sha256'],'PR5 fixture is the exact authenticated cartridge SRAM')
        self.check(len(self.fixture_bytes)==32768,'fixture retains both original SRAM banks without fabrication')
        self.check(p['candidate']['rom_sha256']==PR5_ROM_SHA256 and p['candidate']['symbols_sha256']==PR5_SYMBOLS_SHA256,
                   'fixture provenance identifies the exact merged PR5 ROM and matching symbols')
        self.check(p['controller_only'] and p['game_ram_writes']==0 and not p['source_failures'],
                   'fixture came from a passing controller-only PR5 journey')
        self.check(p['snapshot']['candidate']==p['candidate'] and p['snapshot']['sram_sha256']==PR5_FIXTURE_SHA256,
                   'selected source snapshot and nested candidate agree with fixture identity')
        entries=banks(self.fixture_bytes);current=newest(entries)
        self.check(len(entries)==2 and all(e['revision']==1 for e in entries),
                   'both authentic source banks have valid CRC32 and content revision1')
        self.check(current['offset']==0x200 and current['sequence']==93,
                   'newest PR5 bank is A sequence93, distinct from older B92')
        expected=wire_roster(current['block'])
        self.check(sha(bytes(expected))==p['original_native_continue']['roster_sha256'],
                   'explicit wire oracle matches original matching-PR5 native Continue observation')
        older=next(e for e in entries if e['offset']!=current['offset'])
        self.check(wire_roster(older['block']).instances[0].equipped[0]==1 and expected.instances[0].equipped[0]==5,
                   'fixture distinguishes older Fire command1 from newest advanced command5')
        self.check(not any(current['block'][4032:4296]) and not any(current['block'][4544:5056]),
                   'revision1 source has no preexisting regional quests or equipment payload')
        # Reopen creates a fresh core, loads SRAM, boots the title, and presses
        # Continue. It never imports a previous-ROM machine state.
        self.reopen(FIXTURE);self.settle_save();self.step(2)
        self.check(self.get('loaded_save_version')==5 and self.get('room')==0 and self.get('game_state')==PLAY,
                   'current ROM title Continue loads the PR5 checkpoint into normal village play')
        self.assert_preserved(expected,'migrated Continue')
        latest=newest(banks(self.e.bytes(0x0e000000,32768)))
        self.check(latest['revision']==TARGET_REVISION and latest['sequence']>current['sequence'],
                   'normal Continue checkpoint transaction upgrades to current content revision')
        # The restored village checkpoint is already at the elder. A makes an
        # ordinary checkpoint before dialogue; do not advance the ending pages.
        self.check(abs(self.get('px')-120)+abs(self.get('py')-94)<29,
                   'controller-loaded checkpoint is within ordinary elder interaction range')
        prior_sequence=latest['sequence'];self.tap('A',2,2);self.settle_save();self.step(2)
        self.check(self.get('game_state')==DIALOG,'real A interaction opens elder dialogue after saving')
        self.assert_preserved(expected,'elder checkpoint')
        latest=newest(banks(self.e.bytes(0x0e000000,32768)))
        self.check(latest['revision']==TARGET_REVISION and 0<((latest['sequence']-prior_sequence)&0xffffffff)<0x80000000,
                   'real elder checkpoint commits a newer current content revision transaction')
        saved=self.save('pr5-migrated-elder-checkpoint')
        self.observations['checkpoint_sram_sha256']=digest(saved)
        self.reopen(saved);self.settle_save();self.step(2)
        self.check(self.get('game_state')==PLAY and self.get('room')==0,'independent new core boots the current content revision checkpoint normally')
        self.assert_preserved(expected,'independent current content revision reboot')
        self.check(digest(FIXTURE)==PR5_FIXTURE_SHA256,'the checked-in PR5 fixture remains byte-identical after all reboots')
        self.shot('pr5-migrated-village');self.report()

    def report(self):
        result={'suite':'pr5-quickparty-revision1-to-current content revision-controller-migration',
            'candidate':getattr(self,'candidate',{}),'controller_only':True,'game_ram_writes':0,
            'machine_state_loads':0,'fixture':FIXTURE.name,'fixture_sha256':PR5_FIXTURE_SHA256,
            'source_provenance':getattr(self,'provenance',{}),'passes':self.passes,'failures':self.failures,
            'samples':getattr(self,'migration_samples',[]),'save_pending_checks':getattr(self,'save_checks',[]),
            'observations':self.observations,'final':self.status(),
            'scope':'Authenticated PR5 SRAM migration; normal title Continue, elder checkpoint and independent SRAM reboot. No fabricated roster, quest, equipment or prior-ROM machine state.'}
        (self.out/'quickparty-migration-report.json').write_text(json.dumps(result,indent=2)+'\n')
        (self.out/'controller-inputs.json').write_text(json.dumps(self.inputs,indent=2)+'\n')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rom',type=Path,default=ROOT/'build/emberbond.gba')
    parser.add_argument('--symbols',type=Path,default=ROOT/'build/emberbond.sym')
    parser.add_argument('--output',type=Path,default=ROOT/'build/quickparty-migration-qa')
    parser.add_argument('--expected-rom-sha256',
                        help='optional target hash pin when verifying a frozen candidate')
    args=parser.parse_args()
    if args.expected_rom_sha256 and digest(args.rom)!=args.expected_rom_sha256:
        raise SystemExit('Refusing a ROM that does not match the expected target hash')
    run=QuickPartyMigration(args.rom,args.symbols,args.output)
    try:run.run()
    except Exception as exc:
        run.failures.append({'error':str(exc),'status':run.status()});run.shot('failure');raise
    finally:run.report();run.e.close()
    return int(bool(run.failures))

if __name__=='__main__':raise SystemExit(main())
