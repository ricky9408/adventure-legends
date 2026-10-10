#!/usr/bin/env python3
"""Shop/pause experience assertions with explicit economy boundary doubles."""
from pathlib import Path
import os,subprocess,tempfile
ROOT=Path(__file__).resolve().parents[1]
def main():
 with tempfile.TemporaryDirectory(prefix='shop-experience-') as tmp:
  for name,flags in [('strict',[]),('sanitized',['-fsanitize=address,undefined','-fno-omit-frame-pointer'])]:
   target=Path(tmp)/name
   subprocess.run([os.environ.get('HOST_CC','cc'),'-std=c99','-O1','-g','-Wall','-Wextra','-Werror','-Wno-attributes','-Wno-misleading-indentation','-Isrc',*flags,'tests/shop_experience_host.c','src/game_shop.c','src/ui.c','src/treasure_text_text.c','-o',str(target)],cwd=ROOT,check=True)
   subprocess.run([str(target)],cwd=ROOT,env=dict(os.environ,ASAN_OPTIONS='detect_leaks=0'),check=True)
if __name__=='__main__':main()
