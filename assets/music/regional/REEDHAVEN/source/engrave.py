from pathlib import Path
import json,re
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
O=Path(__file__).parent;d=json.loads((O/'composition_events.json').read_text())
pdfmetrics.registerFont(TTFont('Music','/usr/share/fonts/truetype/noto/NotoMusic-Regular.ttf'))
W,H=A4;c=canvas.Canvas(str(O/'where_the_reeds_turn.pdf'),pagesize=A4);c.setTitle(d['title'])
L=36;R=W-32;sp=5.2;half=sp/2;sig=53;bw=(R-L-sig)/4

def pitchpos(p,role):
 m=re.fullmatch(r'([A-G])([#b]?)(\d)',p);return int(m[3])*7+'CDEFGAB'.index(m[1])-(18 if role=='bass' else 30)
def note(x,y,dur,stem,flag):
 c.saveState();c.translate(x,y);c.rotate(18);c.setLineWidth(.75);c.setFillColorRGB(*( (1,1,1) if dur>=2 else (0,0,0)));c.ellipse(-3.2,-2,3.2,2,fill=1);c.restoreState()
 sx=x+2.9 if stem=='up' else x-2.9;sy=y+25 if stem=='up' else y-25;c.setLineWidth(.65);c.line(sx,y,sx,sy)
 if dur==3:c.circle(x+6,y+1,.8,fill=1,stroke=0)
 if flag:
  p=c.beginPath();p.moveTo(sx,sy)
  if stem=='up':p.curveTo(sx+9,sy-3,sx+7,sy-12,sx+3,sy-14)
  else:p.curveTo(sx+9,sy+3,sx+7,sy+12,sx+3,sy+14)
  c.setLineWidth(1.6);c.drawPath(p)
 return sx,sy
for page in range(3):
 c.setFont('Helvetica-Bold',20);c.drawString(L,H-42,d['title']);c.setFont('Helvetica',10);c.drawString(L,H-60,'Reedhaven · Original Adventure Legends town theme')
 c.setFont('Helvetica-Oblique',9);c.drawString(L,H-77,'Gently flowing · G major · 3/4 · quarter = 88 · Three monophonic voices')
 for s in range(2):
  start=page*8+s*4;top=H-176-s*325;ys={'melody':top,'inner':top-90,'bass':top-174}
  for role,y in ys.items():
   c.setFont('Helvetica',7);c.drawString(L,y+42,{'melody':'Singing lead','inner':'Plucked counterline','bass':'Rounded bass'}[role]);c.setLineWidth(.4)
   for z in range(5):c.line(L,y+sp*z,R,y+sp*z)
   c.setFont('Music',29);c.drawString(L+2,y+(2 if role=='bass' else -2),'𝄢' if role=='bass' else '𝄞');c.setFont('Music',13);c.drawString(L+25,y+(6 if role=='bass' else 8)*half-5,'♯')
   if page==0 and s==0:
    c.setFont('Times-Bold',13);c.drawString(L+39,y+11,'3');c.drawString(L+39,y,'4')
  c.setLineWidth(.7);c.line(L,ys['bass'],L,top+4*sp)
  for k in range(4):
   b=d['bars'][start+k];n=b['number'];x0=L+sig+k*bw
   c.setFont('Helvetica',7);c.drawString(x0+2,top+57,str(n));c.setFont('Helvetica',9);c.drawString(x0+12,top+42,b['chord'])
   if n in (1,9,17):
    c.rect(x0,top+70,22,18);c.setFont('Helvetica-Bold',11);c.drawCentredString(x0+11,top+74,{1:'A',9:'B',17:"A'"}[n])
   for role,y0 in ys.items():
    ev=[]
    for e in b[role]:
     x=x0+14+e['onset']*(bw-22)/3;p=e['pitch'];dur=e['duration']
     if p=='R':
      c.setFont('Music',17);c.drawString(x-3,y0+5,'𝄾');ev.append(None);continue
     di=pitchpos(p,role);y=y0+di*half
     if di<0:
      for z in range(-2,di-1,-2):c.setLineWidth(.6);c.line(x-5,y0+z*half,x+5,y0+z*half)
     if di>8:
      for z in range(10,di+1,2):c.setLineWidth(.6);c.line(x-5,y0+z*half,x+5,y0+z*half)
     ev.append(dict(x=x,y=y,dur=dur,pos=e['onset'],stem='up' if di<4 else 'down'))
    groups=[]
    for i in range(len(ev)-1):
     a,b2=ev[i],ev[i+1]
     if a and b2 and a['dur']==b2['dur']==.5 and int(a['pos'])==int(b2['pos']):groups.append([i,i+1])
    beamed={i for g in groups for i in g}
    for g in groups:
     stem='up' if sum(ev[i]['y'] for i in g)/len(g)<y0+10 else 'down'
     for i in g:ev[i]['stem']=stem
    for i,e in enumerate(ev):
     if e:e['end']=note(e['x'],e['y'],e['dur'],e['stem'],e['dur']==.5 and i not in beamed)
    for g in groups:
     up=ev[g[0]]['stem']=='up';ey=(max if up else min)(ev[i]['y'] for i in g)+(25 if up else -25);c.setLineWidth(.65)
     for i in g:c.line(ev[i]['end'][0],ev[i]['y'],ev[i]['end'][0],ey)
     c.setLineWidth(2.7);c.line(ev[g[0]]['end'][0],ey,ev[g[-1]]['end'][0],ey)
   c.setLineWidth(.5);c.line(x0+bw,ys['bass'],x0+bw,top+4*sp)
   if n==24:c.line(x0+bw-3,ys['bass'],x0+bw-3,top+4*sp)
  c.setFont('Helvetica-Oblique',8)
  if start==0:c.drawString(L+sig,ys['bass']-38,'Lead mp and connected; counterline p, lightly detached; bass warm. No pedal.')
  if start==8:c.drawString(L+sig,ys['bass']-38,'Middle: widen the singing line gently. The C harmony in bar 13 carries a bright #11.')
  if start==20:c.drawString(L+sig,ys['bass']-38,'Loop directly from bar 24 to bar 1. Leave the written breath; no extra pause or fade.')
 c.setFont('Helvetica',8);c.drawString(L,30,'Score-first composition · Piano MIDI for neutral review · Final GBA timbres and audio review pending');c.drawRightString(R,17,f'{page+1} / 3');c.showPage()
c.save()
