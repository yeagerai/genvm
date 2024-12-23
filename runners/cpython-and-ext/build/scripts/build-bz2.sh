#!/usr/bin/env bash
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
source "$SCRIPT_DIR/common.sh"

cd /opt/bzip2-1.0.8

C_AND_CXX_FLAGS="-O3 --sysroot=/opt/host-root/share/wasi-sysroot --target=wasm32-wasi -fPIC"
make CC=/opt/host-root/bin/clang CFLAGS="$C_AND_CXX_FLAGS" -j libbz2.a

cp -f libbz2.a "$WASM32_WASI_ROOT/lib/libbz2.a"
cp -f bzlib.h "$WASM32_WASI_ROOT/include"
chmod a+r "$WASM32_WASI_ROOT/include/bzlib.h"

make clean || true
