from pathlib import Path
import json,struct,xml.etree.ElementTree as X,re
O=Path(__file__).parent;d=json.loads((O/'composition_events.json').read_text());roles=['melody','inner','bass']
def pm(p):
 m=re.fullmatch(r'([A-G])([#b]?)(\d)',p);return 12*(int(m[3])+1)+dict(C=0,D=2,E=4,F=5,G=7,A=9,B=11)[m[1]]+{'':0,'#':1,'b':-1}[m[2]]
expected={r:[] for r in roles}
for b in d['bars']:
 for r in roles:
  assert sum(e['duration'] for e in b[r])==3
  t=0
  for e in b[r]:
   assert e['onset']==t
   if e['pitch']!='R':expected[r].append((int(((b['number']-1)*3+t)*480),pm(e['pitch']),int(e['duration']*480)))
   t+=e['duration']
x=X.parse(O/'under_the_rootbound_arch.musicxml')
for r,p in zip(roles,x.findall('part')):
 actual=[];base=0
 for m in p.findall('measure'):
  t=0
  for n in m.findall('note'):
   du=int(n.findtext('duration'));pitch=n.find('pitch')
   if pitch is not None:
    val=(int(pitch.findtext('octave'))+1)*12+dict(C=0,D=2,E=4,F=5,G=7,A=9,B=11)[pitch.findtext('step')]+int(pitch.findtext('alter','0'));actual.append((base+t,val,du))
   t+=du
  assert t==1440;base+=t
 assert actual==expected[r],r
buf=(O/'under_the_rootbound_arch.mid').read_bytes();assert struct.unpack('>IHHH',buf[4:14])==(6,1,4,480);pos=14;decoded={};eots=[];pedal=[]
def vl(data,i):
 v=0
 while True:
  a=data[i];i+=1;v=(v<<7)|(a&127)
  if a<128:return v,i
for tid in range(4):
 assert buf[pos:pos+4]==b'MTrk';n=int.from_bytes(buf[pos+4:pos+8],'big');data=buf[pos+8:pos+8+n];pos+=8+n;i=t=0;name='';active={};notes=[]
 while i<len(data):
  delta,i=vl(data,i);t+=delta;st=data[i];i+=1
  if st==255:
   ty=data[i];i+=1;sz,i=vl(data,i);v=data[i:i+sz];i+=sz
   if ty==3:name=v.decode()
   if ty==47:eots.append(t)
   continue
  op=st&240
  if op in (192,208):i+=1;continue
  a,b=data[i:i+2];i+=2
  if op==144 and b>0:
   assert not active,('polyphony',name,t);active[a]=t
  elif op==128 or (op==144 and b==0):
   start=active.pop(a);notes.append((start,a,t-start))
  elif op==176 and a==64:pedal.append((t,b))
 assert not active
 decoded[name]=notes
for r in roles:assert decoded[r]==[(a,b,c-14) for a,b,c in expected[r]],r
assert eots==[34560]*4 and not pedal
# All vertical interval changes, including staggered half-beat inner entry.
vertical=[]
for bi,b in enumerate(d['bars']):
 points=sorted(set(e['onset'] for r in roles for e in b[r]))
 for t in points:
  pitches={}
  for r in roles:
   e=next(e for e in b[r] if e['onset']<=t<e['onset']+e['duration'])
   if e['pitch']!='R':pitches[r]=e['pitch']
  intervals={f'{a}/{bb}':(pm(pitches[a])-pm(pitches[bb]))%12 for a,bb in [('melody','inner'),('melody','bass'),('inner','bass')] if a in pitches and bb in pitches}
  vertical.append(dict(bar=bi+1,beat=t,pitches=pitches,interval_classes=intervals))
(O/'vertical_interval_audit.json').write_text(json.dumps(vertical,indent=2))
report=dict(title=d['title'],bars=24,meter='3/4',tempo=78,duration_seconds=72*60/78,bar_sums='All 72 voice-bars exactly 3 beats',xml='All 3 parts match JSON pitches, onsets, durations',midi='Parsed all binary tracks; every pitch and onset matches events; note-offs 14 ticks before notated end',tracks=4,individual_voice_files=3,maximum_polyphony=3,pedal_events=0,end_tick=34560,ranges={r:[min(p for _,p,_ in expected[r]),max(p for _,p,_ in expected[r])] for r in roles},voice_crossings=sum(1 for v in vertical for a,b in [('melody','inner'),('inner','bass')] if a in v['pitches'] and b in v['pitches'] and pm(v['pitches'][a])<=pm(v['pitches'][b])),audible_review_performed=False,visual_review='Both rendered PDF pages inspected; complete 24 bars, readable accidentals/durations, no clipping',loop='A7 to Dm(add9): C#5 to D5, G3 to rest then A3, A2 to D3. Exact 72-beat boundary; no notes or pedal extend past end.')
(O/'validation.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
