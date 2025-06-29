# { "Depends": "py-genlayer:test" }
from genlayer import *


class Contract(gl.Contract):
	@gl.public.write
	def main(self, addr: Address):
		print('contract from.main')
		try:
			res = gl.get_contract_at(addr).view().foo(1, 2).get()
		except gl.vm.UserError as r:
			print('handled', r.message)
		else:
			print(res)
			exit(1)
