from pathlib import Path
import json,re,math
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
O=Path(__file__).parent;d=json.loads((O/'composition_events.json').read_text())
pdfmetrics.registerFont(TTFont('Music','/usr/share/fonts/truetype/noto/NotoMusic-Regular.ttf'))
W,H=A4;c=canvas.Canvas(str(O/'where_the_mileposts_turn.pdf'),pagesize=A4);c.setTitle(d['title']);c.setAuthor('Original composition for Adventure Legends')
space=5.2;half=space/2;left=36;right=W-32;sigw=60;barw=(right-left-sigw)/4
# Conventional letter position; bottom treble E4, bottom bass G2.
def pitchpos(p,staff):
 m=re.fullmatch(r'([A-G])([#b]?)(\d)',p);di=int(m[3])*7+'CDEFGAB'.index(m[1]);base=4*7+2 if staff==1 else 2*7+4;return di-base
def note(x,y,dur,stem='down',flag=False):
 c.saveState();c.translate(x,y);c.rotate(18);c.setLineWidth(.75)
 if dur>=2:c.setFillColorRGB(1,1,1)
 else:c.setFillColorRGB(0,0,0)
 c.ellipse(-3.2,-2.0,3.2,2.0,fill=1,stroke=1);c.restoreState()
 sx=x-2.9 if stem=='down' else x+2.9;sy=y-25 if stem=='down' else y+25
 c.setLineWidth(.65);c.line(sx,y,sx,sy)
 if dur in (1.5,3):c.circle(x+6,y+1,0.8,fill=1,stroke=0)
 if flag:
  p=c.beginPath();p.moveTo(sx,sy)
  if stem=='down':p.curveTo(sx-9,sy+3,sx-7,sy+12,sx-3,sy+14)
  else:p.curveTo(sx+9,sy-3,sx+7,sy-12,sx+3,sy-14)
  c.setLineWidth(1.7);c.drawPath(p)
 return sx,sy
for page in range(2):
 c.setFillColorRGB(.1,.14,.16);c.setFont('Helvetica-Bold',18);c.drawString(left,H-42,d['title'])
 c.setFont('Helvetica',9);c.drawString(left,H-59,'Original road / overworld theme for Adventure Legends · Piano · G major · 4/4')
 c.setFont('Helvetica-Oblique',10);c.drawString(left,H-78,'Allegretto, traveling  ·  quarter = 112  ·  Keep the melody singing and the inner notes soft')
 c.setFillColorRGB(0,0,0)
 for system in range(3):
  start=page*12+system*4;top=H-160-system*214;bottom=top-70
  # clef glyphs grounded using the G4 and F3 anchor lines.
  for staff,y0 in [(1,top),(2,bottom)]:
   c.setLineWidth(.42)
   for k in range(5):c.line(left,y0+k*space,right,y0+k*space)
   c.setFont('Music',30);c.drawString(left+2,y0+(-2 if staff==1 else 2),'𝄞' if staff==1 else '𝄢')
   c.setFont('Music',13)
   for j,pos in enumerate([8] if staff==1 else [6]):c.drawString(left+24+j*8,y0+pos*half-5,'♯')
  if page==0 and system==0:
   for y0 in (top,bottom):
    c.setFont('Times-Bold',13);c.drawString(left+45,y0+11,'4');c.drawString(left+45,y0,'4')
  c.setLineWidth(.8);c.line(left, bottom,left,top+4*space)
  # Left brace drawn with simple continuous curves.
  pp=c.beginPath();pp.moveTo(left-4,top+4*space);pp.curveTo(left-12,top+4*space,left-3,top-16,left-10,(top+bottom+4*space)/2);pp.curveTo(left-3,bottom+36,left-12,bottom,left-4,bottom);c.drawPath(pp)
  for k in range(4):
   b=d['bars'][start+k];n=b['number'];x0=left+sigw+k*barw
   c.setFont('Helvetica',7);c.drawString(x0+2,top+42,str(n))
   c.setFont('Helvetica',9);c.drawString(x0+10,top+31,b['chord'])
   if n in (1,9,17):
    c.setLineWidth(.6);c.rect(x0-2,top+54,19,17);c.setFont('Helvetica-Bold',11);c.drawCentredString(x0+7,top+58,{1:'A',9:'B',17:"A'"}[n])
   if n in (1,9,13,17,21,24):
    c.setFont('Times-BoldItalic',12);c.drawString(x0+9,top-30,{1:'mp',9:'mf',13:'mp',17:'mp',21:'mf',24:'mp'}[n])
   for staff,key,y0 in [(1,'melody',top),(2,'left',bottom)]:
    pos=0;events=[];acc={'F':1};state={}
    for e in b[key]:
     p=e['pitch'];dur=e['duration'];di=pitchpos(p,staff);y=y0+di*half;x=x0+13+pos*(barw-20)/4
     ma=re.fullmatch(r'([A-G])([#b]?)(\d)',p);a={'#':1,'b':-1,'':0}[ma[2]];keyp=(ma[1],ma[3]);old=state.get(keyp,acc.get(ma[1],0))
     if a!=old:
      c.setFont('Music',11);c.drawString(x-10,y-3,{1:'♯',-1:'♭',0:'♮'}[a]);state[keyp]=a
     if di<0:
      for z in range(-2,di-1,-2):c.setLineWidth(.6);c.line(x-5,y0+z*half,x+5,y0+z*half)
     if di>8:
      for z in range(10,di+1,2):c.setLineWidth(.6);c.line(x-5,y0+z*half,x+5,y0+z*half)
     events.append(dict(x=x,y=y,dur=dur,pos=pos,stem='up' if staff==1 and di<4 else 'down'))
     pos+=dur
    # Beam groups are bounded by half-bar beats; mixed durations cannot be bridged.
    groups=[];run=[]
    for ix,e in enumerate(events):
     if e['dur']==.5:
      if run and int(e['pos']//2)!=int(events[run[-1]]['pos']//2):groups.append(run);run=[]
      run.append(ix)
     else:
      if run:groups.append(run);run=[]
    if run:groups.append(run)
    beamed={i for g in groups if len(g)>1 for i in g}
    for i,e in enumerate(events):
     if i in beamed:e['stem']='down' # Ensures each beam group has a consistent direction.
     e['end']=note(e['x'],e['y'],e['dur'],e['stem'],e['dur']==.5 and i not in beamed)
    for g in groups:
     if len(g)<2:continue
     ey=min(events[i]['y'] for i in g)-25
     c.setLineWidth(.65)
     for i in g:
      e=events[i];c.line(e['end'][0],e['y'],e['end'][0],ey)
     c.setLineWidth(2.7);c.line(events[g[0]]['end'][0],ey,events[g[-1]]['end'][0],ey)
   c.setLineWidth(.55);c.line(x0+barw,bottom,x0+barw,top+4*space)
   if n==24:c.line(x0+barw-3,bottom,x0+barw-3,top+4*space)
  # Phrase arcs: four-bar systems hold two complete two-bar phrases.
  for ph in (0,2):
   xa=left+sigw+ph*barw+14;xb=left+sigw+(ph+2)*barw-13
   yy=top+49;p=c.beginPath();p.moveTo(xa,yy);p.curveTo(xa+35,yy+15,xb-35,yy+15,xb,yy);c.setLineWidth(.65);c.drawPath(p)
  if start==0:
   c.setFont('Helvetica-Oblique',8);c.drawString(left+sigw,bottom-47,'Light pedal, cleared every half bar; no rubato between tracks.')
  if start==20:
   c.setFont('Helvetica-Oblique',8);c.drawString(left+sigw,bottom-47,'Loop: bar 24 leads directly into bar 1. Keep the pulse; no closing ritardando.')
 c.setFont('Helvetica',8);c.setFillColorRGB(.3,.3,.3);c.drawString(left,28,'Score-first composition draft · Separate melody / bass / inner MIDI tracks · Audible review pending')
 c.drawRightString(right,28,f'{page+1} / 2');c.showPage()
c.save()
print(O/'where_the_mileposts_turn.pdf')
