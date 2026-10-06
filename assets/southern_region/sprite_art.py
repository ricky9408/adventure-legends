"""Original Southern civic actors and mechanical 16px state icons."""
from generate_assets import Art
NAMES='GUIDE TAILOR MARKET RAIN PORTER CURATOR REST FERRY MIRROR_SLASH MIRROR_BACK HOOD SOCKET CLOCK SHADE_CLOSED SHADE_OPEN RAIN_PIPE HANDLE TRIAL CATCH ROOT DRAIN RIPPLE RESET TORN AWNING GATE WATER_LENS NOTICE RECEIVER CLOTH PLATE CORD BEACON MACHINE_IDLE MACHINE_WARN MACHINE_OPEN DONE REST_LIT'.split()
NPCS=set(NAMES[:6]);# These sprites are original 16x16 living civic characters and mechanical icons.
def sprite(n):
 a=Art(16,16,'transparent')
 if n in NPCS:
  idx=NAMES.index(n);cloth=['water2','fire2','purple2','pine3','gold1','rose3'][idx]
  a.e((2,12,13,15),'shadow');a.r((4,11,6,14),'wood0');a.r((9,11,11,14),'wood0');a.p([(4,6),(10,6),(12,9),(11,13),(4,13),(2,9)],cloth);a.l([(5,7),(5,11)],'white')
  a.r((5,2,10,6),'skin0' if idx%2 else 'skin1');a.r((4,1,11,3),'wood0');a.dot(9,4,'ink');a.dot(7,4,'ink');a.l([(7,6),(9,6)],'skin2')
  if n=='GUIDE':a.r((10,7,14,10),'plaster');a.l([(11,8),(13,8)],'water2')
  if n=='TAILOR':a.r((1,7,4,10),'fire1');a.l([(2,8),(4,10)],'white');a.l([(11,7),(14,6)],'silver')
  if n=='MARKET':a.r((1,0,14,2),'wood4');a.r((4,0,10,1),'plaster');a.r((11,9,15,12),'wood3')
  if n=='RAIN':a.l([(12,12),(13,2)],'wood1',2);a.e((11,0,15,4),'water4')
  if n=='PORTER':a.r((0,5,4,11),'wood1');a.r((1,6,3,9),'wood4')
  if n=='CURATOR':a.r((10,8,14,11),'gold4');a.l([(11,9),(13,9)],'wood3')
 elif n.startswith('REST'):
  a.r((2,11,13,14),'stone2');a.r((5,4,10,12),'plaster');a.e((3,1,12,8),'gold1');a.e((5,3,10,6),'gold4' if n=='REST_LIT' else 'water3');a.l([(2,0),(13,0)],'fire2',2)
 elif n=='FERRY':
  a.r((7,7,8,15),'wood2');a.r((0,0,15,10),'wood1');a.r((1,1,14,9),'plaster');a.p([(3,5),(7,8),(12,5)],'water2');a.l([(7,2),(7,6)],'wood1');a.l([(2,1),(4,1)],'fire2');a.l([(8,1),(10,1)],'fire2')
 elif n.startswith('MIRROR'):
  a.e((0,1,15,14),'wood1');a.e((2,2,13,13),'stone3');a.e((3,3,12,12),'water1');a.l([(4,11),(11,4)] if n=='MIRROR_SLASH' else [(4,4),(11,11)],'watergleam',3);a.dot(7,7,'white');a.r((6,13,9,15),'gold1')
 elif n.startswith('SHADE'):
  a.e((0,12,15,15),'shadow');a.r((7,1,9,13),'wood1');a.e((5,6,11,12),'gold1');a.e((7,8,9,10),'gold4')
  if n=='SHADE_CLOSED':
   a.r((1,1,14,7),'wood0');a.r((2,2,13,6),'water2')
   for x in(4,8,12):a.l([(x,2),(x,6)],'water4')
  else:a.r((7,0,10,7),'water1');a.l([(8,0),(8,6)],'water4')
 elif n=='CLOCK':
  a.e((0,1,15,14),'wood1');a.e((2,2,13,12),'gold3');a.p([(8,3),(12,10),(8,10)],'purple1');a.l([(8,9),(6,4)],'wood1',2);a.r((6,13,9,15),'stone3')
 elif n.startswith('MACHINE'):
  a.e((0,0,15,15),'wood0');a.e((1,1,14,14),'gold1');a.e((3,3,12,12),'plaster');a.e((4,4,11,11),'fire1' if n.endswith('WARN') else 'water2' if n.endswith('OPEN') else 'stone2');a.e((6,6,9,9),'gold4');a.l([(1,7),(3,7)],'silver');a.l([(12,7),(14,7)],'silver');a.r((6,13,9,15),'wood2')
 elif n=='DONE':a.e((2,2,13,13),'pine1');a.e((3,3,12,12),'pine4');a.l([(4,7),(7,10),(12,4)],'white',2)
 elif n in{'TRIAL','NOTICE','RESET'}:
  a.r((6,9,9,15),'wood1');a.r((1,0,14,11),'wood1');a.r((2,1,13,10),'plaster')
  if n=='TRIAL':a.p([(8,2),(12,6),(8,9),(4,6)],'gold1');a.dot(8,4,'white')
  elif n=='NOTICE':a.l([(4,3),(11,3)],'wood2');a.l([(4,6),(11,6)],'wood2');a.dot(5,8,'water2')
  else:a.l([(11,4),(8,2),(4,4),(4,7),(7,9),(11,7)],'water2',2);a.p([(9,2),(12,4),(9,5)],'water2')
 elif n in{'ROOT','CORD'}:
  a.r((2,11,13,14),'wood2');a.l([(4,12),(6,5),(9,4),(11,12)],'wood1',2);a.l([(3,8),(12,8)],'leaflight' if n=='ROOT' else 'gold3',2)
  if n=='ROOT':a.p([(6,6),(1,2),(7,3)],'pine4');a.p([(8,5),(13,1),(13,5)],'pine3')
  else:a.e((5,1,10,6),'wood1');a.e((6,2,9,5),'wood4')
 elif n in{'DRAIN','SOCKET','PLATE','RECEIVER'}:
  a.e((0,3,15,14),'stone1');a.e((1,2,14,12),'stone4');a.e((3,4,12,10),'wood1')
  if n=='DRAIN':
   for x in(4,7,10):a.l([(x,5),(x,9)],'silver')
  elif n=='SOCKET':a.p([(8,4),(11,8),(5,8)],'gold3')
  elif n=='PLATE':a.r((4,5,11,9),'gold2');a.dot(6,6,'gold4')
  else:a.e((4,4,11,10),'water3');a.p([(6,5),(10,5),(8,9)],'white')
 elif n=='RIPPLE':
  a.e((0,5,15,12),'water2');a.l([(2,7),(6,7)],'watergleam');a.l([(8,10),(13,10)],'water4');a.p([(6,4),(11,1),(10,5)],'pine4')
 elif n=='RAIN_PIPE':
  a.r((3,0,8,10),'stone1');a.r((4,0,6,9),'silver');a.r((6,8,12,12),'stone2');a.l([(7,9),(12,9)],'water4');a.l([(12,10),(12,14)],'water3',2)
 elif n in{'CATCH','HANDLE'}:
  a.r((2,9,13,14),'stone2');a.r((3,10,12,12),'plaster');a.l([(7,10),(10,3)],'wood1',3);a.e((8,0,13,5),'gold2')
  if n=='CATCH':a.l([(2,2),(5,2),(5,7)],'silver',2);a.l([(14,2),(11,2),(11,7)],'silver',2)
 elif n in{'HOOD','AWNING','TORN','CLOTH'}:
  a.r((2,12,13,14),'wood1')
  if n=='HOOD':a.p([(2,10),(4,3),(11,2),(14,9),(10,12),(4,12)],'stone2');a.e((5,5,11,10),'deep');a.l([(4,3),(11,2)],'silver')
  else:
   a.r((1,1,14,3),'wood2');a.p([(2,3),(13,3),(14,11),(10,13),(2,11)],'water2' if n=='CLOTH' else 'fire2');a.l([(5,3),(6,11)],'plaster',2);a.l([(10,3),(11,11)],'plaster',2)
   if n=='TORN':a.p([(8,5),(11,6),(8,9),(11,11),(7,11)],'transparent')
 elif n=='BEACON':
  a.r((3,11,12,14),'stone2');a.r((5,4,10,11),'gold1');a.r((4,2,11,4),'wood1');a.r((6,5,9,9),'fire2');a.dot(7,5,'gold4')
 elif n=='WATER_LENS':
  a.e((0,1,15,14),'stone2');a.e((2,2,13,12),'plaster');a.e((4,4,11,10),'water2');a.p([(8,3),(11,8),(8,10),(5,8)],'watergleam');a.l([(1,14),(14,14)],'water3')
 elif n=='GATE':
  a.r((0,1,3,15),'gold1');a.r((12,1,15,15),'gold1');a.r((1,2,2,14),'plaster');a.r((13,2,14,14),'plaster');a.r((0,0,15,3),'wood2');a.r((4,5,11,12),'water1');a.l([(5,6),(10,11)],'water4');a.l([(10,6),(5,11)],'water4')
 return a

