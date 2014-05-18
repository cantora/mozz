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
		'''
		specify size in bits
		'''
		self._name = name
		self._size = size # in bits

	def name(self):
		return self._name

	def size(self):
		return self._size

	def __str__(self):
		return self._name

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

class RegOffset(Memory):
	def __init__(self, name, offset, size):
		self._name = name
		self._offset = offset
		self._size = size

	def size(self):
		return self._size

	def addr(self, host):
		base = host.inferior().reg(self._name)
		addr = base+self._offset
		return addr

	def __str__(self):
		s = ""
		deref = "(%%%s)" % self._name
		if self._offset == 0:
			return deref
		elif self._offset < 0:
			s += "-"

		off = self._offset
		if off < 0:
			off = -off

		s += "0x%x" % off
		s += deref
		return s

class StackOffset(RegOffset):
	def __init__(self, offset, size, stack_grows_down=True):
		self._offset = offset
		self._size = size
		self._stack_grows_down = stack_grows_down

	def addr(self, host):
		sp = host.inferior().reg_sp()
		if self._stack_grows_down:
			addr = sp+self._offset
		else:
			addr = sp-self._offset
		return addr

	def __str__(self):
		deref = "(%%sp)"
		if offset < 1:
			return deref

		s = "0x%x" % self._offset
		if not self._stack_grows_down:
			s = "-" + s

		return s + deref

class Absolute(Memory):
	def __init__(self, addr, size):
		self._addr = addr
		self._size = size

	def size(self):
		return self._size

	def addr(self, host):
		return self._addr

	def __str__(self):
		return "*0x%x" % self._addr

def offset(name, offset, n):
	return RegOffset(name, offset, n << 3)

def abs(addr, n):
	return Absolute(addr, n << 3)
