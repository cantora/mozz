# Copyright 2013 anthony cantor
# This file is part of mozz.
# 
# mozz is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#  
# mozz is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#  
# You should have received a copy of the GNU General Public License
# along with mozz.  If not, see <http://www.gnu.org/licenses/>.
from collections import namedtuple

import mozz.err
from mozz.ioconfig import *
import mozz.sig
import mozz.prototype.int
	
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
			and self.inferior().is_alive() \
			and (not self.session.get_flag_stop())

	def run_inferior(self):
		self.session.clear_flags()
		self.about_to_start_inferior = True
		return self._run_inferior(
			*self.session.target_args,
			**self.session.target_kwargs
		)

	def _run_inferior(self, *args, **kwargs):
		'''
		internal method for subclasses to override.
		valid keyword args:
			'stdin':	IOConfig instance
			'stdout':	IOConfig instance
			'stderr':	IOConfig instance
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
			#mozz.debug("host: advance")
			pc = self.inferior().reg_pc()
			self.inferior().advance()
			#mozz.debug("host: done with advance")
			if self.inferior().is_in_step_mode() \
					and self.inferior().is_alive():
				#self.on_break()
				if pc != self.inferior().reg_pc():
					#pc might not change if a segfault happened
					#or something like that.
					self.invoke_callback(mozz.cb.STEP)

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
		def add_bp(addr):
			bp = self.set_breakpoint(addr)
			if bp is None:
				raise Exception("invalid breakpoint %r" % bp)

			self.bps[addr] = bp

		for addr in self.session.each_break_addr(self.inferior()):
			if addr in self.bps:
				continue

			add_bp(addr)

		add_bp(self.inferior().entry_point)
		
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
		if self.ignore_callback():
			return False
		
		if self.inferior().reg_pc() == self.inferior().entry_point:
			self.invoke_callback(mozz.cb.ENTRY)

		return self.invoke_callback(self.inferior().reg_pc())

	def on_stop(self, signal):
		if self.ignore_callback():
			return False

		#mozz.debug("host: on_stop")
		if not signal in mozz.sig.signals():
			signal = mozz.cb.SIGNAL_UNKNOWN

		result = self.invoke_callback(signal)
		if not result:
			result = self.invoke_callback(mozz.cb.SIGNAL_DEFAULT, signal)
	
		return result
	
	def on_start(self):
		if self.ignore_callback():
			return False

		#mozz.debug("host: on_start")
		if self.about_to_start_inferior == True:
			self.about_to_start_inferior = False
			self.invoke_callback(mozz.cb.INFERIOR_PRE)

		return self.invoke_callback(mozz.cb.START)

	def on_exit(self):
		if self.ignore_callback():
			return False

		#mozz.debug("host: on_exit")
		return self.invoke_callback(mozz.cb.EXIT)

class Instruction(namedtuple('InstructionBase', 'str_val addr data')):

	def __init__(self, str_val, addr, data):
		'''
		@str_val: the string representation of the instruction
		@addr: the address from where the instruction was disassembled
		@data: a tuple of bytes representing the binary form of the instruction
		'''

		if not isinstance(str_val, str):
			raise TypeError("invalid str_val: %r" % str_val)
		if not isinstance(addr, int):
			raise TypeError("invalid addr: %r" % addr)
		if not isinstance(data, tuple) \
				or len([x for x in data if not isinstance(x, int)]) > 0:
			raise TypeError("invalid data: %r" % data)

		super(Instruction, self).__init__(str_val, addr, data)

	def __str__(self):
		return self.str_val

	def __int__(self):
		return self.addr
	
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

	@property
	def io_names(self):
		return self.__class__.IO_NAMES

	def __init__(self, **kwargs):
		self.step_mode = False

		for (name, mode) in self.io_names.items():
			int_name = "_"+name
			if name in kwargs:
				if not isinstance(kwargs[name], IOConfig):
					raise TypeError("expected IOConfig object: %r" % kwargs[name])

				setattr(self, int_name, kwargs[name])
			else:
				setattr(self, int_name, DefaultIOConfig(mode))

	def is_alive(self):
		'''
		returns True if this inferior is a live process, else returns
		False.
		'''
		raise NotImplementedError("not implemented")

	def pid(self):
		if not self.is_alive():
			return nil

		return self._pid()

	def _pid(self):
		'''
		return process id (as integer) of the inferior
		'''
		raise NotImplementedError("not implemented")

	def is_in_step_mode(self):
		return self.step_mode != False

	def is_in_step_into_mode(self):
		return self.step_mode == 'into'

	def is_in_step_over_mode(self):
		return self.step_mode == 'over'

	def enter_step_over_mode(self):
		return self.enter_step_mode('over')

	def enter_step_into_mode(self):
		return self.enter_step_mode('into')

	def enter_step_mode(self, step_type='over'):
		mozz.debug("enter step mode: %s" % step_type)
		self.step_mode = step_type

	def exit_step_mode(self):
		mozz.debug("exit step mode")
		self.step_mode = False

	@property
	def entry_point(self):
		if not getattr(self, 'entry_addr', False):
			self.entry_addr = self._entry_point()

		return self.entry_addr

	def _entry_point(self):
		'''
		return an integer representing the address of 
		the program entry point.
		'''
		raise NotImplementedError("not implemented")
	
	def run(self, *args):
		'''
		run this inferior until the first stop
		'''
		return self._run(*args)

	def _run(self, *args):
		'''
		internal (for subclasses): run this inferior until the first stop
		'''
		raise NotImplementedError("not implemented")

	def advance(self):
		'''
		continue or step, depending on which mode the
		inferior is currently in.
		'''
		if self.step_mode == 'over':
			return self.step_over()
		elif self.step_mode == 'into':
			return self.step_into()
		else:
			return self.cont()
		
	def cont(self):
		'''
		cause a stopped inferior to continue
		'''
		mozz.debug("inf: cont")
		return self._cont()

	def _cont(self):
		'''
		internal: cause a stopped inferior to continue
		'''
		raise NotImplementedError("not implemented")

	def step_over(self):
		'''
		step one instruction forward without descending into calls
		'''
		#mozz.debug("inf: step_over")
		return self._step_over()

	def _step_over(self):
		raise NotImplementedError("not implemented")

	def step_into(self):
		'''
		step one instruction forward, descending into calls
		'''
		#mozz.debug("inf: step_into")
		return self._step_into()

	def _step_into(self):
		raise NotImplementedError("not implemented")

	def cleanup(self):
		if self.is_alive():
			self.kill()

		for name in self.io_names.keys():
			getattr(self, name)().cleanup()

	def kill(self):
		raise NotImplementedError("not implemented")

	def stdin(self):
		return self._stdin

	def stdout(self):
		return self._stdout
	
	def stderr(self):
		return self._stderr

	def reg(self, name):
		'''
		returns value of @name register
		'''
		raise NotImplementedError("not implemented")
	
	def reg_sp(self):
		raise NotImplementedError("not implemented")

	def reg_pc(self):
		raise NotImplementedError("not implemented")

	def reg_set(self, name, value):
		'''
		set @name register to @value.
		'''
		raise NotImplementedError("not implemented")

	def reg_set_pc(self, value):
		raise NotImplementedError("not implemented")

	def reg_set_sp(self, value):
		raise NotImplementedError("not implemented")

	def mem_write_uint32(self, addr, val):
		#TODO: fix LE assumption
		v = (
			(val & 0x000000ff),
			(val & 0x0000ff00) >> 8,
			(val & 0x00ff0000) >> 16,
			(val & 0xff000000) >> 24,
		)
		return self.mem_write(addr, v)

	def mem_write_buf(self, addr, data):
		'''
		write @data at @addr. @addr should be an integer
		and @data should be an object which yields characters.
		'''
		raise NotImplementedError("not implemented")

	def mem_write(self, addr, data):
		'''
		write @data at @addr. @addr should be an integer
		and @data should be an object which yields integers 
		smaller than 256 when iterated.
		'''
		raise NotImplementedError("not implemented")

	def mem_read(self, addr, sz):
		'''
		read @sz bytes at @addr. @addr and @sz should be 
		integers. returns a list of integers < 256.
		'''
		raise NotImplementedError("not implemented")

	def mem_read_buf(self, addr, sz):
		'''
		read @sz bytes at @addr. @addr and @sz should be 
		integers. returns a buffer-like object.
		'''
		raise NotImplementedError("not implemented")

	def mem_read_uint64(self, addr, *args, **kwargs):
		data = self.mem_read_buf(addr, 8)
		kwargs['size'] = 64
		return mozz.prototype.int.to_uint(data, *args, **kwargs)

	def mem_read_uint32(self, addr, *args, **kwargs):
		data = self.mem_read_buf(addr, 4)
		kwargs['size'] = 32
		return mozz.prototype.int.to_uint(data, *args, **kwargs)

	def mem_read_uint16(self, addr, *args, **kwargs):
		data = self.mem_read_buf(addr, 2)
		kwargs['size'] = 16
		return mozz.prototype.int.to_uint(data, *args, **kwargs)

	def mem_read_uint8(self, addr):
		data = self.mem_read(addr, 1)
		return data[0]

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

	def disassemble(self, addr, amt=1):
		'''
		disassemble @amt instructions at addr.
		yields Instruction instances.
		'''
		raise NotImplementedError("not implemented")

	def current_instruction(self):
		for i in self.disassemble(self.reg_pc(), 1):
			return i

		raise InfErr("could not disassemble one instruction at pc")

	def registers(self):
		'''
		returns a set of register names.
		'''
		raise NotImplementedError("not implemented")

	def register_values(self):
		'''
		yields tuples of (register name, register value)
		in no particular order
		'''
		for name in self.registers():
			yield (name, self.reg(name))
