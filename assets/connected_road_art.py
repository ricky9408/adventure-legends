"""Shared, original baked road scenery and exact half-open clearance geometry.

The JSON is also consumed by the runtime route-table generator. No raster source
or frame-time scenery overlay is used. Generator-specific landmarks are drawn
AFTER roads, and whole tree silhouettes are excluded before they are authored.
"""
from pathlib import Path
import json, random
from PIL import Image, ImageDraw

SOURCE=Path(__file__).with_name('connected_roads.json')
DATA=json.loads(SOURCE.read_text())

def endpoints(room):
    return [e for road in DATA['roads'] for e in road['ends'] if e['room']==room]

def paint_lines(room):
    return [line for e in endpoints(room) for line in e.get('paint',[])]

def mask(room,size,extra=0):
    im=Image.new('L',size);d=ImageDraw.Draw(im)
    for line in paint_lines(room):
        width=line['width']+extra*2
        if width<1:continue
        pts=[tuple(p) for p in line['points']];d.line(pts,fill=255,width=width)
        rr=width//2
        for x,y in (pts[1:-1] if line.get('flat_caps') else pts):d.ellipse((x-rr,y-rr,x+rr,y+rr),fill=255)
    return im

def crosses_road(room,box,extra=4):
    ends=endpoints(room)
    if not ends:return False
    x,y,w,h=map(int,box)
    return bool(mask(room,ends[0]['size'],extra).crop((x,y,x+w,y+h)).getbbox())

def draw(a,room,palette):
    """Draw quiet material planes, worn shoulders, and deterministic sparse flecks."""
    for n,line in enumerate(paint_lines(room)):
        pts=[tuple(p)for p in line['points']];width=line['width'];material=line.get('material','dirt')
        ramp={'dirt':['grass1','dirt1','dirt2','dirt3','dirt4'],
              'stone':['stone1','stone2','stone3','stone4','stone5'],
              'wood':['wood0','wood1','wood2','wood3','wood4']}[material]
        def color(c):return palette.get('bg_sunlit_'+c,palette[c])
        masks=[]
        for extra,c in [(3,ramp[0]),(2,ramp[1]),(1,ramp[2]),(0,ramp[3]),(-5,ramp[4])]:
            m=Image.new('L',a.im.size);d=ImageDraw.Draw(m);ww=max(2,width+extra*2);rr=ww//2
            d.line(pts,fill=255,width=ww)
            for x,y in (pts[1:-1] if line.get('flat_caps') else pts):d.ellipse((x-rr,y-rr,x+rr,y+rr),fill=255)
            a.im.paste(color(c),(0,0),m);masks.append(m)
        a.d=ImageDraw.Draw(a.im);rng=random.Random(104729+room*131+n);core=masks[-1]
        for _ in range(a.im.width*a.im.height//55):
            x=rng.randrange(a.im.width);y=rng.randrange(a.im.height)
            if not core.getpixel((x,y)):continue
            for dx in range(rng.randrange(2,5)):
                if x+dx<a.im.width and core.getpixel((x+dx,y)):
                    a.im.putpixel((x+dx,y),color(ramp[2 if _%3 else 3]))
        if material=='wood':
            for y in range(0,a.im.height,5):
                for x in range(a.im.width):
                    if masks[3].getpixel((x,y)):a.im.putpixel((x,y),color('wood5'if y%10 else'wood2'))
            for y in range(3,a.im.height,10):
                for x in range(11+(y//10%2)*9,a.im.width,21):
                    if core.getpixel((x,y)):a.im.putpixel((x,y),color('wood1'))
    a.d=ImageDraw.Draw(a.im)

def subtract(rect,cut):
    x,y,w,h=rect;cx,cy,cw,ch=cut;l=max(x,cx);t=max(y,cy);r=min(x+w,cx+cw);b=min(y+h,cy+ch)
    if l>=r or t>=b:return [list(rect)]
    parts=[[x,y,w,t-y],[x,b,w,y+h-b],[x,t,l-x,b-t],[r,t,x+w-r,b-t]]
    return [p for p in parts if p[2]>0 and p[3]>0]

def clear_rects(room):
    return [rect for e in endpoints(room) for rect in e.get('clear_rects',[])]

def carve_solids(room,solids):
    """Split only approved edge rectangles; never clear a broad interior lane."""
    out=[]
    for solid in solids:
        boxes=[solid['rect']]
        for cut in clear_rects(room):boxes=[part for b in boxes for part in subtract(b,cut)]
        out.extend({**solid,'rect':b}for b in boxes)
    return out

def open_borders(room):
    room['solids']=carve_solids(room['id'],room['solids'])
    return room

def stair(a,x,y,w,h,palette):
    """A supported timber stair running up a facade, with a real top landing."""
    def c(name):return palette.get('bg_sunlit_'+name,palette[name])
    d=a.d;d.rectangle((x-2,y-2,x+w+1,y+h+1),fill=c('wood0'))
    d.rectangle((x,y,x+w-1,y+h-1),fill=c('wood2'))
    for yy in range(y+2,y+h,5):
        d.rectangle((x+2,yy,x+w-3,yy+2),fill=c('wood4'))
        d.line([(x+3,yy),(x+w-4,yy)],fill=c('wood5'))
    for xx in (x-2,x+w):
        d.rectangle((xx,y-6,xx+1,y+h),fill=c('wood1'))
        d.line([(xx,y-6),(xx,y+h-1)],fill=c('wood4'))
        for yy in (y-6,y+h-3):d.rectangle((xx-1,yy,xx+2,yy+2),fill=c('wood5'))
