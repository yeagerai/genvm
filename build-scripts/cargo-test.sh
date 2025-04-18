#!/usr/bin/env bash

set -ex

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

cd "$SCRIPT_DIR/.."

for dir in $(git ls-files | grep -P 'Cargo\.toml')
do
    pushd "$(dirname -- $dir)" 2> /dev/null > /dev/null
    if test -d "tests"
    then
        echo "=== testing $dir ==="
        cargo test --target-dir "$SCRIPT_DIR/../build/generated/rust-target" --tests
    fi
    popd  2> /dev/null > /dev/null
done
