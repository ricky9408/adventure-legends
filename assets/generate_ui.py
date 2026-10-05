#!/usr/bin/env python3
"""Rasterize the original Japanese UI to compact monochrome glyph masks."""
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]
font=ImageFont.truetype('/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc',12,index=0)
small=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',8)
texts={
 'SUBTITLE':'灯の契約', 'START':'START  はじめる', 'CONTINUE':'START  つづきから', 'NEW':'SELECT  新しい冒険',
 'TAGLINE':'小さな灯が、森を変える。','VILLAGE':'灯守りの里','FOREST':'こもれびの川','TEMPLE':'忘れられた祠','BOSS':'森の心臓',
 'ELDER':'灯守り リュマ','FOX':'ホムラ','LEAF':'ミドリ',
 'INTRO1A':'森の灯が、消えかけている。','INTRO1B':'奥の祠で、守り神が眠れずにいる。',
 'INTRO2A':'この剣と、ふたつの契約を授けよう。','INTRO2B':'ホムラは炎。ミドリは芽吹きの精。',
 'INTRO3A':'Bで呼び出し、Lで仲間を選ぶ。','INTRO3B':'Rで力を借りる。Aで剣を振る。',
 'INTRO4A':'北へ。川ではミドリを頼りなさい。','INTRO4B':'祠の灯は、ホムラで灯すのだ。',
 'VILLAGETALK1':'光は、ひとりでは取り戻せない。','VILLAGETALK2':'傷ついたら、ここへお帰り。',
 'BRIDGE1':'ミドリの力で、根が橋になった！','BRIDGE2':'川を渡り、北の祠を目指そう。',
 'BRIDGEHINT1':'川の向こうへ、道がない。','BRIDGEHINT2':'ミドリをBで呼び、岸でRを押そう。',
 'TEMPLE1':'ふたつの台座に、火の気配がある。','TEMPLE2':'ホムラを呼び、台座の近くでR。',
 'GATE1':'ふたつの炎が、封印をほどいた。','GATE2':'北の扉の奥から、鼓動が聞こえる。',
 'BOSS1':'苔の鎧が、守り神を縛っている。','BOSS2':'炎で鎧を砕き、剣で闇を払おう！',
 'WIN1':'最後の闇が、静かにほどけた。','WIN2':'守り神は、また森の夢を見る。',
 'WIN3':'里に、あたたかな灯が戻った。','WIN4':'ふたりの仲間と、次の旅へ。',
 'COMPLETE':'灯をつなぐ者', 'THANKS':'冒険してくれて、ありがとう', 'RESTART':'START  タイトルへ',
 'DEAD':'灯は、まだ消えない', 'RETRY':'A  祠の記憶から再挑戦',
 'PAUSE':'旅のしおり', 'CONTROL1':'十字キー  移動     A  剣・会話', 'CONTROL2':'B  召喚・帰還     L  仲間を切替',
 'CONTROL3':'R  仲間の力       START  続ける', 'CONTROL4':'ミドリは橋を育て、傷を癒す', 'CONTROL5':'ホムラは炎で台座と鎧を破る',
 'QUEST0':'目的：里を北へ出る', 'QUEST1':'目的：ミドリで川に橋を育てる', 'QUEST2':'目的：北の祠へ進む',
 'QUEST3':'目的：ホムラで２つの台座に点火', 'QUEST4':'目的：北の扉へ進む', 'QUEST5':'目的：炎で鎧を砕き、剣で攻撃',
 'ARMORED':'苔の守り神：炎で鎧を砕け', 'EXPOSED':'鎧が崩れた！ 剣で攻撃！',
 'BHUD':'B 召喚', 'RHUD':'R 力', 'LHUD':'L 切替', 'NEXT':'A ▼', 'SAVED':'記録しました', 'HEALED':'傷が癒えた',
 'NEEDSUMMON':'Bで仲間を呼び出そう', 'COOLDOWN':'力をためている…', 'SUMMONED':'いっしょに行こう',
 'FIREHINT':'炎は台座の近くから放とう', 'TOUCHHINT':'炎を当てると、鎧が崩れる',
 'ENDINGSMALL':'EMBERBOND / FIRST CHAPTER', 'BUILD':'ORIGINAL GBA HOMEBREW  v0.1'
}
items=[]
for name,text in texts.items():
    f=small if name in ('ENDINGSMALL','BUILD') else font
    box=f.getbbox(text); w=min(234,box[2]+1); h=15 if f==font else 10
    im=Image.new('1',(w,h),0); ImageDraw.Draw(im).text((0,-(box[1] if f==small else 2)),text,font=f,fill=1,stroke_width=0)
    stride=(w+7)//8; raw=bytearray(stride*h)
    for y in range(h):
        for x in range(w):
            if im.getpixel((x,y)):raw[y*stride+x//8]|=1<<(x%8)
    items.append((name,w,h,stride,raw))
header='#ifndef EMBER_UI_H\n#define EMBER_UI_H\ntypedef struct { unsigned short width; unsigned char height, stride; const unsigned char *data; } UiText;\nenum {\n'+''.join(' TX_'+n+',\n' for n,*_ in items)+' TX_COUNT };\nextern const UiText ui_texts[TX_COUNT];\n#endif\n'
source='#include "ui.h"\n'
for n,w,h,s,d in items:source+='static const unsigned char txt_'+n+'[] = {'+','.join(str(x) for x in d)+'};\n'
source+='const UiText ui_texts[TX_COUNT] = {\n'+''.join('{%d,%d,%d,txt_%s},\n'%(w,h,s,n) for n,w,h,s,d in items)+'};\n'
(ROOT/'src/ui.h').write_text(header);(ROOT/'src/ui.c').write_text(source)
(ROOT/'assets/ui_texts.json').write_text(json.dumps(texts,ensure_ascii=False,indent=2)+'\n')
print('Generated',len(items),'Japanese text masks')
