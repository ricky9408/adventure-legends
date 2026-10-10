#!/usr/bin/env python3
"""Compile journal-only labels and checked interior exits; never changes UI IDs."""
from pathlib import Path
import json,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"assets"))
from gbj_font import render_text
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
FONT = '/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc'
DIRECTIONS = ('N','E','S','W','NE','SE','SW','NW','CENTER','N_LEFT','N_RIGHT',
              'E_TOP','E_BOTTOM','S_LEFT','S_RIGHT','W_TOP','W_BOTTOM')
KINDS = ('ROAD','DOOR','STAIRS','FERRY','LIFT','DIVE','PASSAGE')
JP_DIR = ('北','東','南','西','北東','南東','南西','北西','中央',
          '北・西寄り','北・東寄り','東・北寄り','東・南寄り',
          '南・西寄り','南・東寄り','西・北寄り','西・南寄り')
JP_KIND = ('道','扉','階段','船着場','昇降機','潜水口','通路')

def generate():
    texts = json.loads((ROOT/'assets/journey_map/labels.json').read_text())
    for direction,jpdir in zip(DIRECTIONS,JP_DIR):
        for kind,jpkind in zip(KINDS,JP_KIND):
            texts[f'{direction}_{kind}'] = f'{jpdir}の{jpkind}'
    font = ImageFont.truetype(FONT,10,index=0)
    rows = []
    source = ['#include "journey_map_text.h"',
              '/* Generated paired spans; edit assets/journey_map/labels.json. */']
    metadata = {}
    for name,value in texts.items():
        im = render_text(value,12)
        width = im.width
        limit = 214 if name.endswith('KEYS') or name=='LIST_NOTE' else 146
        assert width <= limit,(name,value,width,limit)
        variants=[]
        for align in (0,1):
            runs=[]
            for y in range(12):
                masks=[]
                for x in range(0,width+align,2):
                    masks.append(sum((1<<b) for b in (0,1)
                        if 0<=x+b-align<width and im.getpixel((x+b-align,y))))
                x=0
                while x<len(masks):
                    if not masks[x]:x+=1;continue
                    end=x+1
                    while end<len(masks) and masks[end]==masks[x]:end+=1
                    runs.append((y*120+x,end-x,masks[x]));x=end
            decoded=Image.new('1',(width+align,12),0)
            for offset,count,mask in runs:
                for half in range(count):
                    yy,xx=divmod(offset+half,120)
                    for bit in (0,1):
                        if mask&(1<<bit):decoded.putpixel((xx*2+bit,yy),1)
            assert decoded.crop((align,0,width+align,12)).tobytes()==im.tobytes()
            source.append('static const UiRun jm_%s_%d[]={%s};' %
                          (name,align,','.join('{%d,%d,%d}'%r for r in runs)))
            variants.append(runs)
        rows.append('{%d,12,0,{jm_%s_0,jm_%s_1},{%d,%d}}' %
                    (width,name,name,len(variants[0]),len(variants[1])))
        metadata[name]={'text':value,'width':width,'height':12}
    source.append('const UiText journey_map_texts[JM_TEXT_COUNT]={'+','.join(rows)+'};')
    source.append('''
extern unsigned short *screen;
extern void text_spans(const UiText*,int,int,int) __attribute__((weak));
void journey_map_text(unsigned id,int x,int y,unsigned char color){
 if(text_spans){text_spans(&journey_map_texts[id],x,y,color);return;}
 const UiText*t=&journey_map_texts[id];const UiRun*r=t->runs[x&1];
 unsigned n=t->count[x&1];unsigned short*base=screen+y*120+(x>>1),pair=color|(color<<8);
 while(n--){unsigned short*dst=base+r->offset;unsigned count=r->count,mask=r->mask;r++;
  if(mask==3)while(count--)*dst++=pair;
  else if(mask==1)while(count--){*dst=(*dst&0xff00)|color;dst++;}
  else while(count--){*dst=(*dst&255)|(color<<8);dst++;}
 }
}
''')
    header='#ifndef EMBER_JOURNEY_MAP_TEXT_H\n#define EMBER_JOURNEY_MAP_TEXT_H\n#include "ui.h"\nenum {\n'+''.join(' JM_'+n+',\n' for n in texts)+' JM_TEXT_COUNT };\nextern const UiText journey_map_texts[JM_TEXT_COUNT];\nvoid journey_map_text(unsigned,int,int,unsigned char);\n#endif\n'
    (ROOT/'src/journey_map_text.h').write_text(header)
    (ROOT/'src/journey_map_text.c').write_text('\n'.join(source))
    (ROOT/'assets/journey_map/text_metrics.json').write_text(json.dumps(metadata,ensure_ascii=False,indent=2)+'\n')
    roads=json.loads((ROOT/'assets/connected_roads.json').read_text())
    sizes=[(240,160)]*78
    for road in roads['roads']:
        for endpoint in road['ends']:sizes[endpoint['room']]=tuple(endpoint['size'])
    extras=json.loads((ROOT/'assets/journey_map/interior_exits.json').read_text())['exits']
    gates={'none':'JM_GATE_NONE','target':'JM_GATE_TARGET','bridge':'JM_GATE_BRIDGE','torches':'JM_GATE_TORCHES'}
    out=['/* Generated map-only metadata. Authoritative geometry stays unchanged. */',
         'static const unsigned short map_sizes[78][2]={'+','.join('{%d,%d}'%s for s in sizes)+'};',
         'static const MapInterior map_interiors[]={']
    for e in extras:
        out.append(' {%d,%d,%d,JOURNEY_%s,JOURNEY_%s,%s},' %
                   (e['room'],e['target'],e['spawn'],e['kind'],e['direction'],gates[e['gate']]))
    out.append('};\n')
    # Public one-hop knowledge uses ROM bitsets, not repeated gate/exit scans.
    # Concealed entrances retain the runtime discovery predicate below.
    links=set()
    for road in roads['roads']:
        a,b=road['ends'];links.add((a['room'],b['room']))
        if not road.get('one_way'):links.add((b['room'],a['room']))
    managed=set(links)|{(45,38),(53,46)}
    for door in roads['doorways']:
        pair=(door['room'],door['target']);links.add(pair);links.add(pair[::-1])
        managed.add(pair);managed.add(pair[::-1])
    special=[]
    travel=json.loads((ROOT/'assets/feedback_travel_entries.json').read_text())['entries']
    hidden={(32,30,4),(39,40,0),(40,39,1),(36,31,1),(44,39,2)}
    for i,e in enumerate(travel):
        pair=(e['room'],e['target'])
        if pair in managed:continue
        if (*pair,e['spawn']) in hidden or e['action']=='TRAVEL_TRIAL':special.append(i)
        else:links.add(pair)
    for e in extras:
        pair=(e['room'],e['target'])
        if pair not in managed:links.add(pair)
    for room in json.loads((ROOT/'assets/campaign_layouts.json').read_text())['rooms']:
        for e in room['exits']:
            pair=(room['id'],e['to_room'])
            if e['id']=='north' and e['to_room'] or e['id']=='south' and pair not in managed:links.add(pair)
    out.append('static const unsigned map_known_adjacency[78][3]={')
    for area in range(78):
        words=[0,0,0]
        for source,target in links:
            if source==area:words[target>>5]|=1<<(target&31)
        out.append(' {'+','.join('0x%08xu'%word for word in words)+'},')
    out.append('};')
    out.append('static const unsigned char map_knowledge_special[]={'+','.join(map(str,special))+'};')
    (ROOT/'src/journey_map_data.inc').write_text('\n'.join(out))
    print('Generated',len(texts),'map labels and',len(extras),'supplemental interior exits')

if __name__=='__main__':generate()
