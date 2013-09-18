import mozz.err
from mozz.ioconfig import *
import mozz.sig
	
class HostErr(mozz.err.Err):
	pass

class Breakpoint(object):
	
	def delete(self):
		'''
		deletes the breakpoint and invalidates this object
		'''
		raise NotImplementedError("not implemented")
	
class Host(object):

	def __init__(self, session):
		self.session = session
		self.inf = None
		self._drop_into_cli = False
		self.inferior_procs = []
		self.about_to_start_inferior = False
		self.bps = {}

	def log(self, s):
		print(s)

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
		self.clear_breakpoints()
		self.set_breakpoints()

	def clear_inferior(self):
		self.clear_breakpoints()
		if self.inf:
			self.inf.cleanup()

		self.invoke_callback(mozz.cb.INFERIOR_POST)
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
		self.about_to_start_inferior = True
		return self._run_inferior(*args, **kwargs)

	def _run_inferior(self, *args, **kwargs):
		'''
		internal method for subclasses to override
		'''
		raise NotImplementedError("not implemented")


	def continue_inferior(self):
		'''
		if run_inferior returned while the inferior was still
		alive (but stopped), this will continue the inferior.
		this should be able to be called indefinitely until
		the inferior exits and may return will the inferior is
		still alive but stopped.
		'''

		while self.should_continue():
			if self.need_to_flush_inferior_procs():
				self.flush_inferior_procs()

			if self.drop_into_cli():
				self.clear_drop_into_cli()
				return 
			mozz.debug("host: continue")
			self.inferior().cont()

		self.clear_inferior()
		return

	def invoke_callback(self, key, *args, **kwargs):
		#host is always the first argument to callbacks
		#so it doesnt need to be explicit
		args = (self,) + args

		if isinstance(key, (int, long)):
			addr = mozz.session.addr_from_int(key)
			result = self.session.notify_addr(addr, *args, **kwargs)
		elif isinstance(key, str):
			result = self.session.notify_event(key, *args, **kwargs)
		else:
			raise TypeError("unexpected callback key %r" % key)

		#if key[0:3] != "SIG" and not result:
		#	mozz.debug("callback %r not handled" % key)

		return result

	def set_breakpoints(self):

		for addr in self.session.each_break_addr(self.inferior()):
			if addr in self.bps:
				continue
			bp = self.set_breakpoint(addr)
			if bp is None:
				raise Exception("invalid breakpoint %r" % bp)

			self.bps[addr] = bp

	def clear_breakpoints(self):
		for (addr, bp) in self.bps.items():
			bp.delete()

		self.bps = {}

	def set_breakpoint(self, addr):
		'''
		returns a breakpoint object. the object should support the
		interface defined by the Breakpoint class above. addr must be
		an integer.
		'''
		raise NotImplementedError("not implemented")

	def set_drop_into_cli(self):
		self._drop_into_cli = True

	def clear_drop_into_cli(self):
		'''
		whenever the host implementation is sure that it can
		actually drop into the command interface, it should
		call this to clear the flag just before doing so.
		'''
		self._drop_into_cli = False

	def drop_into_cli(self):
		'''
		flag which specifies that the session has requested that
		control be given to the host/user until the user decides
		to continue again.
		'''
		return (self._drop_into_cli == True)

	def with_inferior(self, *args, **kwargs):
		'''
		schedule a change to the inferior. modifications of 
		inferior memory/registers/(any kind of process state)
		should be done within the function decorated by this
		method. this allows the implementation host to ensure
		that the changes are made safely.
		'''
		def dec(fn):
			self.inferior_procs.append( (fn, args, kwargs) )
			return fn

		return dec

	def flush_inferior_procs(self):
		for (fn, args, kwargs) in self.inferior_procs:
			fn(self, *args, **kwargs)

		self.inferior_procs = []

	def need_to_flush_inferior_procs(self):
		return len(self.inferior_procs) > 0

	def on_break(self):
		'''
		only invokes callbacks to session for address at pc,
		doesnt notify the inferior of a break, because we 
		dont necessarily consider a 'break' to be a 'stop';
		rather, a 'break' may cause a 'stop', in which case
		the `on_break_and_stop` callback should be invoked
		following this callback
		'''
		if self.ignore_callback():
			return False
		
		return self.invoke_callback(self.inferior().reg_pc())

	def on_break_and_stop(self):
		'''
		this doesnt invoke callbacks to the session as it
		assumes that the session was already notified via
		a call to `on_break`. this only notifies the inferior
		that it has stopped because of a break.
		'''
		if self.ignore_callback():
			return False

		self.inferior().on_break()

	def on_stop(self, signal):
		if self.ignore_callback():
			return False

		self.inferior().on_stop(signal)

		if not signal in mozz.sig.signals():
			signal = mozz.cb.SIGNAL_UNKNOWN

		result = self.invoke_callback(signal)
		if not result:
			result = self.invoke_callback(mozz.cb.SIGNAL_DEFAULT, signal)

		return result
	
	def on_start(self):
		if self.ignore_callback():
			return False

		if self.about_to_start_inferior == True:
			self.about_to_start_inferior = False
			self.invoke_callback(mozz.cb.INFERIOR_PRE)

		self.inferior().on_start()
		return self.invoke_callback(mozz.cb.START)

	def on_exit(self):
		if self.ignore_callback():
			return False

		self.inferior().on_exit()
		return self.invoke_callback(mozz.cb.EXIT)

class InfErr(mozz.err.Err):
	pass

class SymbolNotFound(InfErr):
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

	def run(self, *args):
		'''
		run this inferior until the first stop
		'''
		if self.state() != "dead":
			raise InfErr("tried to run a non-dead inferior")

		return self._run(*args)

	def _run(self, *args):
		'''
		internal (for subclasses): run this inferior until the first stop
		'''
		raise NotImplementedError("not implemented")
		
	def cont(self):
		'''
		cause a stopped inferior to continue
		'''
		if self.state() != "stopped":
			raise InfErr("tried to continue a non-stopped inferior")

		return self._cont()

	def _cont(self):
		'''
		internal: cause a stopped inferior to continue
		'''
		raise NotImplementedError("not implemented")

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

	def reg_pc(self):
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

	def symbol_addr(self, name):
		'''
		returns the absolute address of symbol @name.
		raises SymbolNotFound if @name is not found.
		'''
		result = self._symbol_addr(name)
		if not result:
			raise SymbolNotFound("symbol %r was not found" % name)

		return result

	def _symbol_addr(self, name):
		'''
		returns None if @name is not found, else it returns the
		absolute runtime address of @name.
		'''
		raise NotImplementedError("not implemented")