"""Independent, read-only same-wire5 migration proof for Return adapters.

Only called on native-observed bytes. Never encodes or edits a game save.
Earlier wire formats require their own migration policy and are not accepted.
"""
import binascii
import hashlib

BANK_SIZE=6144
BANK_OFFSETS=(0x200,0x1a00)

def validate_bank(bank,revision):
    bank=bytes(bank)
    assert len(bank)==BANK_SIZE and bank[:4]==b'EB\x05\x20'
    assert int.from_bytes(bank[4:6],'little')==BANK_SIZE
    assert int.from_bytes(bank[6:8],'little')==5056
    assert int.from_bytes(bank[12:14],'little')==revision
    assert bank[14:16]==bytes(2) and bank[20]==0xa5 and bank[21:32]==bytes(11)
    expected=int.from_bytes(bank[16:20],'little')
    check=bytearray(bank);check[16:20]=bytes(4);check[20]=0
    assert binascii.crc32(check)==expected,'CRC-invalid committed wire5 bank'
    return True

def validate_migration(source_bank,current_bank,source_image,current_image,prior_revision):
    assert prior_revision in (3,4,5,6),'Only explicitly supported same-wire5 inputs'
    validate_bank(source_bank,prior_revision);validate_bank(current_bank,7)
    assert len(source_image)==len(current_image)==32768
    offsets=[offset for offset in BANK_OFFSETS if bytes(source_image[offset:offset+BANK_SIZE])==bytes(source_bank)]
    assert len(offsets)==1,'Prior committed bank must occupy one known bank slot'
    offset=offsets[0]
    assert bytes(current_image[offset:offset+BANK_SIZE])==bytes(source_bank),'Prior committed bank overwritten'
    assert bytes(current_bank[32:])==bytes(source_bank[32:]),'Migration changed same-wire5 durable payload'
    return True
