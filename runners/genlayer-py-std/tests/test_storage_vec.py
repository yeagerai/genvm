from genlayer.py._storage import Vec, storage

import common

@storage
class StorVec:
	x: Vec[str]

def same_iter(li, ri):
	for l, r in zip(li, ri):
		assert l == r

def test_len():
	l = StorVec()
	r: list[str] = []
	op = common.SameOp(l.x, r)
	same_iter(l.x, r)
	op(len)
	op(lambda x: x.append('123'))
	op(len)
	op(lambda x: x[0])
	op(lambda x: x[-1])
	same_iter(l.x, r)
	for i in range(5):
		op(str(i))
	same_iter(l.x, r)
	while len(r) > 0:
		op(lambda x: x.pop(), void=True)
		same_iter(l.x, r)