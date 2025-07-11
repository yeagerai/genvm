# { "Depends": "py-genlayer:test" }
from genlayer import *


class Contract(gl.Contract):
	@gl.public.write
	def foo(self):
		def do_fn():
			raise Exception()

		gl.eq_principle.strict_eq(do_fn)

	@gl.public.write
	def bar(self):
		def do_fn():
			return

		gl.eq_principle.strict_eq(do_fn)

	@gl.public.write
	def ex(self):
		def do_fn():
			exit(2)

		gl.eq_principle.strict_eq(do_fn)

	@gl.public.write
	def ex2(self):
		def do_fn():
			non_existent_fn()  # noqa

		gl.eq_principle.strict_eq(do_fn)
