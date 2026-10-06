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
 'INTRO3A':'Bで呼び出し、L＋十字で選ぶ。','INTRO3B':'Rで力を借りる。Aで剣を振る。',
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
 'PAUSE':'旅のしおり', 'CONTROL1':'十字キー  移動     A  剣・会話', 'CONTROL2':'B  召喚・帰還   L＋十字  仲間',
 'CONTROL3':'R  仲間の力       START  続ける', 'CONTROL4':'ミドリは橋を育て、傷を癒す', 'CONTROL5':'ホムラは炎で台座と鎧を破る',
 'QUEST0':'目的：里を北へ出る', 'QUEST1':'目的：ミドリで川に橋を育てる', 'QUEST2':'目的：北東の祠へ進む',
 'QUEST3':'目的：ホムラで２つの台座に点火', 'QUEST4':'目的：北の扉へ進む', 'QUEST5':'目的：炎で鎧を砕き、剣で攻撃',
 'ARMORED':'苔の守り神：炎で鎧を砕け', 'EXPOSED':'鎧が崩れた！ 剣で攻撃！',
 'BHUD':'B 召喚', 'RHUD':'R 力', 'LHUD':'L 切替', 'NEXT':'A ▼', 'SAVED':'記録しました', 'HEALED':'傷が癒えた',
 'NEEDSUMMON':'Bで仲間を呼び出そう', 'COOLDOWN':'力をためている…', 'SUMMONED':'いっしょに行こう',
 'FIREHINT':'炎は台座の近くから放とう', 'TOUCHHINT':'炎を当てると、鎧が崩れる',
 'ENDINGSMALL':'EMBERBOND / THE LANTERNS', 'BUILD':'ORIGINAL GBA HOMEBREW  v0.3',
 'EXPLORE1':'STARTで地図、SELECTで回避。', 'EXPLORE2':'寄り道には、小さな発見がある。',
 'CAMP1':'たき火のぬくもりが、傷を癒す。', 'CAMP2':'次はここから、旅を続けられる。',
 'RELIC1':'命のかけらを見つけた！', 'RELIC2':'ハートの最大数が、２つ増えた。',
 'MAP':'こもれびの森の地図', 'MAP_KEYS':'A 仲間へ     B 戻る',
 'ROLL_CONTROL':'SELECT 回避   A ページ切替',
 'CAMP_GUIDE1':'たき火でA。休んで、記録しよう。', 'CAMP_GUIDE2':'剣は三連撃。最後の一撃が強い。'
}
campaign=json.loads((ROOT/'assets/campaign_dialogue.json').read_text())
for name,scene in campaign['dialogue'].items():
    texts['C_'+name+'_SPEAKER']=scene['speaker']
    for p,page in enumerate(scene['pages']):
        for l,line in enumerate(page):texts['C_'+name+'_'+str(p)+'_'+str(l)]=line
for name,t in campaign['labels'].items():texts['C_'+name]=t
for room in json.loads((ROOT/'assets/campaign_layouts.json').read_text())['rooms']:texts['C_ROOM_'+str(room['id'])]=room['name_ja']
texts.update({'C_SELECTED':'仲間の力', 'C_JOURNAL_HINT':'A  地図・仲間    B  戻る', 'C_HUB_EAST':'東：空織りの祠', 'C_HUB_WEST':'西：灯核の祠', 'C_SAVE_FAILED':'記録できませんでした', 'C_BOSS_WARN':'攻撃の印に気をつけよう', 'C_WIND_WINDOW':'風で結び目をほどこう！', 'C_ALL_FOUR':'四つの力で、灯をつなごう', 'C_UNKNOWN':'？？？', 'C_WIND_HELP':'風で帆を開き、弾を吹き消す', 'C_STONE_HELP':'石の重しと、一撃を防ぐ守り', 'C_NEED_STONE':'石の印：コハクの力を', 'C_NEED_WIND':'風の印：フウリの力を', 'C_NEED_FIRE':'炎の印：ホムラの力を', 'C_PHASE_CHANGE':'次の印が、浮かび上がる'})
texts.update({'C_MAP_ROUTE':'三つの灯をつなぐ道','C_MAP_GROVE':'森の灯','C_MAP_SKY':'空の灯','C_MAP_CORE':'核の灯','C_MAP_RETURN':'里から東へ空、西へ核','C_MAP_NEXT':'A 仲間へ   B 戻る'})
texts.update({'E_HOMURA':'ホムラ・炉守','E_MIDORI':'ミドリ・樹冠','E_FUURI':'フウリ・風織','E_KOHAKU':'コハク・岩門','E_WOOD':'木','E_FIRE':'火','E_EARTH':'土','E_METAL':'金','E_WATER':'水','E_YIN':'陰','E_YANG':'陽','E_GROWTH':'仲間の成長','E_LEVEL':'レベル','E_BOND':'きずな','E_READY':'進化の準備が整った','E_LEVEL_MORE':'冒険で経験を積もう','E_BOND_MORE':'いっしょに絆を育てよう','E_STORY_MORE':'先の旅が力を呼び覚ます','E_TRIAL_MORE':'仲間の願いをかなえよう','E_SANCTUARY':'里か休憩所で進化できる','E_GROWN':'新たな姿で、次の旅へ','E_COMMAND_NEW':'新しい技を選択中','E_COMMAND_OLD':'いつもの技を選択中','E_KEYS':'R 技変更  SELECT 進化','E_CONFIRM':'新しい姿へ進化しますか','E_KEEP_POWER':'大切な力と絆は引き継ぐ','E_CHOICE':'今は待つこともできる','E_CONFIRM_KEYS':'A 進化する   B いまは待つ','E_BOND_LIGHT':'きずなが、光になる','E_SAVING':'冒険を記録しています'})
texts.update({'E_WISH_FIRE':'森の忘れ火に、小さな炎を','E_WISH_ROOT':'森の枯れ芽を、三つ育てよう','E_WISH_WIND':'風待ちの尾根の、風の工房へ','E_WISH_STONE':'夕灯の坂の、石の作業場へ','E_MOVE_FIRE':'技：火のしずく','E_MOVE_HEAL':'技：芽吹きの癒し','E_MOVE_WIND':'技：ひとひらの風','E_MOVE_STONE':'技：小さな石の守り','E_MOVE_HEARTH':'技：三つの炉火','E_MOVE_CANOPY':'技：根の庇護','E_MOVE_REFLECT':'技：返し風','E_MOVE_ARCH':'技：岩門の構え','E_LEVEL_UP':'仲間が成長した！'})
texts.update({'T_ROOM_WIND':'風織りの庭','T_ROOM_STONE':'琥珀の工房','T_WIND_HINT1':'風を、金の糸へつなごう。','T_WIND_HINT2':'Rで風車の向きが変わる。','T_STONE_HINT1':'ふたつの印に、重みを集めよう。','T_STONE_HINT2':'Aで押して、最後に石の力を。','T_COMPLETE1':'仲間の願いが、かなった！','T_COMPLETE2':'里のしおりで、新たな一歩を。','T_FIRE_HINT1':'忘れられた炉に、火の気配。','T_FIRE_HINT2':'ホムラは、小さく尾を揺らした。','T_ROOT_HINT1':'枯れた根に、芽吹きの気配。','T_ROOT_HINT2':'ミドリは、そっと葉を広げた。','T_RESTORED':'小さな場所に、灯が戻った','T_NEED_PLATES':'ふたつの印が、重みを待つ','T_ALREADY':'この願いは、もうかなった','T_RESET':'仕掛けを元に戻した','T_BLOCKED':'こちらには押せない'})
texts.update({'E_NEXT_GROWTH':'A 成長へ    B 戻る'})
texts.update({'Q_CHOOSE':'L＋十字で仲間を選ぶ','Q_RELEASE':'Lを離して決定','Q_CANCEL':'B やめる','Q_PARTY':'仲間の編成','Q_EMPTY':'空き枠','Q_MENU_MOVE':'←→ 枠を選ぶ  ↑↓ 仲間','Q_MENU_ASSIGN':'R 入替  SELECT 外す','Q_LAST_MEMBER':'仲間はひとり以上必要'})
for extra in ('equipment','creatures','region','northern_region'):
    additions=ROOT/'assets'/extra/'ui_additions.json'
    if additions.exists():
        for key,value in json.loads(additions.read_text()).items():
            assert key not in texts or texts[key]==value,key
            texts[key]=value
items=[]
for name,text in texts.items():
    f=small if name in ('ENDINGSMALL','BUILD','C_FINAL_SMALL') else font
    box=f.getbbox(text); w=box[2]+1; h=15 if f==font else 10
    assert w<=214,(name,text,w)
    im=Image.new('1',(w,h),0); ImageDraw.Draw(im).text((0,-(box[1] if f==small else 2)),text,font=f,fill=1,stroke_width=0)
    variants=[]
    for align in (0,1):
        runs=[]
        for y in range(h):
            masks=[]
            for px in range(0,w+align,2):
                bits=0
                for bit in (0,1):
                    x=px+bit-align
                    if 0<=x<w and im.getpixel((x,y)):bits|=1<<bit
                masks.append(bits)
            x=0
            while x<len(masks):
                mask=masks[x]
                if not mask:x+=1;continue
                end=x+1
                while end<len(masks) and masks[end]==mask and end-x<255:end+=1
                runs.append((y*120+x,end-x,mask));x=end
        # Both halfword alignments must reconstruct the original exact pixels.
        decoded=Image.new('1',(w+align,h),0)
        for offset,count,mask in runs:
            for half in range(count):
                y,x=divmod(offset+half,120)
                for bit in (0,1):
                    if mask&(1<<bit):decoded.putpixel((x*2+bit,y),1)
        assert decoded.crop((align,0,w+align,h)).tobytes()==im.tobytes(),name
        variants.append(runs)
    items.append((name,w,h,variants))
header='#ifndef EMBER_UI_H\n#define EMBER_UI_H\n/* Precompiled nonzero pixel-pair spans: no per-frame glyph bit decoding. */\ntypedef struct { unsigned short offset; unsigned char count, mask; } UiRun;\ntypedef struct { unsigned short width; unsigned char height, reserved; const UiRun *runs[2]; unsigned short count[2]; } UiText;\nenum {\n'+''.join(' TX_'+n+',\n' for n,*_ in items)+' TX_COUNT };\nextern const UiText ui_texts[TX_COUNT];\n#endif\n'
source=''
for n,w,h,variants in items:
    for align,runs in enumerate(variants):
        source+='static const UiRun txt_'+n+'_'+str(align)+'[] = {'+','.join('{%d,%d,%d}'%r for r in runs)+'};\n'
source+='const UiText ui_texts[TX_COUNT] = {\n'+''.join('{%d,%d,0,{txt_%s_0,txt_%s_1},{%d,%d}},\n'%(w,h,n,n,len(v[0]),len(v[1])) for n,w,h,v in items)+'};\n'
(ROOT/'src/ui.h').write_text(header)
parts=[];part=''
for line in source.splitlines(True):
    if len((part+line).encode())>32000:parts.append(part);part=''
    part+=line
if part:parts.append(part)
folder=ROOT/'src/ui_data';folder.mkdir(exist_ok=True)
for old in folder.glob('part_*.inc'):old.unlink()
for i,part in enumerate(parts):(folder/f'part_{i:03}.inc').write_text(part)
(ROOT/'src/ui.c').write_text('#include "ui.h"\n/* Generated text masks; edit assets/generate_ui.py. */\n'+''.join(f'#include "ui_data/part_{i:03}.inc"\n' for i in range(len(parts))))
(ROOT/'assets/ui_texts.json').write_text(json.dumps(texts,ensure_ascii=False,indent=2)+'\n')
print('Generated',len(items),'Japanese paired-span text masks')
