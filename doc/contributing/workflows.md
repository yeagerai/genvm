# Common workflows

## Adding new LLM provider
**IMPORTANT**: If your provider is compatible with openai API no additional work is needed

- go to [`executor/modules/implementation/llm-funcs/src/lib.rs`](../../executor/modules/implementation/llm-funcs/src/lib.rs)
- add new value to `enum LLLMProvider`
- add case to `exec_prompt_impl`<br>
    **IMPORTANT**: you must implement it for both text and json modes

### Adding test
- add test case to [`executor/modules/implementation/llm-funcs/src/lib.rs`](../../executor/modules/implementation/llm-funcs/src/lib.rs)
- patch [workflow](../../.github/workflows/module-test-cargo.yaml) to pass secret
- provide api key to repository owners

## Adding new wasm function
- `executor/src/wasi/witx/genlayer_sdk.witx`<br>
    add declaration here
- `executor/src/wasi/genlayer_sdk.rs`<br>
    add implementation here (under `impl` trait)
- `runners/cpython-and-ext/extension/src/lib.rs`<br>
    add python proxy<br>
    NOTE: this will change hash, rebuilding will show you the new one

## Adding new host function

- `executor/codegen/data/host-fns.json`<br>
    add new function id<br>
    after rebuilding (`tags/codegen`) few files will be updated:
    - `executor/src/host/host_fns.rs`
    - `executor/testdata/runner/host_fns.py`
- `executor/testdata/runner/base_host.py`<br>
    update `while True` to handle new case, add new method to the `IHost` protocol<br>
    NOTE: this file is used in simulator as well (under `backend/node/genvm/origin/`)
- `executor/testdata/runner/mock_host.py`<br>
    add implementation for tests
- update simulator and node
