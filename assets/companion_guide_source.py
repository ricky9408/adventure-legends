"""Read the explicit, hash-pinned companion-copy source manifest."""
from pathlib import Path
import hashlib,json

def load_commands(root=None):
 root=Path(root) if root else Path(__file__).resolve().parents[1]
 manifest=json.loads((root/'assets/companion_guide_commands.json').read_text())
 assert manifest['format']=='companion-guide-commands-v1' and manifest['command_count']==128
 commands=[]
 for part in manifest['parts']:
  path=root/'assets'/part['path'];raw=path.read_bytes()
  assert hashlib.sha256(raw).hexdigest()==part['sha256'],str(path)
  rows=json.loads(raw)['commands'];assert 1<=len(rows)<=32
  assert [c['id'] for c in rows]==list(range(part['first_id'],part['last_id']+1))
  commands.extend(rows)
 assert [c['id'] for c in commands]==list(range(1,129))
 return commands
