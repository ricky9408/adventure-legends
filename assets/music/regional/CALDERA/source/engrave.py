from pathlib import Path
import json,re,sys,math
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
O=Path(sys.argv[1]);d=json.loads((O/'composition_events.json').read_text());pdfmetrics.registerFont(TTFont('Music','/usr/share/fonts/truetype/noto/NotoMusic-Regular.ttf'))
W,H=A4;c=canvas.Canvas(str(O/(d['slug']+'.pdf')),pagesize=A4);c.setTitle(d['title']);c.setAuthor('Original composition for Adventure Legends');left=39;right=W-29;sig=48;bw=(right-left-sig)/4;ss=4.7;hs=ss/2
roles=['melody','inner','bass'];beats=int(d['meter'].split('/')[0]);nbar=len(d['bars']);pages=math.ceil(nbar/12)
def di(p,r):
 m=re.fullmatch(r'([A-G])([#b]?)(\d)',p);return int(m[3])*7+'CDEFGAB'.index(m[1])-(18 if r=='bass' else 30)
def note(x,y,dur,up):
 c.saveState();c.translate(x,y);c.rotate(18);c.setFillColorRGB(*( (1,1,1) if dur>=2 else (0,0,0)));c.setLineWidth(.65);c.ellipse(-3,-1.9,3,1.9,fill=1,stroke=1);c.restoreState();sx=x+(2.7 if up else -2.7);sy=y+(23 if up else -23);c.setLineWidth(.6)
 if dur<4:c.line(sx,y,sx,sy)
 if dur in (1.5,3):c.circle(x+5.7,y+1,.8,fill=1,stroke=0)
 if dur==.5:
  p=c.beginPath();p.moveTo(sx,sy);sg=1 if up else -1;p.curveTo(sx+sg*8,sy-sg*3,sx+sg*7,sy-sg*11,sx+sg*3,sy-sg*13);c.setLineWidth(1.4);c.drawPath(p)
for page in range(pages):
 c.setFont('Helvetica-Bold',18);c.drawString(left,H-36,d['title']);c.setFont('Helvetica',9);c.drawString(left,H-53,'Adventure Legends | '+d['cue']+' | Original three-voice dungeon cue')
 c.setFont('Helvetica-Oblique',9);c.drawString(left,H-69,f"Steady pulse | quarter = {d['tempo']} | {d['key']} | {d['meter']} | {nbar*beats*60/d['tempo']:.2f} seconds")
 for sy in range(3):
  start=page*12+sy*4
  if start>=nbar:continue
  top=H-145-sy*222;ys=[top,top-65,top-130]
  c.setLineWidth(.7);c.line(left,ys[-1],left,top+4*ss)
  for r,y0 in zip(roles,ys):
   c.setLineWidth(.35)
   for k in range(5):c.line(left,y0+k*ss,right,y0+k*ss)
   c.setFont('Helvetica',6);c.drawRightString(left-3,y0+8,r[0].upper());c.setFont('Music',28);c.drawString(left+2,y0+(-2 if r!='bass' else 2),'𝄢' if r=='bass' else '𝄞')
   if start==0:c.setFont('Times-Bold',12);c.drawString(left+36,y0+10,str(beats));c.drawString(left+36,y0,'4')
  for j in range(min(4,nbar-start)):
   b=d['bars'][start+j];n=b['number'];x0=left+sig+j*bw
   c.setFont('Helvetica',7);c.drawString(x0+2,top+47,str(n));c.setFont('Helvetica',6.8);c.drawString(x0+9,top+36,b['chord'])
   if str(n) in d['sections']:c.setFont('Helvetica-Bold',9);c.drawString(x0,top+60,d['sections'][str(n)])
   for r,y0 in zip(roles,ys):
    state={}
    for e in b[r]:
     x=x0+13+e['onset']*(bw-23)/beats;dur=e['duration'];p=e['pitch']
     if p=='R':c.setFont('Music',17);c.drawString(x-3,y0+5,'𝄾' if dur==.5 else '𝄽');continue
     v=di(p,r);y=y0+v*hs;ma=re.fullmatch(r'([A-G])([#b]?)(\d)',p);a={'':0,'#':1,'b':-1}[ma[2]];k=(ma[1],ma[3]);old=state.get(k,0)
     if a!=old:c.setFont('Music',10);c.drawString(x-10,y-3,{0:'♮',1:'♯',-1:'♭'}[a])
     state[k]=a
     for z in (range(-2,v-1,-2) if v<0 else range(10,v+1,2) if v>8 else []):c.setLineWidth(.55);c.line(x-5,y0+z*hs,x+5,y0+z*hs)
     note(x,y,dur,v<4)
   c.setLineWidth(.55);c.line(x0+bw,ys[-1],x0+bw,top+4*ss)
   if n==nbar:c.line(x0+bw-3,ys[-1],x0+bw-3,top+4*ss)
  c.setFont('Helvetica-Oblique',7)
  if start==8:c.drawString(left+sig,ys[-1]-31,'Keep the bass grounded through the contrasting phrase. All accidentals are shown explicitly.')
  if start+4>=nbar:c.drawString(left+sig,ys[-1]-31,'Return directly to bar 1 after the final measure. Keep the pulse; no closing ritardando.')
 c.setFont('Helvetica',7);c.drawString(left,25,'Three monophonic voices | Reference MIDI uses piano timbre | Score/encoding checked; audible review pending');c.drawRightString(right,25,f'{page+1} / {pages}');c.showPage()
c.save()
