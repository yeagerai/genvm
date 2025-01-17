"""
Module that is used to run python contracts in the default way
"""

__all__ = ('run',)

import typing

import genlayer.std._wasi as wasi
import genlayer.py.calldata

from ..py.types import Rollback
from ..py.storage._internal.generate import _known_descs


def _give_result(res_fn: typing.Callable[[], typing.Any]):
	try:
		res = res_fn()
	except Rollback as r:
		wasi.rollback(r.msg)
	from .advanced import AlreadySerializedResult

	if isinstance(res, AlreadySerializedResult):
		wasi.contract_return(res)
	else:
		wasi.contract_return(genlayer.py.calldata.encode(res))


def _is_public(meth) -> bool:
	if meth is None:
		return False
	return getattr(meth, '__public__', False)


def run(mod):
	"""
	:param mod: module that contains a contract
	"""
	contract: type = getattr(mod, '__KNOWN_CONTRACT')
	entrypoint: bytes = wasi.get_entrypoint()
	mem = memoryview(entrypoint)
	CALL = b'call!'
	NONDET = b'nondet!'
	SANDBOX = b'sandbox!'
	if entrypoint.startswith(CALL):
		mem = mem[len(CALL) :]
		calldata = genlayer.py.calldata.decode(mem)
		from . import message

		if message.is_init:
			meth = getattr(contract, '__init__')
			if _is_public(meth):
				raise Exception(f'constructor must be private')
		else:
			meth_name = calldata['method']
			if meth_name == '__get_schema__':
				if hasattr(contract, '__get_schema__'):
					_give_result(contract.__get_schema__)
					return

				from ..py.get_schema import get_schema
				import json

				_give_result(lambda: json.dumps(get_schema(contract), separators=(',', ':')))
				return
			meth = getattr(contract, meth_name)
			if not _is_public(meth):
				raise Exception(f"can't call non-public methods")
		from ._internal.storage import STORAGE_MAN, ROOT_STORAGE_ADDRESS

		top_slot = STORAGE_MAN.get_store_slot(ROOT_STORAGE_ADDRESS)
		contract_instance = _known_descs[contract].get(top_slot, 0)
		_give_result(
			lambda: meth(
				contract_instance, *calldata.get('args', []), **calldata.get('kwargs', {})
			)
		)
	elif entrypoint.startswith(NONDET):
		mem = mem[len(NONDET) :]
		# fetch leaders result length
		le = int.from_bytes(mem[:4], 'little')
		mem = mem[4:]

		leaders_res_mem = mem[:le]
		mem = mem[le:]
		import cloudpickle

		runner = cloudpickle.loads(mem)
		if le == 0:
			_give_result(runner)
		else:
			from ._internal import decode_sub_vm_result_retn

			leaders_res = decode_sub_vm_result_retn(leaders_res_mem)
			_give_result(lambda: runner(leaders_res))
	elif entrypoint.startswith(SANDBOX):
		mem = mem[len(SANDBOX) :]
		import cloudpickle

		runner = cloudpickle.loads(mem)
		_give_result(runner)
	else:
		raise Exception(f'unknown entrypoint {entrypoint}')
