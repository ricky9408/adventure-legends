from pathlib import Path
import json,re,struct,xml.etree.ElementTree as X
O=Path(__file__).parent;d=json.loads((O/'composition_events.json').read_text());roles=['melody','inner','bass']
def pm(p):
 m=re.fullmatch(r'([A-G])([#b]?)(\d)',p);return 12*(int(m[3])+1)+dict(C=0,D=2,E=4,F=5,G=7,A=9,B=11)[m[1]]+{'':0,'#':1,'b':-1}[m[2]]
assert len(d['bars'])==24
for b in d['bars']:
 for role in roles:
  es=b[role];assert sum(e['duration'] for e in es)==3
  for i,e in enumerate(es):assert e['onset']==sum(x['duration'] for x in es[:i])
x=X.parse(O/'where_the_reeds_turn.musicxml')
for p,role in zip(x.findall('part'),roles):
 assert len(p.findall('measure'))==24
 for m,b in zip(p.findall('measure'),d['bars']):
  assert sum(int(n.findtext('duration')) for n in m.findall('note'))==1440
  for n,e in zip(m.findall('note'),b[role]):
   assert int(n.findtext('duration'))==round(e['duration']*480)
   if e['pitch']=='R':assert n.find('rest') is not None
   else:
    pp=n.find('pitch');p=pp.findtext('step')+{'1':'#','-1':'b','0':''}[pp.findtext('alter','0')]+pp.findtext('octave');assert p==e['pitch']
raw=(O/'where_the_reeds_turn.mid').read_bytes();assert raw[:4]==b'MThd';fmt,nt,ppq=struct.unpack('>HHH',raw[8:14]);assert (fmt,nt,ppq)==(1,4,480);pos=14;summary=[]
def vlq(raw,pos):
 val=0
 while True:
  b=raw[pos];pos+=1;val=(val<<7)|(b&127)
  if b<128:return val,pos
for tr in range(nt):
 assert raw[pos:pos+4]==b'MTrk';size=int.from_bytes(raw[pos+4:pos+8],'big');buf=raw[pos+8:pos+8+size];pos+=8+size;i=t=0;active={};ns=[];name='';peak=0
 while i<len(buf):
  dt,i=vlq(buf,i);t+=dt;status=buf[i];i+=1
  if status==255:
   typ=buf[i];i+=1;ln,i=vlq(buf,i);payload=buf[i:i+ln];i+=ln
   if typ==3:name=payload.decode()
  elif status&240==192:i+=1
  elif status&240 in [128,144]:
   pitch,vel=buf[i:i+2];i+=2
   if status&240==144 and vel:
    assert pitch not in active;active[pitch]=t;ns.append([t,pitch]);peak=max(peak,len(active))
   else:assert pitch in active;assert t>active.pop(pitch)
  else:raise ValueError(status)
 assert not active and t==34560
 if tr:
  role=roles[tr-1];expected=[[round(((b['number']-1)*3+e['onset'])*480),pm(e['pitch'])] for b in d['bars'] for e in b[role] if e['pitch']!='R'];assert ns==expected;assert peak==1
 summary.append(dict(track=name,notes=len(ns),max_polyphony=peak,end_tick=t))
ranges={role:[min(pm(e['pitch']) for b in d['bars'] for e in b[role] if e['pitch']!='R'),max(pm(e['pitch']) for b in d['bars'] for e in b[role] if e['pitch']!='R')] for role in roles}
intervals=[]
for b in d['bars']:
 for t in [i*.5 for i in range(6)]:
  pitches={}
  for role in roles:
   e=next(e for e in b[role] if e['onset']<=t<e['onset']+e['duration'])
   if e['pitch']!='R':pitches[role]=pm(e['pitch'])
  assert pitches['bass']<pitches['inner']
  if 'melody' in pitches:assert pitches['inner']<pitches['melody']
report=dict(title=d['title'],bars=24,meter='3/4',tempo=88,beats=72,duration_seconds=72*60/88,bar_totals_pass=True,xml_pitch_duration_match=True,midi_note_onsets_match=True,midi_tracks=summary,ranges_midi=ranges,simultaneous_voice_crossings=0,voice_polyphony_limit=3,loop_ticks=34560,rests_in_melody=sum(e['pitch']=='R' for b in d['bars'] for e in b['melody']),audible_review_performed=False,visual_review='All 3 PDF pages visually inspected after engraving correction.',independent_review='Score-level pass for audition candidate; see INDEPENDENT-REVIEW.md. Audio and in-game approval pending.')
(O/'validation.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
