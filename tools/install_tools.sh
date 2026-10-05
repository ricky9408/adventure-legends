#!/bin/sh
# Reproduce the cloud Linux x86_64 tool extraction without root/system changes.
set -eu
HERE=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
cd "$HERE"
mkdir -p downloads sysroot
fetch() {
  file=$1; path=$2; checksum=$3
  if ! test -f "downloads/$file"; then
    curl -fL --connect-timeout 60 --max-time 240 "https://deb.debian.org/debian/pool/main/$path" -o "downloads/$file"
  fi
  echo "$checksum  downloads/$file" | sha256sum -c -
  dpkg-deb -x "downloads/$file" sysroot
}
fetch gcc-arm-none-eabi.deb g/gcc-arm-none-eabi/gcc-arm-none-eabi_14.2.rel1-1_amd64.deb 99252fdda02ad134e8c3c344d3c843f7aa5c0d006e92a5b3d53daf4bd935b5d3
fetch binutils-arm-none-eabi.deb b/binutils-arm-none-eabi/binutils-arm-none-eabi_2.44-3+23+b1_amd64.deb c9c4944e54de852536b4f6a238a682c38a6243cdc2843dd1c4f587e046c0615b
fetch libmgba-dev.deb m/mgba/libmgba-dev_0.10.5+dfsg-1_amd64.deb 35366aa94d519b34dbfd68cd58f252d775be992a4f1a0edefdd5317efb10c467
fetch libmgba.deb m/mgba/libmgba0.10t64_0.10.5+dfsg-1_amd64.deb d7a5f25a9d14a70ef90c2be6422d024fd351c696404dc534133b8c339098a1ba
./build_mgba_bridge.sh
printf '\nReady: %s/sysroot/usr/bin/arm-none-eabi-gcc\n' "$HERE"
