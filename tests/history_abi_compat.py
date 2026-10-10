"""Test-only32-byte zero extension of frozen pre-economy output buffers.

The independent old codec and its old wire grammar remain untouched.
"""
import ctypes as C
from test_save5 import Save
def adapt_harness(root,harness):
 header=(root/'src/save5.h').read_text();old='EconomyState economy;'not in header
 if not old:return harness,False
 assert C.sizeof(Save)-Save.economy.offset==32
 for before,after in [('return sizeof(Save5State);','return sizeof(Save5State)+32;'),('memset(out, 0xcc, sizeof *out);','memset(out,0xcc,sizeof *out+32);'),('valid = (unsigned)save5_has_valid();','if(accepted)memset((unsigned char*)out+sizeof *out,0,32);\n    valid=(unsigned)save5_has_valid();'),('memset(s, 0, sizeof *s);','memset(s,0,sizeof *s+32);')]:
  assert harness.count(before)==1,before;harness=harness.replace(before,after)
 harness+='''
static int history_extension_zero(const Save5State*s){unsigned i;const unsigned char*p;
 if(!s)return 0;
 p=(const unsigned char*)s+sizeof *s;
 for(i=0;i<32;++i)if(p[i])return 0;
 return 1;}
int history_validate_compat(const Save5State*s){return history_extension_zero(s)&&save5_validate(s);}
'''
 if 'save5_validate_revision'in header:harness+='int history_validate_revision_compat(const Save5State*s,unsigned r){return history_extension_zero(s)&&save5_validate_revision(s,r);}\n'
 return harness,True
def bind_compat(lib,old):
 if old:
  lib.save5_validate=lib.history_validate_compat
  if hasattr(lib,'history_validate_revision_compat'):lib.save5_validate_revision=lib.history_validate_revision_compat
 lib.save5_validate.argtypes=[C.POINTER(Save)]
 if hasattr(lib,'save5_validate_revision'):lib.save5_validate_revision.argtypes=[C.POINTER(Save),C.c_uint]
