#!/usr/bin/env python3
"""Portable source-contract supplement to the real linked scheduler test.
These checks are not timing, pixel, or native gameplay evidence.
"""
from pathlib import Path
import os,re,unittest
ROOT=Path(os.environ.get('MAGMA_BOUNDARY_SOURCE',Path(__file__).resolve().parents[1]))
class Contract(unittest.TestCase):
 def test_owned_entry_integration(self):
  s=(ROOT/'src/game.c').read_text();start=re.search(r'COLD void enter_room\([^;{}]+\)\{',s).start();end=s.index('COLD void start_game',start);s=s[start:end]
  self.assertIn('int magma=(unsigned)r-38u<8u&&!restoring_checkpoint&&!(room==46&&r==38&&fromnorth==4);',s)
  self.assertLess(s.index('magma_game_request_enter('),s.index('room=r;'))
  self.assertIn('if(!southern&&!magma)trials_enter(r)',s)
  self.assertIn('fromnorth==2&&!southern&&!magma',s)
  self.assertIn('if(magma_game_enter((unsigned)r,(unsigned)fromnorth)&&magma)trials_enter(r)',s)
  self.assertIn('!(magma&&magma_game_enter_pending())',s)
 def test_event_owned_commit(self):
  s=(ROOT/'src/underwater_engine.inc').read_text();self.assertIn('magma_game_enter_pending()',s);self.assertIn('magma_entering?magma_game_prepare_enter()',s);self.assertLess(s.index('game_state=event_resume_state;',s.index('status=')),s.index('magma_game_commit_enter()'))
 def test_busy_save_does_not_advance(self):
  s=(ROOT/'src/game.c').read_text();a=s.index('if(save_begin_pending>1)');b=s.index('if(save_begin_pending){',a);part=s[a:b]
  self.assertIn('magma_game_prepare_save_step()',part)
  self.assertLess(part.index('if(prepared==SAVE5_BUSY)return;'),part.index('save_begin_pending--;'))
  self.assertIn('if(prepared!=SAVE5_DONE)',part);self.assertIn('save_completion_pending=SAVE5_FAILED',part)
 def test_exact_source_and_shell_separation(self):
  s=(ROOT/'src/magma_enter_job.inc').read_text();self.assertIn('room==46&&area==38&&spawn==4',s);self.assertGreaterEqual(s.count('save5_preflight_matches('),2)
  a=(ROOT/'src/magma_anchor_job.inc').read_text();self.assertIn('save5_preflight_matches(',a);self.assertIn('adventure_save.campaign.spawn=3',a);self.assertNotIn('save5_validate(',a)
if __name__=='__main__':unittest.main(verbosity=2)
