"""Spoiler-bearing actual-controller collection route, no fixture awards."""
from collections import deque
class UnderwaterCollectionRoute:
 def travel(self,target,clear=False):
  here=self.get('room')
  if here==target:return
  graph={46:[47,48],47:[46,50],48:[46,49,51],49:[48,52],50:[47,51],51:[50,52,48],52:[51,53,49],53:[52,46]}
  queue=deque([(here,[])])
  seen={here}
  while queue:
   r,path=queue.popleft()
   if r==target:
    for to in path:self.entry(to)
    return
   for to in graph[r]:
    if to not in seen:seen.add(to);queue.append((to,path+[to]))
  raise AssertionError(('disconnected underwater route',here,target))
 def to_town(self):self.travel(46)
 def optional_recruits(self):
  self.to_town()
  for slot,item in ((0,1),(1,36),(2,53),(3,67),(4,82)):self.equip_item(slot,item)
  for xy in ((160,176),(304,176),(240,240),(240,104),(240,104),(240,104),(384,128)):self.target(*xy)
  self.check(self.quest(41)==3,'distinct town voices and public mural claim one parade reward')
  self.travel(47)
  for xy in ((64,112),(112,112),(64,112),(352,160),(376,184)):self.target(*xy)
  self.check(self.quest(43)==3 and any(c.form_id==58 for c in self.live()),'Commons bench return and guide invitation earned')
  self.travel(48)
  for xy in ((112,92),(144,92),(64,224),(96,224),(240,80)):self.target(*xy)
  self.target(280,224,2);self.target(432,256)
  self.check(self.quest(42)==3 and all(any(c.form_id==f for c in self.live()) for f in (55,64)),'shoal route and two distinct first invitations earned')
  self.travel(49);self.target(144,52);self.target(172,52);self.target(120,48)
  self.cast_position(49,120,72,1,67,'garden-discovery-echo');self.target(64,56)
  self.check(all(any(c.form_id==f for c in self.live()) for f in (61,70)),'garden shade and real echo discovery earn separate companions')
  self.travel(51);self.target(160,80);self.target(160,112);self.target(144,96,2)
  self.check(any(c.form_id==67 for c in self.live()),'two observed boards and side invitation earn Claspcoil')
  self.travel(53);self.target(208,112)
  self.check(self.get('room')==46,'restored return arch connects to town')
  self.entry(48);self.entry(49);self.entry(48);self.entry(46)
  self.target(240,272);self.target(384,160)
  self.check(all(self.quest(q)==3 for q in range(38,46)),'all eight new quests claim their real rewards')
  self.check(len(self.live())==self.prior_count+8,'eight first invitations retain eight distinct new IDs')
  self.check(sum(bool(g.item_id) for g in self.state().equipment.bag)==37,'all37 actual equipment items earned including two-item return reward')
  self.target(80,256);self.snapshot('10-all-eight-families-and-stories')
 def trial_bytes(self):return list(self.e.bytes(self.sym['underwater_game_trial'],32))
 def trial_point(self,n):
  idx=self.trial_bytes()[12];cx,cy=(240,160) if self.get('room') in (48,51) else (120,80)
  if idx==9:return cx-36+(n%3)*36,cy-18+(n//3)*36
  offsets=((-48,-24),(48,-24),(0,32),(64,32),(0,-24),(0,28)) if idx==15 else ((-48,-20),(48,-20),(-48,20),(48,20),(0,-24),(0,28))
  return cx+offsets[n][0],cy+offsets[n][1]
 def trial_a(self,n,times=1):
  for _ in range(times):self.target(*self.trial_point(n))
 def trial_cast(self,n):
  form=self.selected().form_id;family=(form-49)//3;command=67+family*3
  x,y=self.trial_point(n);forward=(24,24,12,12,8,16,6,12)[family];side=-10 if family==7 else 0
  # Ordinary approach tolerance must be sufficient for the visible target.
  self.ready();self.goto(x-side,y+forward,radius=4);self.face(1);self.ready()
  self.tap('R',2,55);self.settle()
 def trial_walk(self,x,y):
  cx,cy=(240,160) if self.get('room') in (48,51) else (120,80)
  self.goto(cx+x,cy+y,radius=3);self.step(3);self.settle()
 def start_underwater_trial(self,form,key):
  family=(form-49)//3;idx=family*2+key-1
  area=(50,52,51,49,48,48,50,51,49,48,48,51,51,52,49,52)[idx]
  self.to_town();self.target(80,256);self.travel(area)
  self.owned_select(form);self.set_command(67+family*3);self.ready();identity=self.selected().instance_id
  large=area in (48,51);self.target((80 if key==1 else 400) if large else (48 if key==1 else 192),240 if large else 112)
  t=self.trial_bytes();self.check(t[12]==idx and int.from_bytes(bytes(t[:4]),'little')==identity,'actual lectern locks authored trial and exact chosen individual')
  self.snapshot(f'trial-{idx:02d}-start')
  return identity,idx
 def solve_underwater_trial(self,idx):
  if idx in (0,1):
   self.trial_a(0)
   if idx==0:self.trial_a(1)
   self.trial_cast(0);self.trial_cast(1)
  elif idx==2:self.trial_cast(0);self.trial_walk(64,28);self.trial_cast(1)
  elif idx==3:
   self.trial_cast(0);self.trial_cast(1);self.trial_cast(1);self.trial_walk(-64,28);self.trial_walk(64,28)
  elif idx==4:self.trial_cast(0);self.trial_cast(1);self.trial_a(4)
  elif idx==5:
   self.trial_a(0);self.trial_a(1);self.trial_walk(-64,28);self.trial_walk(64,28);self.trial_cast(4)
  elif idx==6:self.trial_a(0);self.trial_a(1);self.trial_a(2);self.trial_cast(4)
  elif idx==7:self.trial_a(0);self.trial_a(1,2);self.trial_cast(4)
  elif idx==8:self.trial_cast(0);self.trial_a(0);self.trial_a(1)
  elif idx==9:
   for n in (0,1,2,5):self.trial_cast(n)
  elif idx==10:self.trial_cast(2);self.trial_a(4,3)
  elif idx in (11,12,14):
   self.trial_a(0);self.trial_a(1,3)
   if idx==11:self.trial_a(2)
   self.trial_cast(0);self.trial_cast(1)
  elif idx==13:
   self.trial_a(4,2);self.trial_cast(4)
   for x,y in ((-48,-12),(-48,28),(0,8),(48,-12),(48,28),(0,8)):self.trial_walk(x,y)
  elif idx==15:
   for n in (0,1,2):self.trial_a(n)
   for n in (0,1,2):self.trial_cast(n)
 def evolve_underwater(self,source,target):
  self.to_town();self.target(80,256);self.owned_select(source);identity=self.selected().instance_id;slot=self.roster().party[self.roster().selected_party]
  self.open_tab(3);self.tap('SELECT');before=bytes(self.roster());self.tap('B')
  self.check(self.get('game_state')==3 and bytes(self.roster())==before,'declined preparation leaves roster byte-identical')
  self.tap('SELECT');self.wait_evolution(require_ready=False)
  if self.get('progression_evolution_target')!=target:self.tap('RIGHT')
  self.check(self.get('progression_evolution_target')==target,'actual selected evolution target matches earned branch')
  self.wait_evolution();self.e.screenshot(self.out/f'evolve-{source}-{target}-choice.png');self.tap('A');self.wait_evolution(8);self.settle();self.close_menu()
  c=self.roster().instances[slot];self.check(c.instance_id==identity and c.form_id==target,'evolution transforms same retained individual into chosen form')
  self.snapshot(f'evolved-{target}')
 def repeat_underwater(self,form):
  family=(form-49)//3;area=(46,46,48,47,49,48,51,49)[family]
  self.travel(area);before={c.instance_id:bytes(c) for c in self.live()}
  if family==0:self.target(64,72);self.target(64,72);inv=(64,104)
  elif family==1:self.target(416,72,3);self.goto(448,108);self.step(3);inv=(416,108)
  elif family==2:self.target(368,208);self.goto(400,208);self.step(3);inv=(368,256)
  elif family==3:self.target(392,240);self.goto(424,240);self.step(3);inv=(416,264)
  elif family==4:self.target(208,64);self.target(208,64);inv=(208,96)
  elif family==5:
   for _ in range(3):self.target(304,80)
   self.target(272,80);inv=(336,80)
  elif family==6:self.target(384,64);self.target(416,64);inv=(400,96)
  else:self.target(80,88);self.target(112,88);inv=(64,88)
  self.target(*inv);fresh=[c for c in self.live() if c.instance_id not in before]
  self.check(len(fresh)==1 and fresh[0].form_id==form and fresh[0].bond==20 and fresh[0].trial_flags==0,'new repeat demonstration grants one genuine untrained base individual')
  self.check(all(bytes(c)==before[c.instance_id] for c in self.live() if c.instance_id in before),'repeat invitation neither replaces nor trains any prior individual')
  after=bytes(self.roster());self.target(*inv);self.check(bytes(self.roster())==after,'same-attempt repeat interaction cannot duplicate companion reward')
  self.snapshot(f'repeated-base-{form}')
 def collection_route(self):
  self.optional_recruits()
  for base in range(49,73,3):
   for key in (1,2):
    identity,idx=self.start_underwater_trial(base,key);self.solve_underwater_trial(idx);c=self.selected()
    self.check(c.instance_id==identity and c.form_id==base and c.trial_flags&key,'physical trial awards proof only to exact same base individual')
    self.check(c.level>=28 and c.bond>=45,'authored trial provides stated evolution floor without grinding')
    self.snapshot(f'trial-{idx:02d}-complete');self.evolve_underwater(base,base+key)
    if key==1:self.repeat_underwater(base)
  self.check(len(self.live())==50 and len(self.collection())==89,'all89 histories earned with50 real retained individuals')
  self.target(80,256);self.snapshot('11-all89-earned-town')
