import mozz.err

class HostErr(mozz.err.Err):
	pass

class Host(object):

	def __init__(self, filepath):
		self.filepath = filepath

	def inferior(self):
		'''
		returns an instance of Inf
		'''
		raise NotImplementedError("not implemented")

class InfErr(mozz.err.Err):
	pass

class Inf(object):

	def mem_write(self, addr, bytes):
		'''
		write @bytes at @addr. @addr should be an integer
		and @bytes should be a tuple of integers < 256.
		'''
		raise NotImplementedError("not implemented")

	def mem_read(self, addr, sz):
		'''
		read @sz bytes at @addr. @addr and @sz should be 
		integers. returns a tuple of integers < 256.
		'''
		raise NotImplementedError("not implemented")

	def reg_write(self, name, val):
		'''
		set @name register to @val.
		'''
		raise NotImplementedError("not implemented")

	def reg_read(self, name):
		'''
		returns value of @name register
		'''
		raise NotImplementedError("not implemented")

