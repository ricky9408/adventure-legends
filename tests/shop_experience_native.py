#!/usr/bin/env python3
"""Controller-earned shop/tonic/reward regression with exact native frame tracing.

The supplied SRAM must come from the accepted controller campaign's grove-complete
checkpoint. This run imports ordinary SRAM only; it never writes game RAM or
imports machine states. Economy caps and injected save failures belong to the
separately labeled full native matrix.
"""
from pathlib import Path
import argparse,json,traceback,shutil
from player_feedback_campaign import FeedbackCampaign
from player_feedback_native import sha
class ShopExperience(FeedbackCampaign):
 def __init__(self,a):
  self.events=[];self.input_save=a.earned_save.resolve();self.input_hash=sha(self.input_save);self.complete=False
  super().__init__(a.rom,a.symbols,a.output,a.bridge)
  target=self.out/'test-source/tests/shop_experience_native.py';shutil.copyfile(__file__,target);self.experience_helper={'path':'test-source/tests/shop_experience_native.py','sha256':sha(target)};assert self.experience_helper['sha256']==sha(__file__)
  self.e.load_save(self.input_save);self.e.reset()
 def mark(self,label):
  s=self.save_state();row={'label':label,'hardware_frame':self.e.frame,**{n:self.get(n) for n in ('game_state','room','px','py','hero_hp_q4','ability_cd','game_shop_selection','game_shop_confirm','item_selection','feedback','reward_ticks','game_shop_reward_xp','game_shop_reward_gold','quickparty_open','journal_tab','kills')},'gold':s.economy.gold,'supplies':list(s.economy.supplies),'party_xp':[s.roster.instances[i].xp for i in s.roster.party if i<160]};self.events.append(row);return row
 def shot(self,name):self.raw_step(3);super().shot(name)
 def field_to_items(self):self.tap('START');self.tap('A');self.check(self.get('journal_tab')==15,'A opens Items from named hub')
 def run_shop(self):
  self.step(160);self.tap('A',4,4);self.dialogs();self.drain_background();self.mode='journey';self.check(self.get('game_state')==1 and self.get('room')==0,'controller-earned first-boss save cold-continues into village');self.check(self.save_state().economy.gold==72,'input is the documented earned72G checkpoint')
  self.goto(y=100);self.goto(x=56);self.tap('A');self.check(self.get('game_state')==11,'actual merchant interaction opens shop');self.shot('01-shop-readable-stock-prices')
  self.step(19,'DOWN');self.check(self.get('game_shop_selection')==2,'held Down repeats after18 updates');self.step(6,'DOWN');self.check(self.get('game_shop_selection')==0,'held Down continues at6-update cadence');self.step(3);self.step(30,'UP+DOWN');self.check(self.get('game_shop_selection')==0,'opposing shop directions are inert');self.step(3)
  self.step(60,'A');self.check(self.get('game_shop_confirm')==1 and self.save_state().economy.gold==72,'held first A only opens purchase review');self.step(3);self.shot('02-heart-purchase-review');self.raw_step(320,'A');self.check(self.save_state().economy.gold==54 and self.save_state().economy.supplies[0]==1 and not self.get('game_shop_confirm'),'held confirming A purchases once and does not reopen');self.step(3);self.shot('03-heart-purchase-saved')
  self.tap('DOWN');self.check(not self.get('feedback'),'moving to Spirit clears Heart purchase feedback');self.shot('04-spirit-selected-clean');self.tap('A');self.tap('A');self.check(self.save_state().economy.gold==30 and self.save_state().economy.supplies[1]==1,'real Spirit purchase costs24G exactly once')
  self.tap('DOWN');self.tap('A');self.tap('A');self.check(self.get('feedback')!=0 and self.save_state().economy.gold==30,'unaffordable Edge is refused without charge');self.shot('05-no-gold-with-controls');self.tap('B');self.tap('B');self.field_to_items();self.check(not self.get('feedback'),'shop refusal does not leak into Items');self.shot('06-items-heart-effect')
  self.tap('A');self.check(self.get('feedback') and not self.get('game_shop_confirm'),'full health refuses tonic without consuming');self.shot('07-full-health-with-controls');self.tap('DOWN');self.check(not self.get('feedback'),'Spirit selection clears obsolete full-heart message');self.shot('08-items-spirit-effect');self.tap('A');self.check(self.get('feedback') and not self.get('game_shop_confirm'),'ready power refuses Spirit without consuming');self.tap('B');self.step(3);self.check(not self.get('feedback'),'back to hub clears item feedback');self.tap('START')
  self.select(2);self.ready();self.tap('R');self.check(self.get('ability_cd')>0,'actual wind power creates cooldown');self.field_to_items();self.check(self.get('item_selection')==1,'selected supply is retained on return');self.tap('A');self.check(self.get('game_shop_confirm')==1,'Spirit use requires fresh confirmation');self.shot('09-spirit-use-effect');self.tap('A');self.check(self.save_state().economy.supplies[1]==0 and self.get('ability_cd')==0,'Spirit consumes once and readies actual power');self.shot('10-spirit-use-saved');self.tap('START')
  self.goto(x=120);self.nextroom(1);self.goto(y=272);self.goto(x=240);self.goto(y=180);self.goto(x=240);self.goto(y=92);self.goto(x=368);self.nextroom(2);self.dialogs();self.goto(y=94);self.goto(x=64);self.goto(y=84)
  for _ in range(1200):
   if self.get('hero_hp_q4')<self.e.read(self.sym['gear_stats'],2):break
   self.step(1)
  self.check(0<self.get('hero_hp_q4')<self.e.read(self.sym['gear_stats'],2),'enemy contact causes real nonfatal damage');self.field_to_items();self.tap('UP');before=self.get('hero_hp_q4');self.tap('A');self.shot('11-heart-use-effect');self.tap('A');self.check(self.save_state().economy.supplies[0]==0 and self.get('hero_hp_q4')==min(before+32,self.e.read(self.sym['gear_stats'],2)),'Heart consumes once and restores exactly two hearts up to maximum');self.shot('12-heart-use-saved');self.tap('START');self.select(0)
  before=self.save_state();before_xp=sum(before.roster.instances[i].xp for i in before.roster.party if i<160);initial=self.get('kills')
  for _ in range(300):
   if self.get('kills')>initial:break
   live=[]
   for i in range(6):
    a=self.sym['enemies']+20*i;x,y,hp=[self.e.read(a+n) for n in (0,4,8)]
    if hp:live.append((abs(x-self.get('px'))+abs(y-self.get('py')),x,y))
   self.check(bool(live),'authored enemy remains available until kill');distance,x,y=min(live);dx=x-self.get('px');dy=y-self.get('py');key=('LEFT' if dx<0 else 'RIGHT') if abs(dx)>abs(dy) else ('UP' if dy<0 else 'DOWN');self.step(6 if distance>24 else 1,key);self.tap('A');self.step(8)
  after=self.save_state();after_xp=sum(after.roster.instances[i].xp for i in after.roster.party if i<160);self.check(self.get('kills')==initial+1,'actual sword defeats enemy once');self.check(after.economy.gold-before.economy.gold==self.get('game_shop_reward_gold')==6,'reward G matches actual credit');self.check(after_xp-before_xp==self.get('game_shop_reward_xp')>0,'reward EXP matches actual party gains');self.shot('13-earned-reward');self.mark('reward-earned')
  self.tap('START');remaining=self.get('reward_ticks');self.step(120);self.check(self.get('reward_ticks')==remaining>0,'paused hub preserves remaining reward lifetime');self.tap('START');self.shot('14-reward-after-menu');self.mark('reward-after-menu')
  self.step(4,'L');self.check(self.get('quickparty_open')==1,'L opens familiar field picker');remaining=self.get('reward_ticks');self.step(120,'L');self.check(self.get('reward_ticks')==remaining>0,'held-L picker preserves remaining reward lifetime');self.e.screenshot(self.out/'15-picker-with-paused-reward.png');self.mark('reward-during-picker');self.step(3);self.shot('16-reward-after-picker');self.mark('reward-after-picker');self.step(self.get('reward_ticks')+3);self.check(not self.get('reward_ticks'),'reward expires after remaining visible duration');self.check(self.save_state().economy.gold==after.economy.gold,'paused redisplay never duplicates awarded money');self.snapshot('shop-experience-complete');self.complete=True
 def report_experience(self):
  (self.out/'shop-experience.json').write_text(json.dumps({'complete':self.complete,'candidate':self.candidate,'experience_helper':self.experience_helper,'controller_only':True,'game_ram_writes':0,'machine_state_imports':0,'input_sram':str(self.input_save),'input_sram_sha256':self.input_hash,'passes':self.passes,'failures':self.failures,'events':self.events,'native_observation':self.metrics},indent=2)+'\n')
def main():
 p=argparse.ArgumentParser(description=__doc__)
 for name in ('rom','symbols','bridge','earned-save','output'):p.add_argument('--'+name,type=Path,required=True)
 a=p.parse_args()
 if a.output.exists() and any(a.output.iterdir()):p.error('Use a fresh output directory')
 r=ShopExperience(a)
 try:r.run_shop()
 except Exception as exc:r.failures.append({'error':repr(exc),'status':r.status()});r.shot('failure');traceback.print_exc()
 finally:r.report_experience();r.report();r.trace.close();r.e.close()
 return int(not r.complete or bool(r.failures) or any(r.metrics[k] for k in ('update_misses','flip_misses','cycle_overruns','faults','publication_spills')))
if __name__=='__main__':raise SystemExit(main())
