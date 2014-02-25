#[[[cog
#	import cog
#]]]
#[[[end]]] (checksum: d41d8cd98f00b204e9800998ecf8427e)

import mozz.err
import mozz.prototype.int
import mozz.abi.endian
import mozz.location
import struct

class ValueBase(object):

	def __init__(self, endian, getter, setter):
		self._endian = endian
		self._getter = getter
		self._setter = setter

	def data(self):
		'''
		the data in native endian format
		'''
		return self._getter()

	def set_data(self, data):
		'''
		set the underlying machine location to
		data, where data is in native endian
		format
		'''
		self._setter(data)

	def endian(self):
		return self._endian

	def value(self, *args, **kwargs):
		raise Exception("not implemented")

	@staticmethod
	def size():
		raise Exception("not implemented")

	def __len__(self):
		return self.__class__.size()

	@staticmethod
	def has_static_size():
		return False

class StaticSizeValue(object):
	@staticmethod
	def has_static_size():
		return True

class Int(ValueBase):
	def signed(self):
		raise Exception("not implemented")

	def value(self, *args, **kwargs):
		size = self.__class__.size()
		kwargs['endian'] = self.endian()

		if self.signed():
			kwargs['fmt'] = mozz.prototype.int.TwosComplementSigned
		else:
			kwargs['fmt'] = mozz.prototype.int.TwosComplementUnsigned

		data = self.data()
		real_data = self.endian().truncate(size, data)
		kwargs['size'] = size

		return mozz.prototype.int.to_int(
			real_data, *args, **kwargs
		)
		
#[[[cog
#	tc_int_class_macro = '''
#	class TCInt%d(StaticSizeValue, Int):
#		@staticmethod
#		def size():
#			return %d
#
#		def signed(self):
#			return True
#
#	class TCUInt%d(StaticSizeValue, Int):
#		@staticmethod
#		def size():
#			return %d
#
#		def signed(self):
#			return False
#	'''
#]]]
#[[[end]]] (checksum: d41d8cd98f00b204e9800998ecf8427e)

#[[[cog
#	for sz in [8, 16, 32, 64]:
#		cog.outl(tc_int_class_macro % (sz, sz, sz, sz))
#]]]

class TCInt8(StaticSizeValue, Int):
	@staticmethod
	def size():
		return 8

	def signed(self):
		return True

class TCUInt8(StaticSizeValue, Int):
	@staticmethod
	def size():
		return 8

	def signed(self):
		return False


class TCInt16(StaticSizeValue, Int):
	@staticmethod
	def size():
		return 16

	def signed(self):
		return True

class TCUInt16(StaticSizeValue, Int):
	@staticmethod
	def size():
		return 16

	def signed(self):
		return False


class TCInt32(StaticSizeValue, Int):
	@staticmethod
	def size():
		return 32

	def signed(self):
		return True

class TCUInt32(StaticSizeValue, Int):
	@staticmethod
	def size():
		return 32

	def signed(self):
		return False


class TCInt64(StaticSizeValue, Int):
	@staticmethod
	def size():
		return 64

	def signed(self):
		return True

class TCUInt64(StaticSizeValue, Int):
	@staticmethod
	def size():
		return 64

	def signed(self):
		return False

#[[[end]]] (checksum: 2b392bd0b42d58615738ca090adb11d6)

class Pointer(ValueBase):
	def __init__(self, endian, getter, setter):
		super(Pointer, self).__init__(endian, getter, setter)

	def value(self, *args, **kwargs):
		kwargs['size'] = self.__class__.size()
		kwargs['endian'] = self.endian()
		kwargs['fmt'] = mozz.prototype.int.TwosComplementUnsigned
		return mozz.prototype.int.to_int(
			self.data(), *args, **kwargs
		)

	def string(self, host):
		'''
		dereference pointer and return null terminated
		string at the pointer value
		'''
		start = self.value()
		offset = 0
		bs = []
		def current_byte():
			return host.inferior().mem_read_uint8(start+offset)

		b = current_byte()
		while(b != 0):
			bs.append(b)
			offset += 1
			b = current_byte()

		if len(bs) < 1:
			return ""

		fmt = "%db" % len(bs)
		return struct.pack(fmt, *bs)

	def deref(self, host, typ):
		ml = mozz.location.Absolute(self.value(), typ.size())
		v = ml.value()
		getter = lambda: v
		setter = lambda data: ml.set(host, data)
		return typ(self.endian(), getter, setter)

#[[[cog
#	pointer_class_macro = '''
#	class Pointer%d(StaticSizeValue, Pointer):
#		@staticmethod
#		def size():
#			return %d
#	'''
#]]]
#[[[end]]] (checksum: d41d8cd98f00b204e9800998ecf8427e)

#[[[cog
#	for sz in [8, 16, 32, 64]:
#		cog.outl(pointer_class_macro % (sz, sz))
#]]]

class Pointer8(StaticSizeValue, Pointer):
	@staticmethod
	def size():
		return 8


class Pointer16(StaticSizeValue, Pointer):
	@staticmethod
	def size():
		return 16


class Pointer32(StaticSizeValue, Pointer):
	@staticmethod
	def size():
		return 32


class Pointer64(StaticSizeValue, Pointer):
	@staticmethod
	def size():
		return 64

#[[[end]]] (checksum: dd423d61b3361861e97d697a2ed4344b)
