# { "Depends": "py-genlayer:test" }

from genlayer import *

import typing


class Contract(gl.Contract):
	@gl.public.write.payable
	def __handle_undefined_method__(
		self, method_name: str, args: list[typing.Any], kwargs: dict[str, typing.Any]
	):
		print(
			{
				'me': '__handle_undefined_method__',
				'method_name': method_name,
				'args': args,
				'kwargs': kwargs,
				'value': gl.message.value,
			}
		)
