import mozz.err
from mozz.ioconfig import *
	
class HostErr(mozz.err.Err):
	pass
	
class Host(object):

	def __init__(self, session):
		self.session = session

	def inferior(self):
		raise NotImplementedError("not implemented")

	def run_inferior(self, *args, **kwargs):
		'''
		runs inferior file with @args and returns
		when inferior exits.
		valid keyword args:
			'stdin':	IOConfig instance
			'stdout':	IOConfig instance
			'stderr':	IOConfig instance
		'''
		raise NotImplementedError("not implemented")

class InfErr(mozz.err.Err):
	pass

class Inf(object):

	IO_NAMES = {
		'stdin': 'w',
		'stdout': 'r',
		'stderr': 'r'
	}

	def __init__(self, **kwargs):

		for (name, mode) in IO_NAMES.items():
			int_name = "_"+name
			if name in kwargs:
				if not isinstance(kwargs[name], IOConfig):
					raise TypeError("expected IOConfig object: %r" % kwargs[name])

				setattr(self, int_name, kwargs[name])
			else:
				setattr(self, int_name, DefaultIOConfig(mode))

	def cleanup(self):
		for name in IO_NAMES.keys():
			getattr(self, name).cleanup()

	def running(self):
		raise NotImplementedError("not implemented")

	def stdin(self):
		return self._stdin

	def stdout(self):
		return self._stdout
	
	def stderr(self):
		return self._stderr

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

