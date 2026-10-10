#!/usr/bin/env python3
"""Private development recovery archive, distinct from accepted release files."""
import argparse,hashlib,json,zipfile
from pathlib import Path
from package_source import ROOT,source_files
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--candidate',type=Path,required=True);a=ap.parse_args()
 candidate=a.candidate.resolve();metadata=json.loads((candidate/'candidate.json').read_text());runtime=json.loads((candidate/'source-hashes.json').read_text())
 assert all(sha(ROOT/name)==h for name,h in runtime.items()),'Build must match checkpoint runtime source'
 files=source_files()+[ROOT/'DEVELOPMENT_STATUS.md'];files=sorted(set(files),key=lambda p:p.relative_to(ROOT).as_posix())
 out=ROOT/'dist';out.mkdir(exist_ok=True);target=out/'Adventure-Legends-Feedback-development-checkpoint.zip'
 receipt={'status':'DEVELOPMENT RECOVERY ONLY; NOT AN ACCEPTED RELEASE','candidate':metadata,'runtime_manifest_sha256':sha(candidate/'source-hashes.json'),'pending':['full candidate native and host aggregate','earned main journey through final homecoming','save and performance regressions','independent final review','exact exported regeneration/rebuild'],'files':[]}
 with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
  for p in files:
   content=p.read_bytes();rel=p.relative_to(ROOT).as_posix();digest=hashlib.sha256(content).hexdigest()
   if rel in runtime:assert digest==runtime[rel],rel
   row={'path':rel,'bytes':len(content),'sha256':digest};receipt['files'].append(row)
   info=zipfile.ZipInfo('Adventure-Legends-Emberbond/'+rel,(2026,10,7,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;info.external_attr=(0o755 if p.suffix=='.sh' else 0o644)<<16;z.writestr(info,content)
  for name in ['candidate.json','source-hashes.json']:
   z.writestr('Adventure-Legends-Emberbond/development-build/'+name,(candidate/name).read_bytes())
 assert all(sha(ROOT/name)==h for name,h in runtime.items()),'Runtime changed while checkpointing'
 receipt['archive']={'path':str(target),'bytes':target.stat().st_size,'sha256':sha(target)}
 (out/'journey-guidance-checkpoint-package.json').write_text(json.dumps(receipt,indent=2)+'\n')
 print(json.dumps(receipt['archive']))
if __name__=='__main__':main()
