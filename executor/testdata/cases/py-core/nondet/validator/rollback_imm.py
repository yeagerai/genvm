# { "Depends": "py-genlayer:test" }
from genlayer import *


class Contract(gl.Contract):
	@gl.public.write
	def main(self):
		def run():
			gl.advanced.user_error_immediate('rollback')

		print(gl.eq_principle.strict_eq(run))
