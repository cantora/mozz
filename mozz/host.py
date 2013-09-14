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

	def ignore_callback(self):
		return (not self.has_inferior())

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
			and (not self.session.get_flag_stop())

	def run_inferior(self, *args, **kwargs):
		'''
		runs inferior file with @args and returns
		when inferior exits.
		valid keyword args:
			'stdin':	IOConfig instance
			'stdout':	IOConfig instance
			'stderr':	IOConfig instance
		'''
		self.session.clear_flags()

		return self._run_inferior(*args, **kwargs)

	def _run_inferior(self, *args, **kwargs):
		'''
		internal method for subclasses to override
		'''
		raise NotImplementedError("not implemented")

	def invoke_callback(self, key, *args, **kwargs):
		args = (self,) + args

		if isinstance(key, mozz.session.Addr):
			result = self.session.notify_addr(key, *args, **kwargs)
		elif isinstance(key, str):
			result = self.session.notify_event(key, *args, **kwargs)
		else:
			raise TypeError("unexpected callback key %r" % key)

		#if key[0:3] != "SIG" and not result:
		#	print("callback %r not handled" % key)

		return result

	def on_break(self):
		if self.ignore_callback():
			return
		
		self.inferior().on_break()
		self.invoke_callback(self.inferior().pc_addr())

	def on_stop(self, signal):
		if self.ignore_callback():
			return

		self.inferior().on_stop(signal)

		if not signal in mozz.sig.signals():
			signal = mozz.cb.SIGNAL_UNKNOWN

		result = self.invoke_callback(signal)
		if not result:
			result = self.invoke_callback(mozz.cb.SIGNAL_DEFAULT, signal)

		return result
											
	def on_start(self):
		if self.ignore_callback():
			return

		self.inferior().on_start()
		self.invoke_callback(mozz.cb.START)

	def on_exit(self):
		if self.ignore_callback():
			return

		self.inferior().on_exit()
		self.invoke_callback(mozz.cb.EXIT)

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

		for (name, mode) in self.io_names.items():
			int_name = "_"+name
			if name in kwargs:
				if not isinstance(kwargs[name], IOConfig):
					raise TypeError("expected IOConfig object: %r" % kwargs[name])

				setattr(self, int_name, kwargs[name])
			else:
				setattr(self, int_name, DefaultIOConfig(mode))

	def cleanup(self):
		if self.state() != "dead":
			self.kill()

		for name in self.io_names.keys():
			getattr(self, name)().cleanup()

	def kill(self):
		raise NotImplementedError("not implemented")

	def running(self):
		return self._running

	def state(self):
		'''
		returns one of the STATES in the tuple above
		'''
		raise NotImplementedError("not implemented")

	def on_break(self):
		self._running = False

	def on_stop(self, signal):
		self._running = False
											
	def on_start(self):
		self._running = True

	def on_exit(self):
		self._running = False

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

