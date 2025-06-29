import typing
from functools import partial

from genlayer.py.types import Address, u256

from genlayer.py.evm.calldata import MethodEncoder
import genlayer.py.evm as genvm_eth


def generate_test(
	name: str, params: tuple[type], ret: type, *, dump_to: list
) -> typing.Any:
	encoder = MethodEncoder(name, params, ret)

	def result_fn(self, *args):
		dump_to.append(self._proxy_parent.address)
		dump_to.append(encoder.encode_call(args))

	return result_fn


def test_view_send():
	tst = []
	generator = partial(generate_test, dump_to=tst)

	@genvm_eth.contract_generator(
		generate_view=generator,
		generate_send=generator,
		balance_getter=lambda x: u256(0),
		transfer=lambda p, d: None,
	)
	class MyContract:
		class View:
			def foo(self, param: str, /): ...

		class Write:
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
	contr.emit().bar('abc')
	assert tst == [
		addr,
		b'\xd4s\xa8\xed\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00 \x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x03abc\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00',
	]
