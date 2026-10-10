#!/usr/bin/env python3
"""Retained Southern/Magma runtime scenarios with the new engine scheduling.
Only the host driver changes: after every real action it freezes and drains
one typed queue exactly as EVENT_PENDING does, before the next synthetic input.
Original runtime assertions and historical fixtures are unchanged.
"""
import ctypes as C,unittest
import test_south_game as south
import test_magma_game as magma

def install(module,region,names):
 lib=module.L;pending=getattr(lib,region+'_game_quest_pending');seal=getattr(lib,region+'_game_quest_seal');prepare=getattr(lib,region+'_game_quest_prepare');commit=getattr(lib,region+'_game_quest_commit')
 def settle():
  if not pending():return
  assert seal()==1,'queue must seal at the action boundary'
  C.c_int.in_dll(lib,'game_state').value=10
  for _ in range(160):
   result=prepare()
   if result!=1:break
  assert result==2,('bounded quest preparation failed',region,result)
  C.c_int.in_dll(lib,'game_state').value=1
  assert commit()==1,'one complete private commit'
 for name in names:
  original=getattr(lib,name)
  def action(*args,original=original):
   result=original(*args);settle();return result
  setattr(lib,name,action)

install(south,'south',['south_game_interact','south_game_power','south_game_weapon_hit','tick'])
install(magma,'magma',['magma_game_interact','magma_game_input','magma_game_power','magma_game_weapon_hit','magma_game_command_hit','tick'])
if __name__=='__main__':
 suite=unittest.TestSuite([unittest.defaultTestLoader.loadTestsFromTestCase(south.SouthRuntime),unittest.defaultTestLoader.loadTestsFromTestCase(magma.MagmaRuntime)])
 result=unittest.TextTestRunner(verbosity=2).run(suite)
 raise SystemExit(not result.wasSuccessful())
