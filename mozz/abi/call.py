import mozz.err
from mozz.location import StackOffset, Register

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

	def return_value_size(self):
		'''
		return the number of bits the function
		return value can hold.
		'''
		raise Exception("not implemented")

	def set_return_value(self, val):
		'''
		set function call return value to val
		'''
		raise Exception("not implemented")

	def do_return(self):
		'''
		execute the return procedure for this
		architecture
		'''
		raise Exception("not implemented")

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
		#TODO: implement other types
		return 'INTEGER'

	def return_value_size(self):
		return (8 << 3)

	def set_return_value(self, val):
		self.host.inferior().reg_set("rax", val)

	def do_return(self):
		sp = self.host.inferior().reg_sp()
		en = self.host.session.endian()
		saved_pc = self.host.inferior().mem_read_uint64(sp, endian=en)
		self.host.inferior().reg_set_pc(saved_pc)

		if self.host.session.stack_grows_down():
			new_sp = sp + 8
		else:
			new_sp = sp - 8
		self.host.inferior().reg_set_sp(new_sp)

class X86SYSVConvention(Convention):

	def __init__(self, host):
		super(X86SYSVConvention, self).__init__(host)

		sgd = host.session.stack_grows_down()

		self.add_loc_entry('INTEGER', 0, Register("eax", 32))

		#ebp -> saved ebp
		#ebp + 4 -> ret
		#ebp + 8 -> arg0
		#...etc
		for i in range(1, 32):
			offset = i*4 + 4 
			self.add_loc_entry('INTEGER', i, StackOffset(offset, 32, sgd))

	def type_to_category(self, t):
		#TODO: implement other types
		return 'INTEGER'

	def return_value_size(self):
		return (4 << 3)

	def set_return_value(self, val):
		self.host.inferior().reg_set("rax", val)

	def do_return(self):
		sp = self.host.inferior().reg_sp()
		en = self.host.session.endian()
		saved_pc = self.host.inferior().mem_read_uint32(sp, endian=en)
		self.host.inferior().reg_set_pc(saved_pc)

		if self.host.session.stack_grows_down():
			new_sp = sp + 4
		else:
			new_sp = sp - 4
		self.host.inferior().reg_set_sp(new_sp)

class NativeConventionUnknown(mozz.err.Err):
	pass

def native_convention():
	import mozz.system
	mach = mozz.system.architecture()
	if mach == mozz.system.ARCH_X86_64:
		return X8664SYSVConvention
	elif mach == mozz.system.ARCH_X86:
		return X86SYSVConvention

	raise NativeConventionUnknown("no calling convention " + \
									"known for machine type: " + \
									repr(mach))
