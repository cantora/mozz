import mozz.err
from mozz.ioconfig import *
import mozz.sig
	
class HostErr(mozz.err.Err):
	pass
	
class Host(object):

	def __init__(self, session):
		self.session = session
		self.inf = None

	def log(self, s):
		raise NotImplementedException("not implemented")

	def has_inferior(self):
		if not self.inf:
			return False

		return True

	def set_inferior(self, inf):
		if not isinstance(inf, Inf):
			raise TypeError("expected instance of Inf: %r" % inf)

		self.inf = inf

	def clear_inferior(self):
		if self.inf:
			self.inf.cleanup()

		self.inf = None

	def inferior(self):
		return self.inf

	def should_continue(self):
		return self.has_inferior() \
			and (not self.inferior().state() == "dead") \
			and (not self.session.get_flag("stop"))			

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

	STATES = (
		'running', 			#inferior is running (not stopped)
		'stopped',			#inferior is stopped
		'dead'				#inferior process is dead or hasnt been created yet
	)

	@property
	def io_names(self):
		return self.__class__.IO_NAMES

	def __init__(self, **kwargs):
		self._running = False	
		self._callbacks = {}

		for (name, mode) in self.io_names.items():
			int_name = "_"+name
			if name in kwargs:
				if not isinstance(kwargs[name], IOConfig):
					raise TypeError("expected IOConfig object: %r" % kwargs[name])

				setattr(self, int_name, kwargs[name])
			else:
				setattr(self, int_name, DefaultIOConfig(mode))

	def cleanup(self):
		for name in self.io_names.keys():
			getattr(self, name)().cleanup()

	@property
	def callbacks(self):
		return self._callbacks

	def running(self):
		return self._running

	def state(self):
		'''
		returns one of the STATES in the tuple above
		'''
		raise NotImplementedError("not implemented")

	def invoke_callback(self, key):
		if not key in self._callbacks \
				or not callable(self._callbacks[key]):
			return False

		self._callbacks[key]()
		return True

	def on_break(self):
		self._running = False
		self.invoke_callback(self.pc_addr())

	def on_stop(self, signal):
		self._running = False

		if not signal in mozz.sig.signals():
			signal = 'signal_unknown'

		if not self.invoke_callback(signal):
			self.invoke_callback('signal_default')
											
	def on_start(self):
		self._running = True
		self.invoke_callback("start")

	def on_exit(self):
		self._running = False
		self.invoke_callback("exit")

	def stdin(self):
		return self._stdin

	def stdout(self):
		return self._stdout
	
	def stderr(self):
		return self._stderr

	def pc_addr(self):
		raise NotImplementedError("not implemented")

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

