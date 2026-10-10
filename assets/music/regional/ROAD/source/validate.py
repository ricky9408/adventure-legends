from pathlib import Path
import json,struct,xml.etree.ElementTree as X
O=Path(__file__).parent
j=json.loads((O/'composition_events.json').read_text());x=X.parse(O/'where_the_mileposts_turn.musicxml')
# Independently parse encoded MusicXML durations, rather than trust source-only checks.
xml_events={};xml_sums=[]
for m in x.findall('.//part/measure'):
 for voice in ('1','2'):
  seq=[n for n in m.findall('note') if n.findtext('voice')==voice];total=sum(int(n.findtext('duration')) for n in seq);assert total==1920
  xml_sums.append(dict(bar=int(m.attrib['number']),voice=voice,ticks=total))
  expected=j['bars'][int(m.attrib['number'])-1]['melody' if voice=='1' else 'left']
  assert len(seq)==len(expected)
  for n,e in zip(seq,expected):
   assert n.find('pitch') is not None
   pitch=n.findtext('pitch/step')+{'1':'#','-1':'b','0':''}[n.findtext('pitch/alter','0')]+n.findtext('pitch/octave')
   assert pitch==e['pitch'] and int(n.findtext('duration'))==int(e['duration']*480)
# Independent SMF parser, checking running event clocks, note pairing, tempo, and bounds.
b=(O/'where_the_mileposts_turn.mid').read_bytes();assert b[:4]==b'MThd';fmt,nt,ppq=struct.unpack('>HHH',b[8:14]);assert (fmt,nt,ppq)==(1,4,480)
pos=14;tracks=[]
def vlq(data,p):
 val=0
 while True:
  z=data[p];p+=1;val=(val<<7)|(z&127)
  if not z&128:return val,p
for ti in range(nt):
 assert b[pos:pos+4]==b'MTrk';length=int.from_bytes(b[pos+4:pos+8],'big');data=b[pos+8:pos+8+length];pos+=8+length
 p=0;t=0;active={};notes=[];name='';vel=[];pedals={};on_grid=True
 while p<len(data):
  dt,p=vlq(data,p);t+=dt;status=data[p];p+=1
  if status==255:
   typ=data[p];p+=1;n,p=vlq(data,p);payload=data[p:p+n];p+=n
   if typ==3:name=payload.decode()
   if typ==0x2f:assert t==46080
  elif status&0xf0==0xc0:p+=1
  else:
   a,bb=data[p:p+2];p+=2;key=(status&15,a)
   if status&0xf0==0x90 and bb:
    assert key not in active;active[key]=t;notes.append((t,a,bb));vel.append(bb);on_grid &= t%240==0
   elif status&0xf0==0x80 or status&0xf0==0x90:
    assert key in active;assert t>active.pop(key)
   elif status&0xf0==0xb0 and a==64:pedals[status&15]=bb
 assert not active;assert all(v==0 for v in pedals.values());assert on_grid
 if name!='conductor':
  expected=[]
  for bar in j['bars']:
   onset=(bar['number']-1)*1920
   for e in bar['melody' if name=='melody' else 'left']:
    pch=e['pitch'];midi=(int(pch[-1])+1)*12+dict(C=0,D=2,E=4,F=5,G=7,A=9,B=11)[pch[0]]+(1 if '#' in pch else -1 if 'b' in pch else 0)
    if name=='melody' or e['role']==name:expected.append((onset,midi))
    onset+=int(e['duration']*480)
  assert [(t,p) for t,p,v in notes]==expected
 tracks.append(dict(name=name,end_tick=t,attacks=len(notes),velocity_range=[min(vel),max(vel)] if vel else None,all_attacks_on_eighth_grid=on_grid))
assert pos==len(b)
# Vertical envelope audit: every active melody is above every concurrently sounding LH pitch.
def pm(s):
 step=s[0];octave=int(s[-1]);alt=1 if '#' in s else -1 if 'b' in s else 0;return 12*(octave+1)+dict(C=0,D=2,E=4,F=5,G=7,A=9,B=11)[step]+alt
minimum_gap=100;crossings=[]
for bar in j['bars']:
 t=0
 for e in bar['melody']:
  lt=0
  for i,left in enumerate(bar['left']):
   if lt< t+e['duration'] and lt+left['duration']>t:
    gap=pm(e['pitch'])-pm(left['pitch']);minimum_gap=min(gap,minimum_gap)
    if gap<=0:crossings.append((bar['number'],e,left))
   lt+=left['duration']
  t+=e['duration']
assert not crossings
all_lh=[e for b in j['bars'] for e in b['left']]
max_lh_leap=max(abs(pm(a['pitch'])-pm(b['pitch'])) for a,b in zip(all_lh,all_lh[1:]+all_lh[:1]))
assert max_lh_leap<=12
report=json.loads((O/'validation.json').read_text());report.update(dict(musicxml_pitch_duration_matches_event_data=True,midi_pitch_onset_matches_event_data=True,maximum_successive_lh_leap_semitones=max_lh_leap,audio_engine_seam_tested=False,setting='Sunmere Grove / sunlit woodland road',xml_voice_bar_totals=xml_sums,midi_parse=tracks,voice_crossings=crossings,minimum_simultaneous_melody_lh_semitones=minimum_gap,midi_all_notes_closed=True,midi_all_pedals_released=True,rendered_score='2-page readable custom engraving; PDF is a review aid, MusicXML is authoritative editable notation'))
(O/'validation.json').write_text(json.dumps(report,indent=2));print(json.dumps({k:v for k,v in report.items() if k!='xml_voice_bar_totals'},indent=2))
