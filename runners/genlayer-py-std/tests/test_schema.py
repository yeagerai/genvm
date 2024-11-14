from genlayer.py.get_schema import get_schema

import typing


def public(f):
	f.__public__ = True
	return f


def public_view(f):
	f.__public__ = True
	f.__readonly__ = True
	return f


class A:
	def __init__(self, x: int, *, y: str): ...

	@public
	def foo(self, x: dict, *, y: list): ...

	@public_view
	def foo_bar(self, x: dict[str, int], *, y: list[list[int]]): ...

	@public_view
	def an(self, x: typing.Any): ...


def test_schema():
	print(get_schema(A))
	assert get_schema(A) == {
		'ctor': {'params': [['x', 'int']], 'kwparams': {'y': 'string'}},
		'methods': {
			'an': {'params': [['x', 'any']], 'kwparams': {}, 'readonly': True, 'ret': 'any'},
			'foo': {
				'params': [['x', 'dict']],
				'kwparams': {'y': 'array'},
				'readonly': False,
				'ret': 'any',
			},
			'foo_bar': {
				'params': [['x', {'$dict': 'int'}]],
				'kwparams': {'y': [{'$rep': [{'$rep': 'int'}]}]},
				'readonly': True,
				'ret': 'any',
			},
		},
	}