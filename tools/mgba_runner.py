#!/usr/bin/env python3
"""Real mGBA automation. Python API plus a simple frame/key/read/screenshot script CLI."""
from pathlib import Path
import argparse, ctypes as C, json, shlex, sys
from PIL import Image
HERE=Path(__file__).resolve().parent
KEYS={'A':1,'B':2,'SELECT':4,'START':8,'RIGHT':16,'LEFT':32,'UP':64,'DOWN':128,'R':256,'L':512,'NONE':0}
def keymask(keys):
    if isinstance(keys,int): return keys
    try:return int(keys,0)
    except ValueError:return sum(KEYS[k.upper()] for k in keys.replace('|','+').split('+'))
class Emulator:
    def __init__(self,rom):
        self.lib=C.CDLL(str(HERE/'mgba_bridge.so'))
        for name,args,rest in [
            ('eb_open',[C.c_char_p],C.c_void_p),('eb_close',[C.c_void_p],None),
            ('eb_frames',[C.c_void_p,C.c_uint,C.c_uint],None),
            ('eb_read',[C.c_void_p,C.c_uint32,C.c_uint],C.c_uint32),
            ('eb_write',[C.c_void_p,C.c_uint32,C.c_uint32,C.c_uint],None),
            ('eb_rgb',[C.c_void_p,C.c_void_p],None),('eb_framecounter',[C.c_void_p],C.c_uint),
            ('eb_reset',[C.c_void_p],None),('eb_load_save',[C.c_void_p,C.c_char_p],C.c_int),
            ('eb_state',[C.c_void_p,C.c_char_p,C.c_int],C.c_int),
            ('eb_audio_start',[C.c_void_p,C.c_char_p],C.c_int),('eb_audio_stop',[C.c_void_p],C.c_uint)]:
            f=getattr(self.lib,name);f.argtypes=args;f.restype=rest
        self.ptr=self.lib.eb_open(str(Path(rom).resolve()).encode())
        if not self.ptr:raise RuntimeError(f'mGBA could not open ROM: {rom}')
    def close(self):
        if self.ptr:self.lib.eb_close(self.ptr);self.ptr=None
    def __enter__(self):return self
    def __exit__(self,*args):self.close()
    def frames(self,n,keys=0):self.lib.eb_frames(self.ptr,int(n),keymask(keys))
    def tap(self,key,hold=1,release=1):self.frames(hold,key);self.frames(release,0)
    def read(self,address,width=4):return self.lib.eb_read(self.ptr,address,width)
    def write(self,address,value,width=4):self.lib.eb_write(self.ptr,address,value,width)
    def bytes(self,address,length):return bytes(self.read(address+i,1) for i in range(length))
    def screenshot(self,path=None):
        pixels=(C.c_uint8*(240*160*3))();self.lib.eb_rgb(self.ptr,pixels)
        image=Image.frombytes('RGB',(240,160),bytes(pixels))
        if path:image.save(path)
        return image
    @property
    def frame(self):return self.lib.eb_framecounter(self.ptr)
    def reset(self):self.lib.eb_reset(self.ptr)
    def load_save(self,path):
        if not self.lib.eb_load_save(self.ptr,str(path).encode()):raise RuntimeError('Cannot load save')
    def audio_start(self,path):
        if not self.lib.eb_audio_start(self.ptr,str(path).encode()):raise RuntimeError("Cannot start WAV capture")
    def audio_stop(self):return self.lib.eb_audio_stop(self.ptr)
    def state(self,path,load=False):
        if not self.lib.eb_state(self.ptr,str(path).encode(),int(load)):raise RuntimeError('Cannot read/write state')

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('rom');p.add_argument('--script',help='command file (otherwise read stdin)')
    p.add_argument('--frames',type=int,default=0);p.add_argument('--shot');p.add_argument('--save');p.add_argument('--audio')
    args=p.parse_args()
    with Emulator(args.rom) as emu:
        if args.audio:emu.audio_start(args.audio)
        if args.save:emu.load_save(args.save);emu.reset()
        if args.frames:emu.frames(args.frames)
        if args.shot:emu.screenshot(args.shot)
        if args.script:lines=Path(args.script).read_text().splitlines()
        elif not args.frames and not args.shot:lines=sys.stdin
        else:lines=[]
        for line in lines:
            tokens=shlex.split(line,comments=True)
            if not tokens:continue
            cmd,*v=tokens
            if cmd in ('frames','frame'):emu.frames(int(v[0],0),v[1] if len(v)>1 else 0)
            elif cmd=='tap':emu.tap(v[0],int(v[1]) if len(v)>1 else 1,int(v[2]) if len(v)>2 else 1)
            elif cmd in ('shot','screenshot'):emu.screenshot(v[0]);print(json.dumps({'screenshot':v[0],'frame':emu.frame}))
            elif cmd=='read':
                address=int(v[0],0);width=int(v[1],0) if len(v)>1 else 4;count=int(v[2],0) if len(v)>2 else 1
                print(json.dumps({'frame':emu.frame,'address':hex(address),'width':width,'values':[emu.read(address+i*width,width) for i in range(count)]}))
            elif cmd=='dump':Path(v[2]).write_bytes(emu.bytes(int(v[0],0),int(v[1],0)))
            elif cmd=='write':emu.write(int(v[0],0),int(v[1],0),int(v[2],0) if len(v)>2 else 4)
            elif cmd=='state':emu.state(v[0])
            elif cmd=='loadstate':emu.state(v[0],True)
            elif cmd=='reset':emu.reset()
            elif cmd=='audio':emu.audio_start(v[0])
            elif cmd=='stopaudio':print(json.dumps({'audio_samples':emu.audio_stop()}))
            else:raise ValueError(f'Unknown command: {cmd}')
if __name__=='__main__':main()
