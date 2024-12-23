#!/usr/bin/env bash
set -ex

cd /opt/openssl-3.3.2

patch -p1 <"/scripts/openssl.patch"

C_AND_CXX_FLAGS="-O3 --sysroot=/opt/host-root/share/wasi-sysroot -DOPENSSL_NO_SECURE_MEMORY -DNO_SYSLOG -Dgetuid=getpagesize -Dgeteuid=getpagesize -Dgetgid=getpagesize -Dgetegid=getpagesize"

env \
    CC=/opt/host-root/bin/clang \
    CXX=/opt/host-root/bin/clang++ \
    CFLAGS="$C_AND_CXX_FLAGS" \
    CXXFLAGS="$C_AND_CXX_FLAGS" \
    ./Configure \
        "--prefix=$WASM32_WASI_ROOT" \
        no-asm no-async no-posix-io no-shared no-sock no-stdio no-threads no-ui-console no-secure-memory \
        wasm32-wasi

# no-apps

# no-asm no-async no-egd no-posix-io no-shared no-sock no-stdio no-threads no-ui-console no-weak-ssl-ciphers wasm32-wasi

make -j

make install_sw install_ssldirs
make clean || true
