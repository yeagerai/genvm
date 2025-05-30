from genlayer.py.types import Address
import abc

from .core import *


class BoolDesc(TypeDesc):
	__slots__ = ()

	def __init__(self):
		TypeDesc.__init__(self, 1, [1])

	def get(self, slot: Slot, off: int) -> bool:
		return slot.read(off, 1)[0] != 0

	def set(self, slot: Slot, off: int, val: bool):
		slot.write(off, bytes([1 if val else 0]))

	def __repr__(self):
		return '_BoolDesc'


class IntDesc(TypeDesc):
	__slots__ = ('signed',)

	def __init__(self, size: int, signed=True):
		TypeDesc.__init__(self, size, [size])
		self.signed = signed

	def get(self, slot: Slot, off: int) -> int:
		return int.from_bytes(
			slot.read(off, self.size), byteorder='little', signed=self.signed
		)

	def set(self, slot: Slot, off: int, val: int):
		slot.write(
			off, memoryview(val.to_bytes(self.size, byteorder='little', signed=self.signed))
		)

	def __repr__(self):
		return f"_IntDesc[{self.size}, {"" if self.signed else "un"}signed]"

	def __eq__(self, r):
		if not isinstance(r, IntDesc):
			return False
		return self.size == r.size and self.signed == r.signed

	def __hash__(self):
		return hash(('_IntDesc', self.size, self.signed))


class NoneDesc(TypeDesc[None]):
	__slots__ = ()

	def __init__(self):
		TypeDesc.__init__(self, 0, [0])

	def get(self, slot: Slot, off: int) -> None:
		return

	def set(self, slot: Slot, off: int, val: None):
		pass

	def __repr__(self):
		return f'_NoneDesc'

	def __eq__(self, r):
		return isinstance(r, NoneDesc)

	def __hash__(self):
		return hash('_NoneDesc')


_u8_desc = IntDesc(1, signed=False)
_u32_desc = IntDesc(4, signed=False)


class AddrDesc(TypeDesc):
	__slots__ = ()

	def __init__(self):
		TypeDesc.__init__(self, Address.SIZE, [Address.SIZE])

	def get(self, slot: Slot, off: int) -> Address:
		return Address(slot.read(off, self.size))

	def set(self, slot: Slot, off: int, val: Address):
		slot.write(off, memoryview(val.as_bytes))

	def __repr__(self):
		return '_AddrDesc'


class _CopyStrBytesAction(ComplexCopyAction):
	__slots__ = ()

	def __init__(self):
		pass

	def copy(self, frm: Slot, frm_off: int, to: Slot, to_off: int) -> int:
		frm_stor = frm.indirect(frm_off)
		to_stor = to.indirect(to_off)
		le = _u32_desc.get(frm, frm_off)
		_u32_desc.set(to, to_off, le)
		to_stor.write(0, frm_stor.read(0, le))

		return _u32_desc.size

	def __repr__(self):
		return '_CopyStrBytesAction'


class _StrBytesDesc[T](TypeDesc):
	__slots__ = ()

	def __init__(self):
		TypeDesc.__init__(self, _u32_desc.size, [_CopyStrBytesAction()])

	@abc.abstractmethod
	def decode(self, val: collections.abc.Buffer) -> T:
		raise NotImplementedError()

	@abc.abstractmethod
	def encode(self, val: T) -> memoryview:
		raise NotImplementedError()

	def get(self, slot: Slot, off: int) -> T:
		le = _u32_desc.get(slot, off)
		contents_at = slot.indirect(off)
		return self.decode(contents_at.read(0, le))

	def set(self, slot: Slot, off: int, val: T):
		contents_at = slot.indirect(off)
		enc = self.encode(val)
		_u32_desc.set(slot, off, len(enc))
		contents_at.write(0, enc)

	def __eq__(self, r):
		return isinstance(r, type(self))

	def __hash__(self):
		return hash(type(self).__name__)


class StrDesc(_StrBytesDesc[str]):
	__slots__ = ()

	def __init__(self):
		_StrBytesDesc.__init__(self)

	def decode(self, val: collections.abc.Buffer) -> str:
		return str(val, encoding='utf-8')

	def encode(self, val: str) -> memoryview:
		return memoryview(val.encode())

	def __repr__(self):
		return '_StrDesc'


class BytesDesc(_StrBytesDesc[bytes]):
	__slots__ = ()

	def __init__(self):
		_StrBytesDesc.__init__(self)

	def decode(self, val: collections.abc.Buffer) -> bytes:
		return bytes(val)

	def encode(self, val: bytes) -> memoryview:
		return memoryview(val)

	def __repr__(self):
		return '_BytesDesc'


class _BigIntDesc(_StrBytesDesc[int]):
	__slots__ = ()

	def __init__(self):
		_StrBytesDesc.__init__(self)

	def decode(self, val: collections.abc.Buffer) -> int:
		return int.from_bytes(val, 'little', signed=True)

	def encode(self, val: int) -> memoryview:
		val_abs = abs(val)
		log256 = 2
		while val_abs > 0:
			log256 += 1
			val_abs //= 256
		return memoryview(val.to_bytes(log256, 'little', signed=True))

	def __repr__(self):
		return '_BigIntDesc'
