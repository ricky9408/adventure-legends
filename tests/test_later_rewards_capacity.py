#!/usr/bin/env python3
"""Synthetic full160 roster at every fresh authored report source, real core."""
import ctypes as C
from test_later_rewards import LaterRewardTests,Instance,SOURCES
LaterRewardTests.setUpClass()
case=LaterRewardTests()
for treasure in range(4):
 for source in SOURCES[treasure]:
  case.setUp();s,c=case.state(treasure,True,source)
  for slot in range(160):
   if not s.roster.instances[slot].form_id:
    copy=Instance.from_buffer_copy(bytes(s.roster.instances[0]));copy.flags=1;copy.instance_id=s.roster.next_instance_id
    s.roster.instances[slot]=copy;s.roster.next_instance_id+=1
  assert case.l.save5_validate(C.byref(s))
  before=[bytes(x)for x in s.roster.instances];party=bytes(s.roster.party);gear=bytes(s.equipment);identity=s.roster.next_instance_id
  case.job(s,treasure,source,c)
  assert sum(bool(x.form_id)for x in s.roster.instances)==160
  assert bytes(s.roster.party)==party and bytes(s.equipment)==gear and s.roster.next_instance_id==identity
  for slot in range(160):
   if treasure<2 or slot not in s.roster.party:assert bytes(s.roster.instances[slot])==before[slot]
print('PASS all6 fresh report sources with160 occupied roster slots: no admission, loss, replacement, selection change or gear mutation')
