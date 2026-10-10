#!/bin/sh
# Build a tiny native interface to mGBA 0.10.x. Prefer isolated workspace tools;
# otherwise use a system libmgba development installation (pkg-config optional).
set -eu
HERE=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
CC=${HOST_CC:-cc}
OUTPUT="$HERE/horizons_mgba_bridge.so.tmp.$$"
trap 'rm -f "$OUTPUT"' EXIT HUP INT TERM
if [ "$(uname -s)" = Darwin ]; then
  SHARED=-dynamiclib
  ORIGIN=@loader_path
else
  SHARED=-shared
  ORIGIN='$ORIGIN'
fi
if [ -f "$HERE/sysroot/usr/include/mgba/core/core.h" ] && [ -f "$HERE/sysroot/usr/lib/x86_64-linux-gnu/libmgba.so" ]; then
  "$CC" -std=c11 -D_GNU_SOURCE -O2 -fPIC -MD -MF "$HERE/horizons_mgba_bridge.d" "$SHARED" "$HERE/horizons_mgba_bridge.c" \
    -I"$HERE/sysroot/usr/include" -L"$HERE/sysroot/usr/lib/x86_64-linux-gnu" \
    -Wl,-rpath,"$ORIGIN/sysroot/usr/lib/x86_64-linux-gnu" \
    -o "$OUTPUT" -lmgba
elif command -v pkg-config >/dev/null 2>&1 && pkg-config --exists mgba; then
  # Deliberate splitting: pkg-config emits a compiler argument list.
  # shellcheck disable=SC2046
  "$CC" -std=c11 -D_GNU_SOURCE -O2 -fPIC -MD -MF "$HERE/horizons_mgba_bridge.d" "$SHARED" "$HERE/horizons_mgba_bridge.c" \
    $(pkg-config --cflags --libs mgba) -o "$OUTPUT"
elif command -v pkg-config >/dev/null 2>&1 && pkg-config --exists libmgba; then
  # shellcheck disable=SC2046
  "$CC" -std=c11 -D_GNU_SOURCE -O2 -fPIC -MD -MF "$HERE/horizons_mgba_bridge.d" "$SHARED" "$HERE/horizons_mgba_bridge.c" \
    $(pkg-config --cflags --libs libmgba) -o "$OUTPUT"
else
  # Debian's libmgba-dev can expose standard include/library locations without
  # a .pc file. A normal linker invocation supports that arrangement.
  "$CC" -std=c11 -D_GNU_SOURCE -O2 -fPIC -MD -MF "$HERE/horizons_mgba_bridge.d" "$SHARED" "$HERE/horizons_mgba_bridge.c" \
    -o "$OUTPUT" -lmgba
fi

mv -f "$OUTPUT" "$HERE/horizons_mgba_bridge.so"

python3 - "$HERE" "$CC" <<'RECEIPT'
import hashlib,json,pathlib,shlex,subprocess,sys
root=pathlib.Path(sys.argv[1]);sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
raw=(root/'horizons_mgba_bridge.d').read_text().replace(chr(92)+chr(10),' ')
paths=[pathlib.Path(x).resolve() for x in shlex.split(raw.split(':',1)[1])]
receipt={'bridge_sha256':sha(root/'horizons_mgba_bridge.so'),'source_sha256':sha(root/'horizons_mgba_bridge.c'),'compiler':subprocess.check_output([sys.argv[2],'--version'],text=True).splitlines()[0],'compiler_dependencies':{str(p):sha(p) for p in paths if p.is_file()}}
(root/'horizons_mgba_bridge.build.json').write_text(json.dumps(receipt,indent=2)+'\n')
RECEIPT
