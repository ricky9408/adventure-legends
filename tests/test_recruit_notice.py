#!/usr/bin/env python3
"""Real-core discovery acknowledgement, codec roundtrip and ownership tests.
This is a host regression, separate from native controller/visual proof.
"""
import ctypes as C
import os,subprocess,tempfile,unittest
from pathlib import Path
from test_save5 import ROOT,Save,compare_state

class RecruitNoticeTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.tmp=tempfile.TemporaryDirectory(prefix='recruit-notice-');cls.addClassCleanup(cls.tmp.cleanup)
  d=Path(cls.tmp.name);(d/'adapter.c').write_text('''
#include "save5.h"
Save5State adventure_save;
unsigned notice_pixels;
void rect(int x,int y,int w,int h,unsigned char color){(void)x;(void)y;(void)color;notice_pixels+=(unsigned)(w*h);}
''')
  flags=['-fsanitize=undefined','-fno-sanitize-recover=all']if os.environ.get('RECRUIT_NOTICE_SANITIZE')else[]
  out=d/'core.so'
  subprocess.run(['cc','-std=c99','-O2','-Wall','-Wextra','-Werror','-ffreestanding','-fno-builtin','-DSAVE4_HOST_TEST','-DSAVE5_HOST_TEST','-shared','-fPIC','-I'+str(ROOT/'src'),*flags,str(d/'adapter.c'),*[str(ROOT/'src'/n)for n in ('recruit_notice.c','save4.c','save5.c','creatures.c','creature_data.c','equipment.c','equipment_data.c')],'-o',str(out)],check=True)
  cls.l=C.CDLL(str(out));cls.s=Save.in_dll(cls.l,'adventure_save');cls.ram=(C.c_ubyte*32768).in_dll(cls.l,'save5_test_sram')
  for n in ('save5_store','save5_load','save5_validate','save5_preflight_begin'):getattr(cls.l,n).argtypes=[C.POINTER(Save)]
  cls.l.save5_preflight_step.argtypes=[C.c_uint,C.c_uint]
 def setUp(self):
  self.l.save5_test_reset_writer();self.l.save5_test_fail_after(-1);self.l.save5_preflight_cancel()
  C.memset(C.addressof(self.s),0,C.sizeof(self.s));self.ram[:]=bytes([255])*32768
  self.l.equipment_init(C.byref(self.s.equipment));self.assertEqual(self.l.creatures_migrate_legacy(C.byref(self.s.roster),0,0),1)
 def grant(self,legacy):
  self.s.campaign.chapter_flags=1 if legacy==2 else 3
  self.s.campaign.spawn=3
  for i in range(2,legacy+1):self.assertLess(self.l.creatures_grant_story(C.byref(self.s.roster),i,self.s.campaign.chapter_flags),160)
  return next(c for c in self.s.roster.instances if c.flags&2 and c.form_id==(7 if legacy==2 else 10))
 def pending(self,c):return self.l.recruit_notice_pending(C.byref(c))
 def ack(self,c):return self.l.recruit_notice_acknowledge(C.byref(c))
 def test_starters_unmarked_boss_recruits_pending_without_awards(self):
  self.assertFalse(self.pending(self.s.roster.instances[0]));self.assertFalse(self.pending(self.s.roster.instances[1]))
  wind=self.grant(2);before=bytes(self.s.roster)
  self.assertTrue(self.pending(wind));self.assertEqual(bytes(self.s.roster),before)
  stone=self.grant(3);self.assertTrue(self.pending(wind));self.assertTrue(self.pending(stone));self.assertEqual(self.l.save5_validate(C.byref(self.s)),1)
 def test_acknowledge_specific_story_member_once_keeps_all_progress(self):
  wind=self.grant(2);stone=self.grant(3);before=bytes(self.s);roster=bytes(self.s.roster)
  self.assertEqual(self.ack(wind),1);self.assertEqual(self.s.economy.reserved[1],1)
  self.assertFalse(self.pending(wind));self.assertTrue(self.pending(stone));self.assertEqual(self.ack(wind),0)
  self.assertEqual(bytes(self.s.roster),roster);self.assertEqual(self.l.save5_validate(C.byref(self.s)),1)
  after=bytes(self.s);self.assertEqual(sum(a!=b for a,b in zip(before,after)),1)
 def test_acknowledgement_roundtrip_preserves_uninspected_member(self):
  wind=self.grant(2);stone=self.grant(3);self.assertEqual(self.l.save5_store(C.byref(self.s)),1)
  self.assertEqual(self.ack(wind),1);self.assertEqual(self.l.save5_store(C.byref(self.s)),1)
  expected=compare_state(self.s);C.memset(C.addressof(self.s),0,C.sizeof(self.s))
  self.assertEqual(self.l.save5_load(C.byref(self.s)),1);self.assertEqual(compare_state(self.s),expected)
  self.assertFalse(self.pending(self.s.roster.instances[2]));self.assertTrue(self.pending(self.s.roster.instances[3]))
 def test_preflight_ownership_defers_acknowledgement(self):
  wind=self.grant(2);token=self.l.save5_preflight_begin(C.byref(self.s));self.assertTrue(token)
  before=bytes(self.s);self.assertEqual(self.ack(wind),0);self.assertEqual(bytes(self.s),before)
  self.l.save5_preflight_cancel();self.assertEqual(self.ack(wind),1)
 def test_unowned_world_marker_survives_evolution_history(self):
  self.assertTrue(self.l.recruit_notice_world(13));self.assertFalse(self.l.recruit_notice_world(0));self.assertFalse(self.l.recruit_notice_world(129))
  self.s.roster.obtained[1]|=1<<4
  self.assertFalse(self.l.recruit_notice_world(13))
 def test_no_acknowledgement_without_recruit_or_chapter_proof(self):
  self.s.economy.reserved[1]=1;self.assertEqual(self.l.save5_validate(C.byref(self.s)),0)
  self.s.campaign.chapter_flags=1;self.assertEqual(self.l.save5_validate(C.byref(self.s)),0)
  self.s.economy.reserved[1]=0;wind=self.grant(2);self.assertEqual(self.ack(wind),1)
  self.s.economy.reserved[1]|=4;self.assertEqual(self.l.save5_validate(C.byref(self.s)),0)
 def test_badge_is_static_bounded_native_text(self):
  pixels=C.c_uint.in_dll(self.l,'notice_pixels');pixels.value=0;self.l.recruit_notice_badge(20,54)
  self.assertGreater(pixels.value,13*7);self.assertLess(pixels.value,13*7+45)

if __name__=='__main__':unittest.main()
