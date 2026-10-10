from pathlib import Path
import re,json,struct,xml.etree.ElementTree as X
O=Path(__file__).parent;TITLE='Under the Rootbound Arch';TEMPO=78;SLUG='under_the_rootbound_arch'
mel=[
'D5:1.5 A4:.5 E5:1','F5:2 E5:1','C5:1 A4:1 G4:1','A4:2 C5:1',
'D5:1.5 B4:.5 G4:1','A4:1 D5:1 F5:1','E5:1 G5:1 E5:1','C#5:2 R:1',
'R:.5 D5:1.5 A4:1','C5:1.5 A4:.5 F5:1','E5:1 D5:1 Bb4:1','C#5:1 E5:1 G5:1',
'F5:1.5 E5:.5 D5:1','G5:1 E5:1 Bb4:1','D5:1 C#5:1 B4:.5 A4:.5','E5:2 C#5:1',
'D5:1.5 A4:.5 E5:1','F5:2 G5:.5 E5:.5','C5:1 A4:1 G4:1','A4:2 C5:1',
'D5:1 F5:1 A5:1','G5:1.5 F5:.5 E5:1','D5:1 C#5:1 A4:1','E5:1 G5:1 C#5:1']
inner=[
'R:.5 A3:.5 D4:1 A3:1','R:.5 G3:.5 C4:1 G3:1','R:.5 A3:.5 E4:1 A3:1','R:.5 G3:.5 C4:1 E4:1',
'R:.5 G3:.5 D4:1 E4:1','R:.5 F3:.5 A3:1 D4:1','R:.5 Bb3:.5 D4:1 Bb3:1','R:.5 G3:.5 E4:1 G3:1',
'R:.5 A3:.5 F4:1 D4:1','R:.5 C4:.5 F4:1 C4:1','R:.5 Bb3:.5 D4:1 G3:1','R:.5 G3:.5 A3:1 C#4:1',
'R:.5 A3:.5 D4:1 A3:1','R:.5 Bb3:.5 D4:1 G3:1','R:.5 G3:.5 E4:1 G3:1','R:.5 G3:.5 A3:1 G3:1',
'R:.5 A3:.5 D4:1 A3:1','R:.5 G3:.5 C4:1 G3:1','R:.5 A3:.5 E4:1 A3:1','R:.5 G3:.5 C4:1 E4:1',
'R:.5 Bb3:.5 D4:1 F4:1','R:.5 Bb3:.5 D4:1 G3:1','R:.5 G3:.5 E4:1 G3:1','R:.5 G3:.5 E4:1 G3:1']
bass=['D3:3','E3:3','F3:3','A2:3','B2:3','A2:3','E3:3','A2:3','Bb2:3','A2:3','G2:3','A2:3','F3:3','E3:3','A2:3','A2:3','D3:3','E3:3','F3:3','A2:3','Bb2:3','G2:3','A2:3','A2:3']
chords=['Dm(add9)','C/E (4-3)','Fmaj7','Am7','G6/B','Dm/A','Em7(b5)','A7','Bbmaj7','F/A','Gm6','A7','Dm/F','Em7(b5)','A7sus4 > A7','A7','Dm(add9)','C/E (4-3)','Fmaj7','Am7','Bbmaj7','Gm6','A7sus4 > A7','A7']
def pm(p):
 m=re.fullmatch(r'([A-G])([#b]?)(\d)',p);return 12*(int(m[3])+1)+dict(C=0,D=2,E=4,F=5,G=7,A=9,B=11)[m[1]]+{'':0,'#':1,'b':-1}[m[2]]
def parse(s):
 out=[];beat=0
 for t in s.split():
  p,d=t.split(':');d=float(d);out.append(dict(pitch=p,duration=d,onset=beat));beat+=d
 assert beat==3
 return out
roles=['melody','inner','bass'];bars=[]
for i in range(24):bars.append(dict(number=i+1,chord=chords[i],**{r:parse(a[i]) for r,a in zip(roles,[mel,inner,bass])}))
data=dict(title=TITLE,tempo=TEMPO,meter='3/4',key='D minor with Dorian mixture',bars=bars)
(O/'composition_events.json').write_text(json.dumps(data,indent=2))
def sub(a,t,s=None,**kw):
 b=X.SubElement(a,t,{k:str(v) for k,v in kw.items()})
 if s is not None:b.text=str(s)
 return b
root=X.Element('score-partwise',version='4.0');sub(sub(root,'work'),'work-title',TITLE);sub(sub(root,'identification'),'creator','Original composition for Adventure Legends',type='composer');pl=sub(root,'part-list')
for i,r in enumerate(roles,1):
 sp=sub(pl,'score-part',id=f'P{i}');sub(sp,'part-name',r.title());sub(sp,'part-abbreviation',r[0].upper());si=sub(sp,'score-instrument',id=f'I{i}');sub(si,'instrument-name',r.title());mi=sub(sp,'midi-instrument',id=f'I{i}');sub(mi,'midi-channel',i);sub(mi,'midi-program',1)
for ri,r in enumerate(roles,1):
 part=sub(root,'part',id=f'P{ri}')
 for b in bars:
  n=b['number'];m=sub(part,'measure',number=n)
  if n==1:
   a=sub(m,'attributes');sub(a,'divisions',480);sub(sub(a,'key'),'fifths',-1);t=sub(a,'time');sub(t,'beats',3);sub(t,'beat-type',4);c=sub(a,'clef');sub(c,'sign','F' if r=='bass' else 'G');sub(c,'line',4 if r=='bass' else 2)
   if ri==1:
    d=sub(m,'direction',placement='above');dt=sub(d,'direction-type');sub(dt,'words','Reverent, quietly moving; three monophonic voices');met=sub(dt,'metronome');sub(met,'beat-unit','quarter');sub(met,'per-minute',TEMPO);sub(d,'sound',tempo=TEMPO)
  if ri==1:
   d=sub(m,'direction',placement='above');sub(sub(d,'direction-type'),'words',b['chord'])
   if n in (1,9,17):sub(sub(sub(m,'direction',placement='above'),'direction-type'),'rehearsal',{1:'A - Threshold',9:'B - Forest heart',17:'A\u2032 - Remembered light'}[n])
   if n==24:sub(sub(sub(m,'direction',placement='above'),'direction-type'),'words','Loop directly to 1; no ritardando')
  state={}
  for e in b[r]:
   nt=sub(m,'note');p=e['pitch'];dur=e['duration']
   if p=='R':sub(nt,'rest')
   else:
    ma=re.fullmatch(r'([A-G])([#b]?)(\d)',p);pp=sub(nt,'pitch');sub(pp,'step',ma[1]);alt={'':0,'#':1,'b':-1}[ma[2]]
    if alt:sub(pp,'alter',alt)
    sub(pp,'octave',ma[3])
   sub(nt,'duration',int(dur*480));sub(nt,'type',{.5:'eighth',1:'quarter',1.5:'quarter',2:'half',3:'half'}[dur])
   if dur in (1.5,3):sub(nt,'dot')
   if p!='R':
    k=(ma[1],ma[3]);old=state.get(k,-1 if ma[1]=='B' else 0)
    if alt!=old:sub(nt,'accidental',{0:'natural',1:'sharp',-1:'flat'}[alt])
    state[k]=alt
  if n==24:sub(sub(m,'barline',location='right'),'bar-style','light-light')
X.indent(root);(O/f'{SLUG}.musicxml').write_bytes(b'<?xml version="1.0" encoding="UTF-8"?>\n'+X.tostring(root,encoding='utf-8'))
def vlq(x):
 a=[x&127];x>>=7
 while x:a.insert(0,(x&127)|128);x>>=7
 return bytes(a)
length=24*1440;tracks={'conductor':[(0,b'\xff\x51\x03'+round(60000000/TEMPO).to_bytes(3,'big')),(0,b'\xff\x58\x04\x03\x02\x18\x08'),(0,b'\xff\x59\x02\xff\x01')]}
for ch,r in enumerate(roles):
 ev=[(0,bytes([0xc0+ch,0]))]
 for b in bars:
  for e in b[r]:
   if e['pitch']=='R':continue
   onset=int(((b['number']-1)*3+e['onset'])*480);dur=int(e['duration']*480);vel={'melody':74,'inner':46,'bass':57}[r]+(3 if 9<=b['number']<=14 else 0)
   ev.extend([(onset,bytes([0x90+ch,pm(e['pitch']),vel])),(onset+dur-14,bytes([0x80+ch,pm(e['pitch']),0]))])
 tracks[r]=ev
 def tr(name,events):
  bb=name.encode();out=b'\x00\xff\x03'+vlq(len(bb))+bb;last=0
  for t,e in sorted(events,key=lambda a:(a[0],a[1][0]&0xf0!=0x80)):out+=vlq(t-last)+e;last=t
  out+=vlq(length-last)+b'\xff\x2f\x00';return b'MTrk'+struct.pack('>I',len(out))+out
for r in roles:
 (O/f'{SLUG}_{r}.mid').write_bytes(b'MThd'+struct.pack('>IHHH',6,1,2,480)+tr('conductor',tracks['conductor'])+tr(r,tracks[r]))
(O/f'{SLUG}.mid').write_bytes(b'MThd'+struct.pack('>IHHH',6,1,4,480)+b''.join(tr(k,v) for k,v in tracks.items()))
print('Wrote score, events, 4-track MIDI and individual voice MIDI files')
