import typing
from functools import partial

from genlayer.py.types import Address

from genlayer.py.eth.calldata import MethodEncoder
import genlayer.py.eth as genvm_eth


def generate_test(
	name: str, params: list[type], ret: type, *, dump_to: list
) -> typing.Any:
	encoder = MethodEncoder(name, params, ret)

	def result_fn(self, *args):
		dump_to.append(self.parent.address)
		dump_to.append(encoder.encode(list(args)))

	return result_fn


def test_view_send():
	tst = []
	generator = partial(generate_test, dump_to=tst)

	@genvm_eth.contract_generator(generate_view=generator, generate_send=generator)
	class MyContract:
		class View:
			def foo(self, param: str, /): ...

		class Send:
			def bar(self, param: str, /): ...

	addr = Address(b'\x00' * 20)
	contr = MyContract(addr)
	assert tst == []
	contr.view().foo('123')
	assert tst == [
		addr,
		b'\xf3\x1aii\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00 \x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x03123\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00',
	]

	tst.clear()
	contr.send().bar('abc')
	assert tst == [
		addr,
		b'\xd4s\xa8\xed\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00 \x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x03abc\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00',
	]