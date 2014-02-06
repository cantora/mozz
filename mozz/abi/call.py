import struct

import mozz.err

class Location(object):
	def size(self):
		raise Exception("not implemented")

	def value(self, host):
		'''
		return value at location in native endian format
		'''
		raise Exception("not implemented")

	def set(self, host, data):
		raise Exception("not implemented")

class Register(Location):
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
		fmt = mozz.util.size_to_struct_fmt(self._size)
		if not fmt:
			raise Exception("invalid register size %d" % self._size)
		data = struct.pack("%s%s" % (endian.format(), fmt), v)
		return data

	def set(self, host, data):
		endian = host.session.endian()
		fmt = mozz.util.size_to_struct_fmt(self._size)
		if not fmt:
			raise Exception("invalid register size %d" % self._size)
		v = struct.unpack(
			"%s%s" % (fmt, endian.format()),
			data[0:self._size]
		)
		host.inferior().reg_set(self._name, v)
		
class StackOffset(Location):
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

	def value(self, host):
		addr = self.addr(host)
		byte_size = self._size >> 3
		#returns data in native endian format
		return host.inferior().mem_read_buf(addr, byte_size)

	def set(self, host, data):
		addr = self.addr(host)
		byte_size = self._size >> 3
		#returns data in native endian format
		return host.inferior().mem_write_buf(addr, data[0:byte_size])

class Convention(object):
	class UnknownArgument(mozz.err.Err):
		pass

	def __init__(self, host):
		self.host = host
		self.loc_table = {}

	def add_loc_entry(self, cat_name, n, loc):
		k = (cat_name, n)
		self.loc_table[k] = loc
	
	def type_to_category(self, t):
		'''
		convert the type t to a type category
		'''
		raise Exception("not implemented")

	def arg(self, t, n):
		'''
		get argument n of type t. argument 0 is the return value
		'''
		category = self.type_to_category(t)

		k = (category, n)
		if k not in self.loc_table:
			raise UnknownArgument(
				"dont know how to locate argument" + \
				" %d of type %s" % (n, t)
			)
		loc = self.loc_table[k]

		v = loc.value(self.host)
		getter = lambda: v
		setter = lambda data: loc.set(self.host, data)

		return (getter, setter)

class X8664SYSVConvention(Convention):
	'''
	this isnt complete, it just handles the
	calling convention for INTEGER type arguments
	and return types right now.
	'''

	def __init__(self, host):
		super(X8664SYSVConvention, self).__init__(host)

		sgd = host.session.stack_grows_down()

		self.add_loc_entry('INTEGER', 0, Register("rax", 64))
		self.add_loc_entry('INTEGER', 1, Register("rdi", 64))
		self.add_loc_entry('INTEGER', 2, Register("rsi", 64))
		self.add_loc_entry('INTEGER', 3, Register("rdx", 64))
		self.add_loc_entry('INTEGER', 4, Register("rcx", 64))
		self.add_loc_entry('INTEGER', 5, Register("r8", 64))
		self.add_loc_entry('INTEGER', 6, Register("r9", 64))

		for i in range(7, 32):
			offset = (i-7)*8 + 8
			self.add_loc_entry('INTEGER', i, StackOffset(offset, 64, sgd))

	def type_to_category(self, t):
		return 'INTEGER'
