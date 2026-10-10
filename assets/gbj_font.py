"""Native GBJ bitmap rasterizer for the GBA UiRun compiler (not GB Studio).

The official atlas encodes byte values 32..255 in row-major 8x8 tiles.
Magenta columns are proportional-width metadata, never visible pixels.
Original left bearings are retained. Noto Sans CJK Bold is used only for glyphs
absent from the pack; it is rasterized at 10px, baseline aligned with 8px GBJ.
No bitmap rescaling, smoothing, per-frame decoding or GB Studio runtime needed.
"""
from pathlib import Path
import json
from functools import lru_cache
from PIL import Image, ImageDraw, ImageFont
ROOT = Path(__file__).resolve().parent
ATLAS = ROOT / 'fonts/gbj'
FALLBACK = '/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc'
MAGENTA = (255, 0, 255)

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
def latin_fallback(): return ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',8)

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

def render_text(text, height=15, slim=False):
    parts=[]
    for char in text:
        bitmap=glyph(char,slim)
        parts.append((bitmap,2) if bitmap is not None else (fallback_glyph(char),0))
    width=max(1,sum(im.width for im,_ in parts)+1)
    # Render uncropped first and assert that no visible ink can be lost.
    full=Image.new('1',(width,max(15,height))); x=0
    for bitmap,y in parts:
        full.paste(bitmap,(x,y)); x+=bitmap.width
    bounds=full.getbbox()
    assert not bounds or bounds[3]<=height,(text,height,bounds)
    return full.crop((0,0,width,height))
