from pathlib import Path
import json,re,struct,sys,math,xml.etree.ElementTree as X
O=Path(sys.argv[1]);d=json.loads((O/'composition_events.json').read_text());roles=['melody','inner','bass'];beats=int(d['meter'].split('/')[0]);nbar=len(d['bars']);slug=d['slug'];tempo=d['tempo'];length=nbar*beats*480

def pm(p):
 m=re.fullmatch(r'([A-G])([#b]?)(\d)',p);return 12*(int(m[3])+1)+dict(C=0,D=2,E=4,F=5,G=7,A=9,B=11)[m[1]]+{'':0,'#':1,'b':-1}[m[2]]
def sub(a,t,s=None,**kw):
 b=X.SubElement(a,t,{k:str(v) for k,v in kw.items()})
 if s is not None:b.text=str(s)
 return b
root=X.Element('score-partwise',version='4.0');sub(sub(root,'work'),'work-title',d['title']);sub(sub(root,'identification'),'creator','Original composition for Adventure Legends',type='composer');pl=sub(root,'part-list')
keyalts={c:1 for c in 'FCGDAEB'[:d['fifths']]} if d['fifths']>0 else {c:-1 for c in 'BEADGCF'[:-d['fifths']]}
for i,r in enumerate(roles,1):
 sp=sub(pl,'score-part',id=f'P{i}');sub(sp,'part-name',r.title());mi=sub(sp,'midi-instrument',id=f'I{i}');sub(mi,'midi-channel',i);sub(mi,'midi-program',1)
for ri,r in enumerate(roles,1):
 part=sub(root,'part',id=f'P{ri}')
 for b in d['bars']:
  n=b['number'];m=sub(part,'measure',number=n)
  if n==1:
   a=sub(m,'attributes');sub(a,'divisions',480);sub(sub(a,'key'),'fifths',d['fifths']);t=sub(a,'time');sub(t,'beats',beats);sub(t,'beat-type',4);c=sub(a,'clef');sub(c,'sign','F' if r=='bass' else 'G');sub(c,'line',4 if r=='bass' else 2)
   if ri==1:
    dr=sub(m,'direction',placement='above');dt=sub(dr,'direction-type');sub(dt,'words','Steady pulse; melody mp, inner pp, bass p; no rubato');met=sub(dt,'metronome');sub(met,'beat-unit','quarter');sub(met,'per-minute',tempo);sub(dr,'sound',tempo=tempo)
  if ri==1:
   sub(sub(sub(m,'direction',placement='above'),'direction-type'),'words',b['chord'])
   if str(n) in d['sections']:sub(sub(sub(m,'direction',placement='above'),'direction-type'),'rehearsal',d['sections'][str(n)])
   if n==nbar:sub(sub(sub(m,'direction',placement='above'),'direction-type'),'words','Loop to bar 1 without pause')
  state={}
  for e in b[r]:
   nt=sub(m,'note');p=e['pitch'];du=e['duration']
   if p=='R':sub(nt,'rest')
   else:
    ma=re.fullmatch(r'([A-G])([#b]?)(\d)',p);pp=sub(nt,'pitch');sub(pp,'step',ma[1]);alt={'':0,'#':1,'b':-1}[ma[2]]
    if alt:sub(pp,'alter',alt)
    sub(pp,'octave',ma[3])
   sub(nt,'duration',int(du*480));sub(nt,'type',{.5:'eighth',1:'quarter',1.5:'quarter',2:'half',3:'half',4:'whole'}[du])
   if du in (1.5,3):sub(nt,'dot')
   if p!='R':
    k=(ma[1],ma[3]);old=state.get(k,keyalts.get(ma[1],0))
    if alt!=old:sub(nt,'accidental',{0:'natural',1:'sharp',-1:'flat'}[alt])
    state[k]=alt
  if n==nbar:sub(sub(m,'barline',location='right'),'bar-style','light-light')
X.indent(root);(O/f'{slug}.musicxml').write_bytes(b'<?xml version="1.0" encoding="UTF-8"?>\n'+X.tostring(root,encoding='utf-8'))
def vlq(x):
 a=[x&127];x>>=7
 while x:a.insert(0,(x&127)|128);x>>=7
 return bytes(a)
def tr(name,events):
 bb=name.encode();out=b'\x00\xff\x03'+vlq(len(bb))+bb;last=0
 for t,e in sorted(events,key=lambda a:(a[0],a[1][0]&0xf0!=0x80)):out+=vlq(t-last)+e;last=t
 out+=vlq(length-last)+b'\xff\x2f\x00';return b'MTrk'+struct.pack('>I',len(out))+out
tracks={'conductor':[(0,b'\xff\x51\x03'+round(60000000/tempo).to_bytes(3,'big')),(0,bytes([255,88,4,beats,2,24,8])),(0,bytes([255,89,2,d['fifths']%256,1]))]};expected={r:[] for r in roles}
for ch,r in enumerate(roles):
 ev=[(0,bytes([0xc0+ch,0]))]
 for b in d['bars']:
  t=0
  for e in b[r]:
   assert e['onset']==t;t+=e['duration']
   if e['pitch']=='R':continue
   on=int(((b['number']-1)*beats+e['onset'])*480);du=int(e['duration']*480);vel={'melody':76,'inner':46,'bass':57}[r];expected[r].append((on,pm(e['pitch']),du))
   ev.extend([(on,bytes([0x90+ch,pm(e['pitch']),vel])),(on+du-14,bytes([0x80+ch,pm(e['pitch']),0]))])
  assert t==beats
 tracks[r]=ev
for r in roles:(O/f'{slug}_{r}.mid').write_bytes(b'MThd'+struct.pack('>IHHH',6,1,2,480)+tr('conductor',tracks['conductor'])+tr(r,tracks[r]))
(O/f'{slug}.mid').write_bytes(b'MThd'+struct.pack('>IHHH',6,1,4,480)+b''.join(tr(k,v) for k,v in tracks.items()))
# Read back XML and binary MIDI, not merely generation arrays.
x=X.parse(O/f'{slug}.musicxml')
for r,p in zip(roles,x.findall('part')):
 actual=[];base=0
 for m in p.findall('measure'):
  t=0
  for no in m.findall('note'):
   du=int(no.findtext('duration'));pi=no.find('pitch')
   if pi is not None:actual.append((base+t,(int(pi.findtext('octave'))+1)*12+dict(C=0,D=2,E=4,F=5,G=7,A=9,B=11)[pi.findtext('step')]+int(pi.findtext('alter','0')),du))
   t+=du
  assert t==beats*480;base+=t
 assert actual==expected[r]
def vl(buf,i):
 val=0
 while True:
  a=buf[i];i+=1;val=(val<<7)|(a&127)
  if a<128:return val,i
buf=(O/f'{slug}.mid').read_bytes();pos=14;decoded={};eots=[]
for ti in range(4):
 assert buf[pos:pos+4]==b'MTrk';sz=int.from_bytes(buf[pos+4:pos+8],'big');track=buf[pos+8:pos+8+sz];pos+=8+sz;i=t=0;active={};notes=[];name=''
 while i<len(track):
  dt,i=vl(track,i);t+=dt;st=track[i];i+=1
  if st==255:
   ty=track[i];i+=1;sz,i=vl(track,i);val=track[i:i+sz];i+=sz
   if ty==3:name=val.decode()
   if ty==47:eots.append(t)
   continue
  op=st&240
  if op==192:i+=1;continue
  p,v=track[i:i+2];i+=2
  if op==144:assert not active;active[p]=t
  elif op==128:notes.append((active.pop(p),p,t))
  else:raise AssertionError(st)
 assert not active;decoded[name]=[(a,p,z-a) for a,p,z in notes]
for r in roles:assert decoded[r]==[(a,p,z-14) for a,p,z in expected[r]]
assert eots==[length]*4
vertical=[]
for b in d['bars']:
 for t in sorted({e['onset'] for r in roles for e in b[r]}):
  pp={r:next(e['pitch'] for e in b[r] if e['onset']<=t<e['onset']+e['duration']) for r in roles};pp={r:p for r,p in pp.items() if p!='R'}
  vertical.append(dict(bar=b['number'],beat=t,pitches=pp,interval_classes={a+'/'+z:(pm(pp[a])-pm(pp[z]))%12 for a,z in [('melody','inner'),('melody','bass'),('inner','bass')] if a in pp and z in pp}))
(O/'vertical_interval_audit.json').write_text(json.dumps(vertical,indent=2))
report=dict(title=d['title'],bars=nbar,meter=d['meter'],tempo=tempo,duration_seconds=nbar*beats*60/tempo,xml='All pitches, onsets, durations match event data',midi='All four binary tracks parsed; notes match events; 14-tick release gap',end_tick=length,maximum_polyphony=3,pedal_events=0,voice_crossings=sum(pm(v['pitches'][a])<=pm(v['pitches'][b]) for v in vertical for a,b in [('melody','inner'),('inner','bass')] if a in v['pitches'] and b in v['pitches']),ranges={r:[min(p for _,p,_ in expected[r]),max(p for _,p,_ in expected[r])] for r in roles},audible_review_performed=False,visual_review='Pending PNG inspection',independent_review='See INDEPENDENT-MUSIC-REVIEW.md')
for r in roles:
 actual=(O/f'{slug}_{r}.mid').read_bytes();assert actual[:14]==b'MThd'+struct.pack('>IHHH',6,1,2,480);assert actual[14:]==tr('conductor',tracks['conductor'])+tr(r,tracks[r])
report['individual_voice_midi']='All three files have valid two-track headers and byte-identical conductor and voice tracks to checked master'
(O/'validation.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))
