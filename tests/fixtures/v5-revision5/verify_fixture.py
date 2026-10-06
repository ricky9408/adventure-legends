#!/usr/bin/env python3
"""Portable, read-only authentication of generated Magma revision5 fixtures.

Uses only the standard library. Never loads machine states, writes SRAM,
constructs ownership, or consults current enabled catalog rows.
"""
import argparse
import binascii
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROM='90ba47f30a0c94c28f073d26cc31ac5f5c736eb4d6e704d090892d2776f1ffb2'
SYMBOLS='add52be1a5d23d2e8df8fd616f4ef1c7fde8d3e1906e1d789925d68476cf50f6'
LIFECYCLE='8093ef37f4ae90174b24a3a12203c80c6bfaad94d5e087e5b65c4ede38c23bc6'
ACQUISITION='055d1cf3c86f64cb9a5781731c252dc32b652e9b7d6f32b0cab104123ec9241b'
SOURCE_MANIFEST='a72fd93eddb0a39322b22e45caf0f4ac49496d962776ee616dfd83642342ef3f'
FIXTURES={'magma-all65-town.sav':'a4b45873a14d3ca18c3f93678350f8ab2a0a8c6609cdc17d1eb7a609a9760858',
          'magma-all65-acquisition-town.sav':'28a01170b27b9029546067e2866ee91cde1ee7f64ffd6564f37df836aa2c11eb'}

def digest(data):return hashlib.sha256(data).hexdigest()

def reconstruct(descriptor,expected):
    path=HERE/descriptor['manifest'];raw=path.read_bytes()
    assert digest(raw)==descriptor['manifest_sha256']
    manifest=json.loads(raw)
    assert manifest['format']=='exact-byte-concatenation-v1' and manifest['max_part_bytes']==30000
    assert manifest['original_sha256']==descriptor['original_sha256']==expected
    pieces=[];offset=0
    for index,row in enumerate(manifest['parts']):
        assert row['file']==f'part_{index:03d}.txt' and row['offset']==offset
        data=(path.parent/row['file']).read_bytes();data.decode('utf-8')
        assert 0<len(data)<=30000 and len(data)==row['bytes'] and digest(data)==row['sha256']
        pieces.append(data);offset+=len(data)
    data=b''.join(pieces)
    assert len(data)==manifest['original_bytes']==descriptor['original_bytes'] and digest(data)==expected
    assert len(pieces)==descriptor['part_count']
    return json.loads(data)

def decode_banks(path):
    data=path.read_bytes();assert len(data)==32768
    result=[]
    for offset in (0x200,0x1a00):
        bank=data[offset:offset+6144]
        assert bank[:8]==bytes.fromhex('454205200018c013') and bank[12:16]==bytes((5,0,0,0)) and bank[20]==0xa5
        normalized=bytearray(bank);normalized[16:20]=bytes(4);normalized[20]=0
        assert binascii.crc32(normalized)==int.from_bytes(bank[16:20],'little')
        instances=[{'index':i,'form_id':bank[160+24*i],
                    'instance_id':int.from_bytes(bank[168+24*i:172+24*i],'little'),
                    'record_hex':bank[160+24*i:184+24*i].hex()}
                   for i in range(160) if bank[161+24*i]&1]
        obtained=[i+1 for i in range(128) if bank[112+i//8]&(1<<(i%8))]
        quests=[(bank[4032+i//4]>>(2*(i%4)))&3 for i in range(64)]
        items=[int.from_bytes(bank[4544+i*8:4546+i*8],'little')for i in range(48)];items=[i for i in items if i]
        assert len(instances)==34 and len({x['instance_id'] for x in instances})==34 and len(obtained)==65
        assert quests==[3]*38+[0]*26
        result.append({'bank_offset':offset,'sequence':int.from_bytes(bank[8:12],'little'),'room':bank[32],'spawn':bank[33],
                       'chapter_flags':bank[34],'owned_instance_count':34,'obtained_form_count':65,'claimed_quest_count':38,
                       'gear_item_count':len(items),'instances':instances,'obtained_form_ids':obtained,'quests':quests,
                       'party_slots':list(bank[4000:4004]),'selected_party':bank[4004],
                       'next_instance_id':int.from_bytes(bank[4008:4012],'little')})
    return result

def verify(runtime_root=None):
    p=json.loads((HERE/'provenance.json').read_text())
    assert p['generated_test_fixture'] is True and p['player_save'] is False
    assert p['source_rom_sha256']==ROM and p['source_symbols_sha256']==SYMBOLS
    life=reconstruct(p['source_report'],LIFECYCLE);acq=reconstruct(p['acquisition_report'],ACQUISITION)
    manifest=reconstruct(p['source_manifest'],SOURCE_MANIFEST)
    assert len(manifest)==p['runtime_source_count']==893
    for report,count in ((life,647),(acq,26884)):
        assert report['rom_sha256']==ROM and report['symbols_sha256']==SYMBOLS
        assert report['source_manifest_sha256']==SOURCE_MANIFEST
        assert report['controller_only'] and report['game_ram_writes']==0 and not report['failures']
        assert len(report['checks'])==count and all(row['passed'] for row in report['checks'])
    assert life['completed'] and life['machine_state_loads']==0
    source=life['provenance']
    assert source['earned_source_relation']=='same-ROM' and source['earned_source_report_sha256']==ACQUISITION
    assert source['earned_source_sram_sha256']==FIXTURES['magma-all65-acquisition-town.sav']
    assert source['earned_source_rom_sha256']==ROM and source['source_machine_states_loaded']==0
    receipt_path=HERE/'acquisition-producer/test-source-capture.json'
    assert digest(receipt_path.read_bytes())==p['acquisition_observer_receipt_sha256']==source['producer_source_capture_sha256']
    receipt=json.loads(receipt_path.read_text());assert receipt['recorded_hashes_verified']==acq['test_sources']
    for label,report in (('lifecycle',life),('acquisition',acq)):
        sources=p['producer_test_sources'][label]
        assert all(sources[path]==sha for path,sha in report['test_sources'].items())
        for path,expected in sources.items():
            assert digest((HERE/(label+'-producer/test-source')/path).read_bytes())==expected
    assert p['producer_test_sources']['acquisition']==source['verified_producer_test_sources']
    assert p['source_state']==life['snapshots']['03-full34-independent-reboot']
    bank_records={}
    for name,expected in FIXTURES.items():
        path=HERE/name;assert digest(path.read_bytes())==expected
        bank_records[name]=decode_banks(path);assert bank_records[name]==p['wire_banks'][name]
    current=max(bank_records['magma-all65-town.sav'],key=lambda b:b['sequence'])
    assert current['room']==38 and current['spawn']==3 and current['chapter_flags']==15
    endpoint=life['snapshots']['03-full34-independent-reboot']
    assert endpoint['sram_sha256']==FIXTURES['magma-all65-town.sav']
    assert current['obtained_form_ids']==endpoint['obtained_form_ids']
    assert [x['form_id']for x in current['instances']]==endpoint['owned_form_ids']
    actual=life['retained_records']['after-full34-independent-reboot']['individuals']
    assert [{k:v for k,v in x.items()if k!='index'}for x in current['instances']]==actual
    assert acq['snapshots']['09-all65-earned-town']['sram_sha256']==FIXTURES['magma-all65-acquisition-town.sav']
    capture=HERE/p['verified_originals']['path'];assert digest(capture.read_bytes())==p['verified_originals']['sha256']
    assert len(json.loads(capture.read_text()))==p['verified_originals']['count']
    ledger=HERE/'CHECKSUMS.json'
    ledger_count=0
    if ledger.exists():
        checks=json.loads(ledger.read_text())
        for path,expected in checks.items():
            assert not Path(path).is_absolute() and '..' not in Path(path).parts
            assert digest((HERE/path).read_bytes())==expected
        ledger_count=len(checks)
    if runtime_root:
        for path,expected in manifest.items():assert digest((runtime_root/path).read_bytes())==expected
    return {'passed':True,'fixture_sha256':FIXTURES['magma-all65-town.sav'],'source_rom_sha256':ROM,
            'banks_verified':4,'actual_retained_individuals':34,'earned_form_histories':65,'claimed_quests':38,
            'exact_report_parts':p['source_report']['part_count']+p['acquisition_report']['part_count'],
            'runtime_manifest_entries':len(manifest),'current_runtime_verified':bool(runtime_root),
            'checksum_files_verified':ledger_count,'machine_states_loaded':0,'fixture_bytes_changed':False}

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--runtime-root',type=Path)
    print(json.dumps(verify(parser.parse_args().runtime_root),indent=2))
