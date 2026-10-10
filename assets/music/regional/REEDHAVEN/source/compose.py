from pathlib import Path
import re,json,struct,xml.etree.ElementTree as X
O=Path(__file__).parent
TITLE='Where the Reeds Turn';TEMPO=88
mel=[
'B4:1 D5:.5 E5:.5 D5:1',
'G5:1 E5:.5 D5:.5 B4:.5 R:.5',
'C5:1 B4:.5 A4:.5 E5:1',
'D5:1 B4:1 A4:.5 R:.5',
'B4:.5 D5:.5 E5:1 G5:1',
'F#5:1 E5:.5 D5:.5 A4:.5 R:.5',
'C5:1 E5:.5 D5:.5 B4:1',
'A4:1 C5:1 D5:.5 R:.5',
'G5:1 F#5:.5 E5:.5 B4:1',
'E5:1 D5:.5 C5:.5 A4:.5 R:.5',
'F#5:1 E5:.5 D5:.5 C5:1',
'B4:1 A4:.5 G4:.5 B4:.5 R:.5',
'C5:1 D5:.5 E5:.5 F#5:1',
'E5:1 D5:.5 C5:.5 B4:.5 R:.5',
'A4:.5 B4:.5 C5:1 E5:1',
'D5:1 C5:.5 B4:.5 A4:.5 R:.5',
'B4:1 D5:.5 E5:.5 D5:1',
'G5:1 E5:.5 D5:.5 B4:.5 R:.5',
'C5:1 E5:.5 D5:.5 A4:1',
'B4:1 A4:.5 G4:.5 D5:.5 R:.5',
'E5:1 G5:.5 F#5:.5 E5:1',
'D5:1 B4:.5 A4:.5 G4:.5 R:.5',
'C5:1 E5:.5 D5:.5 B4:1',
'A4:1 F#4:.5 A4:.5 D5:.5 R:.5']
inner=[
'G3:1 B3:.5 D4:.5 B3:1',
'G3:1 B3:1 D4:.5 B3:.5',
'A3:1 C4:.5 E4:.5 C4:1',
'A3:1 C4:1 F#4:.5 E4:.5',
'G3:1 B3:.5 E4:.5 B3:1',
'A3:1 D4:1 F#4:.5 D4:.5',
'G3:1 C4:.5 E4:.5 G4:1',
'A3:1 C4:1 F#4:.5 A3:.5',
'G3:1 B3:.5 E4:.5 G4:1',
'A3:1 C4:1 E4:.5 C4:.5',
'A3:1 D4:.5 F#4:.5 A4:1',
'G3:1 B3:1 D4:.5 B3:.5',
'G3:1 C4:.5 E4:.5 C4:1',
'G3:1 C4:1 E4:.5 G4:.5',
'A3:1 C4:.5 E4:.5 C4:1',
'A3:1 C4:1 F#4:.5 E4:.5',
'G3:1 B3:.5 D4:.5 B3:1',
'G3:1 B3:1 D4:.5 G4:.5',
'A3:1 C4:.5 E4:.5 C4:1',
'G3:1 B3:1 D4:.5 B3:.5',
'G3:1 C4:.5 E4:.5 C4:1',
'G3:1 B3:1 D4:.5 B3:.5',
'A3:1 C4:.5 E4:.5 C4:1',
'A3:1 C4:1 F#4:.5 A3:.5']
bass=['G2:3','B2:3','A2:3','D3:2 C3:1','E3:3','F#2:3','C3:3','D3:3','E3:3','C3:3','D3:3','B2:3','C3:3','E3:3','A2:3','D3:2 C3:1','G2:3','B2:3','A2:3','B2:3','C3:3','B2:3','A2:3','D3:3']
chords=['G(add6)','G/B','Am','D7','Em7','D/F#','Cmaj7','D7','Em','Am/C','D7','G/B','C(add#11)','Cmaj7/E','Am(add9)','D7','G(add6)','G/B','Am','G/B','C(add#11)','G/B','Am(add9)','D7']
def pm(p):
 m=re.fullmatch(r'([A-G])([#b]?)(\d)',p);return 12*(int(m[3])+1)+dict(C=0,D=2,E=4,F=5,G=7,A=9,B=11)[m[1]]+{'':0,'#':1,'b':-1}[m[2]]
def parse(s):
 es=[];t=0
 for x in s.split():
  p,d=x.split(':');d=float(d);es.append(dict(pitch=p,duration=d,onset=t));t+=d
 assert t==3
 return es
bars=[dict(number=i+1,chord=chords[i],melody=parse(mel[i]),inner=parse(inner[i]),bass=parse(bass[i])) for i in range(24)]
data=dict(title=TITLE,location='Reedhaven (room16)',tempo=TEMPO,key='G major',meter='3/4',form='A 1–8; B 9–16; A′ 17–24',bars=bars)
(O/'composition_events.json').write_text(json.dumps(data,indent=2))
def sub(a,t,s=None,**attrs):
 b=X.SubElement(a,t,{k:str(v) for k,v in attrs.items()})
 if s is not None:b.text=str(s)
 return b
root=X.Element('score-partwise',version='4.0');sub(sub(root,'work'),'work-title',TITLE)
sub(sub(root,'identification'),'creator','Original music for Adventure Legends',type='composer');pl=sub(root,'part-list')
for j,(role,label) in enumerate([('melody','Singing lead'),('inner','Plucked counterline'),('bass','Rounded bass')],1):
 sp=sub(pl,'score-part',id=f'P{j}');sub(sp,'part-name',label);sub(sp,'part-abbreviation',label.split()[0]);si=sub(sp,'score-instrument',id=f'I{j}');sub(si,'instrument-name','Acoustic Grand Piano');mi=sub(sp,'midi-instrument',id=f'I{j}');sub(mi,'midi-channel',j);sub(mi,'midi-program',1)
for j,role in enumerate(['melody','inner','bass'],1):
 p=sub(root,'part',id=f'P{j}')
 for b in bars:
  n=b['number'];m=sub(p,'measure',number=n)
  if n==1:
   a=sub(m,'attributes');sub(a,'divisions',480);sub(sub(a,'key'),'fifths',1);t=sub(a,'time');sub(t,'beats',3);sub(t,'beat-type',4);c=sub(a,'clef');sub(c,'sign','F' if role=='bass' else 'G');sub(c,'line',4 if role=='bass' else 2)
   d=sub(m,'direction');sub(sub(d,'direction-type'),'words','Gently flowing; quarter = 88. No swing.' if j==1 else ('Light, even, detached' if j==2 else 'Warm, sustained; no pedal'));sub(d,'sound',tempo=TEMPO)
  if j==1:
   d=sub(m,'direction');sub(sub(d,'direction-type'),'words',b['chord'])
   if n in (1,9,17):sub(sub(sub(m,'direction'),'direction-type'),'rehearsal',{1:'A',9:'B',17:'A′'}[n])
   if n==24:sub(sub(sub(m,'direction'),'direction-type'),'words','Loop directly to 1, without pause')
  for i,e in enumerate(b[role]):
   nt=sub(m,'note');pitch=e['pitch'];dur=e['duration']
   if pitch=='R':sub(nt,'rest')
   else:
    ma=re.fullmatch(r'([A-G])([#b]?)(\d)',pitch);pp=sub(nt,'pitch');sub(pp,'step',ma[1]);alt={'':0,'#':1,'b':-1}[ma[2]]
    if alt:sub(pp,'alter',alt)
    sub(pp,'octave',ma[3])
   sub(nt,'duration',round(dur*480));sub(nt,'voice',1);sub(nt,'type',{.5:'eighth',1:'quarter',2:'half',3:'half'}[dur])
   if dur==3:sub(nt,'dot')
   if pitch!='R' and dur==.5:
    prev=i>0 and b[role][i-1]['duration']==.5 and b[role][i-1]['pitch']!='R' and int(b[role][i-1]['onset'])==int(e['onset'])
    nxt=i+1<len(b[role]) and b[role][i+1]['duration']==.5 and b[role][i+1]['pitch']!='R' and int(b[role][i+1]['onset'])==int(e['onset'])
    if prev or nxt:sub(nt,'beam','end' if prev else 'begin',number=1)
  if n==24:sub(sub(m,'barline',location='right'),'bar-style','light-light')
X.indent(root);(O/'where_the_reeds_turn.musicxml').write_bytes(b'<?xml version="1.0" encoding="UTF-8"?>\n'+X.tostring(root,encoding='utf-8'))
def vlq(x):
 a=[x&127];x>>=7
 while x:a.insert(0,(x&127)|128);x>>=7
 return bytes(a)
length=24*1440
tracks={'conductor':[(0,b'\xff\x51\x03'+round(60000000/TEMPO).to_bytes(3,'big')),(0,b'\xff\x58\x04\x03\x02\x18\x08'),(0,b'\xff\x59\x02\x01\x00')]}
for ch,role in enumerate(['melody','inner','bass']):
 events=[(0,bytes([0xc0+ch,0]))]
 for b in bars:
  for e in b[role]:
   if e['pitch']=='R':continue
   t=round(((b['number']-1)*3+e['onset'])*480);dur=round(e['duration']*480)
   vel={'melody':79,'inner':49,'bass':61}[role]+(3 if b['number'] in range(9,14) else 0)+(2 if e['onset']==0 else 0)
   gate={'melody':.97,'inner':.72,'bass':.96}[role]
   events.extend([(t,bytes([0x90+ch,pm(e['pitch']),vel])),(t+round(dur*gate),bytes([0x80+ch,pm(e['pitch']),0]))])
 tracks[role]=events

def track(name,es):
 b=name.encode();out=b'\x00\xff\x03'+vlq(len(b))+b;last=0
 for t,e in sorted(es,key=lambda x:(x[0],0 if x[1][0]&0xf0==0x80 else 1)):out+=vlq(t-last)+e;last=t
 out+=vlq(length-last)+b'\xff\x2f\x00';return b'MTrk'+struct.pack('>I',len(out))+out
(O/'where_the_reeds_turn.mid').write_bytes(b'MThd'+struct.pack('>IHHH',6,1,4,480)+b''.join(track(k,v) for k,v in tracks.items()))
print('Created 24 bars; duration',72*60/TEMPO)
