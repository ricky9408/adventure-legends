"""Native Japanese raster compiler for GBA UiRun masks (not GB Studio).

PixelMplus12 Regular is the coherent native 12px prose/menu font. Explicitly
constrained summaries can use the author's unscaled k8x12 bitmap. Small ASCII
footers retain GBJ-Slim/DejaVu8. No glyph is resized or antialiased. Legacy GBJ
and Noto accessors remain available for immutable source-atlas proof callers;
Noto is not the default render_text path.
"""
from pathlib import Path
import json
import os
import struct
import re
from functools import lru_cache
from PIL import Image, ImageDraw, ImageFont
ROOT = Path(__file__).resolve().parent
ATLAS = ROOT / 'fonts/gbj'
FALLBACK = os.environ.get('EMBERBOND_NOTO_FONT','/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc')
MAGENTA = (255, 0, 255)
NATIVE_FONT = ROOT / 'fonts/pixelmplus/PixelMplus12-Regular.ttf'
COMPACT_FONT = ROOT / 'fonts/k8x12/k8x12.bdf'

@lru_cache(None)
def atlas(slim=False):
    name = 'GBJ-Slim' if slim else 'GBJ'
    return Image.open(ATLAS / (name+'.png')).convert('RGB'), json.loads((ATLAS/(name+'.json')).read_text())['mapping']

@lru_cache(None)
def glyph(char, slim=False):
    sheet, mapping = atlas(slim)
    # Unmapped byte positions inside the kana region are NOT ASCII. Only these
    # verified ASCII defaults have the same meaning in the supplied atlas.
    code = mapping.get(char)
    if code is None and char in ' !%&()/0123456789:=?': code = ord(char)
    if code is None: return None
    i = code - 32
    assert 0 <= i < 224
    tile = sheet.crop((i%16*8, i//16*8, i%16*8+8, i//16*8+8))
    width = next((x for x in range(8) if all(tile.getpixel((x,y)) == MAGENTA for y in range(8))), 8)
    assert all(tile.getpixel((x,y)) == MAGENTA for x in range(width,8) for y in range(8))
    mask = Image.new('1',(width,8))
    for y in range(8):
        for x in range(width):
            r,g,b = tile.getpixel((x,y))
            if max(r,g,b)<128: mask.putpixel((x,y),1)
    return mask

@lru_cache(None)
def fallback(): return ImageFont.truetype(FALLBACK, 10, index=0)

@lru_cache(None)
def latin_fallback(): return ImageFont.truetype(os.environ.get('EMBERBOND_DEJAVU_FONT','/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'),8)

@lru_cache(None)
def fallback_glyph(char):
    latin = ord(char)<128
    f=latin_fallback() if latin else fallback(); box=f.getbbox(char)
    # Pillow monochrome hinting can put ink beyond getbbox/getlength (e.g. z).
    # Measure an actual padded raster, not metrics alone; preserve bearings.
    pad=16
    padded=Image.new('1',(64,48))
    ImageDraw.Draw(padded).text((pad,pad+(-1 if latin else -2)),char,font=f,fill=1)
    ink=padded.getbbox()
    left=min(0,ink[0]-pad) if ink else 0
    right=max(0,ink[2]-pad) if ink else 0
    bottom=max(13,ink[3]-pad) if ink else 13
    width=max(1,round(f.getlength(char)),box[2],right)-left
    mask=padded.crop((pad+left,pad,pad+left+width,pad+bottom))
    return mask

@lru_cache(None)
def native_font(): return ImageFont.truetype(NATIVE_FONT,12)

@lru_cache(None)
def native_coverage():
    """Read Unicode cmap coverage; never silently render the TTF .notdef box."""
    data=NATIVE_FONT.read_bytes();count=struct.unpack_from('>H',data,4)[0]
    tables={data[12+i*16:16+i*16]:struct.unpack_from('>II',data,20+i*16) for i in range(count)}
    offset,_=tables[b'cmap'];subtables=struct.unpack_from('>H',data,offset+2)[0];covered=set()
    for i in range(subtables):
        platform,encoding,relative=struct.unpack_from('>HHI',data,offset+4+i*8)
        if platform not in (0,3):continue
        start=offset+relative;kind=struct.unpack_from('>H',data,start)[0]
        if kind==4:
            segments=struct.unpack_from('>H',data,start+6)[0]//2
            ends=start+14;starts=ends+segments*2+2;deltas=starts+segments*2;ranges=deltas+segments*2
            for j in range(segments):
                first=struct.unpack_from('>H',data,starts+2*j)[0];last=struct.unpack_from('>H',data,ends+2*j)[0]
                delta=struct.unpack_from('>h',data,deltas+2*j)[0];distance=struct.unpack_from('>H',data,ranges+2*j)[0]
                for code in range(first,last+1):
                    index=struct.unpack_from('>H',data,ranges+2*j+distance+2*(code-first))[0] if distance else code
                    if index or not distance:index=(index+delta)&65535
                    if index and code!=65535:covered.add(chr(code))
        elif kind==12:
            groups=struct.unpack_from('>I',data,start+12)[0]
            for j in range(groups):
                first,last,index=struct.unpack_from('>III',data,start+16+12*j)
                covered.update(chr(code) for code in range(first,last+1) if index+code-first)
    return frozenset(covered)

@lru_cache(None)
def native_glyph(char):
    if char not in native_coverage():raise ValueError('PixelMplus12 missing glyph: '+repr(char))
    font=native_font();pad=24
    full=Image.new('1',(96,72));ImageDraw.Draw(full).text((pad,pad),char,font=font,fill=1)
    bounds=full.getbbox();advance=round(font.getlength(char))
    left=min(0,bounds[0]-pad) if bounds else 0
    right=max(advance,bounds[2]-pad) if bounds else advance
    # Never discard a font's upper bearing before validating its target cell.
    assert not bounds or bounds[1]>=pad,('native glyph above baseline cell',char,bounds)
    bottom=max(15,bounds[3]-pad) if bounds else 15
    return full.crop((pad+left,pad,pad+right,pad+bottom))

@lru_cache(None)
def compact_atlas():
    cells={}
    for block in COMPACT_FONT.read_text().split('STARTCHAR ')[1:]:
        rows=block.split('ENDCHAR')[0].splitlines()
        code=int(next(r for r in rows if r.startswith('ENCODING ')).split()[1])
        advance=int(next(r for r in rows if r.startswith('DWIDTH ')).split()[1])
        w,h,xoffset,yoffset=map(int,next(r for r in rows if r.startswith('BBX ')).split()[1:])
        cell=Image.new('1',(advance,12));start=rows.index('BITMAP')+1
        for y,row in enumerate(rows[start:start+h]):
            bits=int(row,16);bitwidth=len(row)*4
            for x in range(w):
                if bits&(1<<(bitwidth-1-x)):
                    xx=x+xoffset;yy=10-yoffset-h+y
                    assert 0<=xx<advance and 0<=yy<12,(code,xx,yy)
                    cell.putpixel((xx,yy),1)
        cells[chr(code)]=cell
    return cells

def render_text(text, height=15, slim=False, compact=False):
    parts=[]
    for char in text:
        if compact:
            if char not in compact_atlas():raise ValueError('k8x12 missing glyph: '+repr(char))
            parts.append((compact_atlas()[char],1))
        elif slim:
            bitmap=glyph(char,True)
            # Explicit historical/slim callers retain the original glyph API;
            # production's five 10px footer labels contain ASCII only. Bounds
            # below reject any unsupported Japanese glyph too tall for10px.
            parts.append((bitmap,2) if bitmap is not None else (fallback_glyph(char),0))
        else:parts.append((native_glyph(char),0))
    width=max(1,sum(im.width for im,_ in parts)+1)
    # Allocate for every source bitmap BEFORE checking target height: checking
    # an already-clipped 15px canvas could previously hide lost lower strokes.
    full=Image.new('1',(width,max([height]+[im.height+y for im,y in parts]))); x=0
    for bitmap,y in parts:
        full.paste(bitmap,(x,y)); x+=bitmap.width
    bounds=full.getbbox()
    assert not bounds or bounds[3]<=height,(text,height,bounds)
    return full.crop((0,0,width,height))

def deduplicate_spans(source):
    """Share exact immutable pixel-pair arrays; UiText IDs/ABI stay unchanged.

    This compile-time alias needs no cartridge state, decoding or extra work.
    Different strings are shared only if every offset/count/mask byte matches.
    """
    seen={}
    pattern=re.compile(r'^(static const UiRun\s+)(\w+)\[\]\s*=\s*\{([^;]+)\};$',re.M)
    def replace(match):
        name=match[2];data=re.sub(r'\s+','',match[3])
        if data in seen:return '#define '+name+' '+seen[data]
        seen[data]=name
        return match[0]
    return pattern.sub(replace,source)
