from pathlib import Path
import json, re, struct, xml.etree.ElementTree as X
O=Path(__file__).parent
TITLE='Where the Mileposts Turn'
TEMPO=112
# Each pitch-duration pair is a compositional event, not a quantized performance.
mel=[
'G4:1 D5:1 B4:.5 A4:.5 G4:1',
'A4:2 B4:.5 D5:.5 C5:1',
'B4:1 E5:1 D5:.5 B4:.5 G4:1',
'F#4:2 A4:1 D5:1',
'E5:1 D5:.5 C5:.5 B4:1 A4:1',
'G4:3 B4:.5 C5:.5',
'D5:1 C5:1 B4:.5 A4:.5 C5:1',
'A4:2 F#4:1 A4:1',
'B4:2 G4:1 E5:1',
'D#5:1 F#5:.5 E5:.5 D#5:1 B4:1',
'E5:3 D5:.5 B4:.5',
'C5:1 E5:1 G5:2',
'F#5:1 E5:1 D5:.5 C5:.5 A4:1',
'B4:2 D5:1 G5:1',
'E5:1 C5:1 B4:.5 A4:.5 C5:1',
'A4:2 F#4:1 D5:1',
'G4:1 D5:1 B4:.5 A4:.5 G4:1',
'A4:2 B4:.5 D5:.5 E5:1',
'D5:1 G5:1 F#5:.5 E5:.5 D5:1',
'B4:2 A4:1 G4:1',
'E5:1 D5:.5 C5:.5 B4:1 A4:1',
'G4:2 B4:1 D5:1',
'C5:1 E5:1 D5:.5 C5:.5 A4:1',
'A4:2 C5:1 F#4:1']
# Quarter-note bass steps and paired light eighths make a walking pulse.
# The single left-hand line is playable and separated by musical role in MIDI.
lh=[
'G2 B2 D3 D3 B2 D3',
'F#2 A2 C3 D3 A2 C3',
'E2 G2 B2 B2 G2 B2',
'D2 F#2 A2 A2 F#3 D3',
'C3 E3 G3 G2 C3 E3',
'B2 D3 G3 D3 B2 D3',
'A2 C3 E3 E3 G3 C4',
'D3 F#3 A3 A2 C3 F#3',
'E3 G3 B3 B2 E3 G3',
'B2 D#3 F#3 F#2 A2 D#3',
'E3 G3 B3 B2 E3 G3',
'C3 E3 G3 G2 C3 E3',
'D3 F#3 A3 A2 C3 F#3',
'B2 D3 G3 D3 B2 D3',
'A2 C3 E3 E3 G3 C4',
'D3 F#3 A3 A2 C3 F#3',
'G2 B2 D3 D3 B2 D3',
'F#2 A2 C3 D3 A2 C3',
'E2 G2 B2 B2 G2 B2',
'B2 D3 G3 D3 B2 D3',
'C3 E3 G3 G2 C3 E3',
'B2 D3 G3 D3 B2 D3',
'A2 C3 E3 E3 G3 C4',
'D3 F#3 A3 D3 A3 C3']
chords=['G','D7/F#','Em7','D','Cmaj7','G/B','Am7','D7','Em','B7','Em7','C','D7','G/B','Am7','D7','G','D7/F#','Em7','G/B','Cmaj7','G/B','Am7','D7']
def pm(s):
 m=re.fullmatch(r'([A-G])([#b]?)(\d)',s);return 12*(int(m[3])+1)+dict(C=0,D=2,E=4,F=5,G=7,A=9,B=11)[m[1]]+{'#':1,'b':-1,'':0}[m[2]]
bars=[]
for n,(mm,ll,chord) in enumerate(zip(mel,lh,chords),1):
 melody=[dict(pitch=a.split(':')[0],duration=float(a.split(':')[1])) for a in mm.split()]
 left=[dict(pitch=a,duration=1 if i in (0,3) else .5,role='bass' if i in (0,3) else 'inner') for i,a in enumerate(ll.split())]
 assert sum(x['duration'] for x in melody)==4
 assert len(left)==6 and sum(e['duration'] for e in left)==4
 bars.append(dict(number=n,chord=chord,melody=melody,left=left))
(O/'composition_events.json').write_text(json.dumps(dict(title=TITLE,tempo=TEMPO,key='G major',meter='4/4',bars=bars),indent=2))
def sub(a,t,s=None,**attrs):
 b=X.SubElement(a,t,{k:str(v) for k,v in attrs.items()})
 if s is not None:b.text=str(s)
 return b
root=X.Element('score-partwise',version='4.0');sub(sub(root,'work'),'work-title',TITLE)
idn=sub(root,'identification');sub(idn,'creator','Original composition for Adventure Legends',type='composer')
pl=sub(root,'part-list');sp=sub(pl,'score-part',id='P1');sub(sp,'part-name','Piano');si=sub(sp,'score-instrument',id='I1');sub(si,'instrument-name','Acoustic Grand Piano');mi=sub(sp,'midi-instrument',id='I1');sub(mi,'midi-channel',1);sub(mi,'midi-program',1)
p=sub(root,'part',id='P1');types={.5:'eighth',1:'quarter',1.5:'quarter',2:'half',3:'half'}
for bar in bars:
 n=bar['number'];m=sub(p,'measure',number=n)
 if n==1:
  a=sub(m,'attributes');sub(a,'divisions',480);sub(sub(a,'key'),'fifths',1);t=sub(a,'time');sub(t,'beats',4);sub(t,'beat-type',4);sub(a,'staves',2)
  for sn,sg,li in [(1,'G',2),(2,'F',4)]:c=sub(a,'clef',number=sn);sub(c,'sign',sg);sub(c,'line',li)
  d=sub(m,'direction',placement='above');dt=sub(d,'direction-type');sub(dt,'words','Allegretto, with an easy traveling stride; sing the long notes');mt=sub(dt,'metronome');sub(mt,'beat-unit','quarter');sub(mt,'per-minute',TEMPO);sub(d,'sound',tempo=TEMPO)
  d=sub(m,'direction',placement='below');sub(sub(d,'direction-type'),'words','Brief half-pedal on each bass step; inner pairs light');sub(d,'staff',2)
 if n in (1,9,17):
  d=sub(m,'direction',placement='above');sub(sub(d,'direction-type'),'rehearsal',{1:'A',9:'B',17:"A′"}[n])
 if n in (1,9,13,17,21,24):
  d=sub(m,'direction',placement='below');dy=sub(sub(d,'direction-type'),'dynamics');sub(dy,{1:'mp',9:'mf',13:'mp',17:'mp',21:'mf',24:'mp'}[n]);sub(d,'staff',1)
 d=sub(m,'direction',placement='above');sub(sub(d,'direction-type'),'words',bar['chord']);sub(d,'staff',1)
 if n==24:
  d=sub(m,'direction',placement='above');sub(sub(d,'direction-type'),'words','Return directly to bar 1; keep the pulse')
 for staff,key in [(1,'melody'),(2,'left')]:
  if staff==2:sub(sub(m,'backup'),'duration',1920)
  pos=0
  for i,e in enumerate(bar[key]):
   nt=sub(m,'note');pp=sub(nt,'pitch');ma=re.fullmatch(r'([A-G])([#b]?)(\d)',e['pitch']);sub(pp,'step',ma[1]);alt={'#':1,'b':-1,'':0}[ma[2]]
   if alt:sub(pp,'alter',alt)
   sub(pp,'octave',ma[3]);sub(nt,'duration',round(e['duration']*480));sub(nt,'voice',staff);sub(nt,'type',types[e['duration']])
   if e['duration'] in (1.5,3):sub(nt,'dot')
   if ma[2]=='b':sub(nt,'accidental','flat')
   elif ma[1] in ('F',) and alt==0:sub(nt,'accidental','natural')
   elif ma[2]=='#' and ma[1] not in ('F',):sub(nt,'accidental','sharp')
   sub(nt,'stem','up' if staff==1 and pm(e['pitch'])<71 else 'down');sub(nt,'staff',staff)
   if staff==2 and e['duration']==.5:sub(nt,'beam','begin' if i in (1,4) else 'end',number=1)
   elif e['duration']==.5:
    prev=i>0 and bar[key][i-1]['duration']==.5 and int((pos-.5)//2)==int(pos//2)
    nxt=i+1<len(bar[key]) and bar[key][i+1]['duration']==.5 and int((pos+.5)//2)==int(pos//2)
    if prev or nxt:sub(nt,'beam','continue' if prev and nxt else 'end' if prev else 'begin',number=1)
   if staff==1 and ((n%2==1 and i==0) or (n%2==0 and i==len(bar[key])-1)):
    ns=sub(nt,'notations');sub(ns,'slur',type='start' if n%2 else 'stop',number=1)
   pos+=e['duration']
 if n==24:sub(sub(m,'barline',location='right'),'bar-style','light-light')
X.indent(root);(O/'where_the_mileposts_turn.musicxml').write_bytes(b'<?xml version="1.0" encoding="UTF-8"?>\n'+X.tostring(root,encoding='utf-8'))
# Format 1, independent melody/bass/inner tracks and fixed metrical onsets.
def vlq(x):
 a=[x&127];x>>=7
 while x:a.insert(0,(x&127)|128);x>>=7
 return bytes(a)
length=24*1920
tracks={k:[] for k in ['conductor','melody','bass','inner']}
tracks['conductor']=[(0,b'\xff\x51\x03'+round(60000000/TEMPO).to_bytes(3,'big')),(0,b'\xff\x58\x04\x04\x02\x18\x08'),(0,b'\xff\x59\x02\x01\x00')]
for bar in bars:
 n=bar['number'];base=(n-1)*1920;dynamic=[0,1,3,1,1,0,2,-2,3,4,5,5,-1,0,1,-2,1,2,3,1,4,2,0,-3][n-1]
 t=base
 for i,e in enumerate(bar['melody']):
  dur=round(480*e['duration']);v=78+dynamic+(2 if t%1920==0 else 0)+(2 if pm(e['pitch'])>=81 else 0)-(3 if n%2==0 and i==len(bar['melody'])-1 else 0)
  gate=.93 if n%2==0 and i==len(bar['melody'])-1 else .98
  tracks['melody'] += [(t,bytes([0x90,pm(e['pitch']),v])),(t+int(dur*gate),bytes([0x80,pm(e['pitch']),0]))];t+=dur
 t=base
 for i,e in enumerate(bar['left']):
  role=e['role'];ch=1 if role=='bass' else 2;v=(62 if role=='bass' else 48)+dynamic+(2 if i in (2,5) else 0)
  tracks[role]+=[(t,bytes([0x90+ch,pm(e['pitch']),v])),(t+int(e['duration']*480*.88),bytes([0x80+ch,pm(e['pitch']),0]))]
  t+=int(e['duration']*480)
 # Half-bar pedal clears every bass attack. No pedal carries across the loop boundary.
 for role,ch in [('bass',1),('inner',2)]:
  for beat in (0,960):tracks[role]+=[(base+beat+10,bytes([0xb0+ch,64,80])),(base+beat+936,bytes([0xb0+ch,64,0]))]
def make_track(name,events):
 b=name.encode();out=vlq(0)+b'\xff\x03'+vlq(len(b))+b;last=0
 for t,e in sorted(events,key=lambda a:(a[0],0 if a[1][0]&0xf0==0x80 else 1)):out+=vlq(t-last)+e;last=t
 out+=vlq(length-last)+b'\xff\x2f\x00';return b'MTrk'+struct.pack('>I',len(out))+out
for role,ch in [('melody',0),('bass',1),('inner',2)]:tracks[role].append((0,bytes([0xc0+ch,0])))
mid=b'MThd'+struct.pack('>IHHH',6,1,4,480)+b''.join(make_track(k,v) for k,v in tracks.items())
(O/'where_the_mileposts_turn.mid').write_bytes(mid)
# Basic validation records, subsequently supplemented by independent review.
report={'title':TITLE,'bars':24,'beats_per_bar':4,'tempo':TEMPO,'duration_seconds':24*4*60/TEMPO,'musicxml_voices':2,'midi_note_tracks':3,'bar_sums_valid':True,'melody_range_midi':[min(pm(e['pitch']) for b in bars for e in b['melody']),max(pm(e['pitch']) for b in bars for e in b['melody'])],'left_range_midi':[min(pm(e['pitch']) for b in bars for e in b['left']),max(pm(e['pitch']) for b in bars for e in b['left'])],'audible_review_performed':False,'loop':'24 bars / 96 beats; last F#4 resolves upward to initial G4 over D7 -> G. No ritardando, tail, or extra cadence bars.'}
(O/'validation.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))
