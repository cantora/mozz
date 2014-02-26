import struct
import mozz.util

class Base(object):
	def size(self):
		raise Exception("not implemented")

	def value(self, host):
		'''
		return value at location in native endian format
		'''
		raise Exception("not implemented")

	def set(self, host, data):
		raise Exception("not implemented")

class Register(Base):
	def __init__(self, name, size):
		self._name = name
		self._size = size

	def name(self):
		return self._name

	def size(self):
		return self._size

	def value(self, host):
		v = host.inferior().reg(self._name)
		endian = host.session.endian()
		fmt = mozz.util.size_to_struct_fmt(self.size())
		if not fmt:
			raise Exception("invalid register size %d" % self._size)
		data = struct.pack("%s%s" % (endian.format(), fmt), v)
		return data

	def set(self, host, data):
		endian = host.session.endian()
		sz = len(data) << 3
		fmt = mozz.util.size_to_struct_fmt(sz).upper()
		if not fmt:
			raise Exception("invalid register size %d" % sz)
		unpack_fmt = "%s%s" % (endian.format(), fmt)
		v = struct.unpack(unpack_fmt, data[0:self._size])[0]
		host.inferior().reg_set(self._name, v)

class Memory(Base):
	def value(self, host):
		addr = self.addr(host)
		byte_size = self.size() >> 3
		#returns data in native endian format
		return host.inferior().mem_read_buf(addr, byte_size)

	def set(self, host, data):
		addr = self.addr(host)
		byte_size = self.size() >> 3
		#returns data in native endian format
		return host.inferior().mem_write_buf(addr, data[0:byte_size])

class StackOffset(Memory):
	def __init__(self, offset, size, stack_grows_down=True):
		self._offset = offset
		self._size = size
		self._stack_grows_down = stack_grows_down

	def size(self):
		return self._size

	def addr(self, host):
		sp = host.inferior().reg_sp()
		if self._stack_grows_down:
			addr = sp+self._offset
		else:
			addr = sp-self._offset
		return addr

class Absolute(Memory):
	def __init__(self, addr, size):
		self._addr = addr
		self._size = size

	def size(self):
		return self._size

	def addr(self, host):
		return self._addr
