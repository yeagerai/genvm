# { "depends": ["genvm-rustpython:test"] }
import genlayer.sdk as gsdk

@gsdk.public
def foo(a, b):
    print('contract to.foo')
    import json
    json.loads = 11 # evil!
    return a + b