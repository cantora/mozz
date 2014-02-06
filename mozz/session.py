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
import os
from collections import namedtuple

import mozz.err
from mozz.cb import *
import mozz.log
import mozz.abi.endian

class SessionErr(mozz.err.Err):
	pass

class FunctionContext(object):
	'''
	placeholder. still needs to be implemented
	'''
	pass

class Addr(object):
	
	def value(self, inferior):
		'''
		convert this address into an integer value, 
		potentially using the inferior to resolve.
		'''
		raise NotImplementedError("not implemented")

class SymbolOffset(namedtuple('SymbolOffsetBase', 'name offset'), Addr):
	'''
	represents the numeric value of a symbol + some offset
	'''
	def __init__(self, name, offset):
		if not isinstance(offset, (int, long)):
			offset = 0
		super(SymbolOffset, self).__init__(name, offset)

	def value(self, inferior):
		return inferior.symbol_addr(self.name) + self.offset

class NumericAddr(namedtuple('NumericAddrBase', 'addr base'), Addr):
	def __init__(self, addr, base):
		'''
		a runtime address. @addr should be an 
		integer. if @base is a `str` then @base will
		be looked up as a section, the runtime 
		segment mapping of that section shall be 
		determined, and @addr will be treated as
		an offset into the segment in which the 
		section resides.
		'''
		
		if not isinstance(base, str):
			base = None

		super(NumericAddr, self).__init__(addr, base)

	def value(self, inferior):
		'''
		havent implemented self.base functionality yet,
		so only absolute addresses are supported now
		'''
		return self.addr

def addr_from_int(n):
	return NumericAddr(n, None)

def convert_values_to_addrs(*args):
	result = []
	for x in args:
		if isinstance(x, (int,long)):
			newx = NumericAddr(x, None)
		elif isinstance(x, str):
			newx = SymbolOffset(x, 0)
		elif isinstance(x, tuple) and len(x) == 2 \
				and isinstance(x[0], str) \
				and isinstance(x[1], (int,long)):
			newx = SymbolOffset(*x)
		elif isinstance(x, Addr):
			newx = x
		else:
			raise TypeError("invalid input address %r" % x)

		result.append(newx)

	return tuple(result)

class Session(object):

	def __init__(self, target, limit=1):
		'''
		@target: the target binary path
		@limit: the maximum number of times to
                run the session before stopping.
		'''
		self.event_cbs = {}
		self.addr_cbs = {}
		self.mockups = {}
		self.function_cbs = {}
		self.skip_map = {}
		self.break_counts = {}
		self.n = 0
		self.set_little_endian()
		self._stack_grows_down = True
		self.target = target
		self._target_args = tuple([])
		self._target_kwargs = {}
		self.calling_convention = None
		'''
		valid keyword args:
			'stdin':	IOConfig instance
			'stdout':	IOConfig instance
			'stderr':	IOConfig instance
		'''
		self.flags = {}
		self.flag_finished = False
		if limit >= 0:
			self.limit = limit
		else:
			self.limit = 1

	def set_calling_convention(self, cc):
		self.calling_convention = cc

	def set_little_endian(self):
		self._endian = mozz.abi.endian.Little

	def set_big_endian(self):
		self._endian = mozz.abi.endian.Big

	def set_stack_grows_up(self):
		self._stack_grows_down = False

	def endian(self):
		return self._endian

	def stack_grows_down(self):
		return self._stack_grows_down

	@property
	def target_args(self):
		return self._target_args

	@property
	def target_kwargs(self):
		return self._target_kwargs

	def set_target_args(self, *args):
		self._target_args = args

	def set_target_kwargs(self, **kwargs):
		self._target_kwargs = kwargs

	def iteration(self):
		return self.n

	def add_event_cb_fn(self, name):
		def tmp(fn):
			if name not in self.event_cbs:
				self.event_cbs[name] = []
			self.event_cbs[name].append(fn)
			return fn

		return tmp

	def remove_event_cb_fn(self, name, fn):
		if name not in self.event_cbs:
			return False

		if fn not in self.event_cbs[name]:
			return False

		self.event_cbs[name] = [
			x for x in self.event_cbs[name] if x != fn
		]
		return True

	def add_addr_cb_fn(self, addr, *args, **kwargs):
		def tmp(fn):
			if addr not in self.addr_cbs:
				self.addr_cbs[addr] = []
			self.addr_cbs[addr].append((fn, args, kwargs))
			return fn

		return tmp

	def del_addr_cb_fn(self, addr, fn):
		(addr,) = convert_values_to_addrs(addr)
		if addr not in self.addr_cbs:
			return False

		found = False
		new_list = []
		for (func, args, kwargs) in self.addr_cbs[addr]:
			if fn == func:
				found = True
			else:
				new_list.append((func, args, kwargs))

		if found:
			self.addr_cbs[addr] = new_list
			return True
		else:
			return False

	def on_inferior_pre(self):
		'''
		called just after inferior object is created
		and before it is run
		'''
		return self.add_event_cb_fn(INFERIOR_PRE)

	def del_cb_inferior_pre(self, fn):
		return self.remove_event_cb_fn(INFERIOR_PRE, fn)

	def on_inferior_post(self):
		'''
		called just after inferior finishes and just
		before it the inferior object is destroyed
		'''
		return self.add_event_cb_fn(INFERIOR_POST)

	def del_cb_inferior_post(self, fn):
		return self.remove_event_cb_fn(INFERIOR_POST, fn)

	def at_entry(self):
		'''
		invoke the decorated function at the execution of
		the entry point
		'''
		return self.add_event_cb_fn(ENTRY)

	def del_cb_entry(self, fn):
		return self.remove_event_cb_fn(ENTRY, fn)

	def on_step(self):
		'''
		invoke the decorated function each time the inferior
		stops in step mode. this will only be called once per
		instruction per stop, i.e. once every time the inferior
		steps.
		'''
		return self.add_event_cb_fn(STEP)

	def del_cb_step(self, fn):
		return self.remove_event_cb_fn(STEP, fn)

	def at_function(self, addr, *args, **kwargs):
		(addr,) = convert_values_to_addrs(addr)
		def tmp(fn):
			self.function_cbs[addr] = (fn, args, kwargs)
			return fn

		return tmp

	def at_addr(self, addr, *args, **kwargs):
		(addr,) = convert_values_to_addrs(addr)

		return self.add_addr_cb_fn(addr, *args, **kwargs)

	def mockup(self, addr, jmp, *args, **kwargs):
		(addr, jmp) = convert_values_to_addrs(addr, jmp)

		def tmp(fn):
			self.mockups[addr] = (fn, jmp, kwargs)
			return fn

		return tmp

	def skip(self, addr, end, *args, **kwargs):
		'''
		skip instructions at address [@addr, @end). in otherwords,
		jump to @end when we arrive at @addr
		'''
		(addr, end) = convert_values_to_addrs(addr, end)
		self.skip_map[addr] = (end, args, kwargs)

	def on_run(self):
		'''
		invoke this callback when the host is ready to
		run the session.
		'''
		return self.add_event_cb_fn(RUN)

	def del_cb_run(self, fn):
		return self.remove_event_cb_fn(RUN, fn)

	def on_finish(self):
		'''
		invoke this callback when the session is finished
		and about to be destroyed.
		'''
		return self.add_event_cb_fn(FINISH)

	def del_cb_finish(self, fn):
		return self.remove_event_cb_fn(FINISH, fn)

	def on_signal_default(self):
		return self.add_event_cb_fn(SIGNAL_DEFAULT)

	def del_cb_signal_default(self, fn):
		return self.remove_event_cb_fn(SIGNAL_DEFAULT, fn)

	def on_signal(self, sig):
		return self.add_event_cb_fn(sig)

	def del_cb_signal(self, sig, fn):
		return self.remove_event_cb_fn(sig, fn)

	def on_signal_unknown(self):
		return self.add_event_cb_fn(SIGNAL_UNKNOWN)

	def del_cb_signal_unknown(self, fn):
		return self.remove_event_cb_fn(SIGNAL_UNKNOWN, fn)

	def on_start(self):
		return self.add_event_cb_fn(START)

	def del_cb_start(self, fn):
		return self.remove_event_cb_fn(START, fn)
	
	def on_exit(self):
		return self.add_event_cb_fn(EXIT)

	def del_cb_exit(self, fn):
		return self.remove_event_cb_fn(EXIT, fn)

	def process_event(self, name, *args, **kwargs):
		if name == INFERIOR_PRE:
			self.n += 1
		elif name == INFERIOR_POST:
			if self.limit > 0 and self.n >= self.limit:
				self.set_flag_finished()
		
	def notify_event(self, name, *args, **kwargs):
		self.process_event(name, *args, **kwargs)
		handled = False

		if not name in self.event_cbs \
				or len(self.event_cbs[name]) < 1:
			return False

		for fn in self.event_cbs[name]:
			if not callable(fn):
				continue
			fn(*args, **kwargs)
			handled = True

		return handled

	def find_addrs(self, d, addr, inferior):
		i = addr.value(inferior)
		for (k, v) in d.items():
			kval = k.value(inferior)
			if kval == i:
				yield (k, v)

	def inc_break_count(self, addr):
		if not addr in self.break_counts:
			self.break_counts[addr] = 1
		else:
			self.break_counts[addr] += 1

	def break_count(self, addr):
		if not addr in self.break_counts:
			return 0
		else:
			return self.break_counts[addr]

	def notify_addr(self, addr, host, *args, **kwargs):
		#mozz.log.debug("notify address %r" % (addr,))
		handled = False
		mockup_handled = False
		skip_handled = False

		for (_, ls) in self.find_addrs(self.addr_cbs, addr, host.inferior()):
			for (fn, _, options) in ls:
				if not callable(fn):
					continue
		
				regargs = self.make_regset_args(host, **options)
				handled = True
				fn(host, *(regargs + args), **kwargs)

		for (_, (fn, proto_args, options)) in self.find_addrs(self.function_cbs, addr, host.inferior()):
			if not callable(fn):
				continue

			self.do_function_callback(host, addr, fn, proto_args, options, *args, **kwargs)

		for (_, (fn, jmp, options)) in self.find_addrs(self.mockups, addr, host.inferior()):
			if not callable(fn):
				continue
	
			mockup_handled = True
			self.do_mockup_callback(host, fn, jmp, options, *args, **kwargs)

		#skips have lower precedence than mockups
		if not mockup_handled: 
			for (_, (jmp, _, options)) in self.find_addrs(self.skip_map, addr, host.inferior()):
				skip_handled = True 
				self.do_jmp(host, jmp, **options)

		self.inc_break_count(addr)
		
		return handled or mockup_handled or skip_handled

	def make_regset_args(self, host, **kwargs):
		regargs = []
		if 'regset' in kwargs:
			for reg in kwargs['regset']:
				regargs.append(host.inferior().reg(reg))

		return tuple(regargs)

	def do_mockup_callback(self, host, fn, jmp, options, *args, **kwargs):
		regargs = self.make_regset_args(host, **options)
		
		args = regargs + args
		fn(host, *args, **kwargs)
		self.do_jmp(host, jmp, **options)

	def do_function_callback(self, host, addr, fn, proto_args, options, *args, **kwargs):
		if not self.calling_convention:
			raise Exception("a calling convention must " + \
							"be set to use function callbacks")

		cc = self.calling_convention(host)
		arg_vals = []
		for i in range(len(proto_args)):
			arg = proto_args[i]
			arg_vals.append(arg(self.endian(), *cc.arg(arg, i+1)))

		break_count = self.break_count(addr)
		fn_ctx = FunctionContext()
		fn(host, fn_ctx, break_count, *arg_vals)

	def do_jmp(self, host, addr, **kwargs):
		@host.with_inferior()
		def set_pc(host):
			self.do_regstate(host, addr, **kwargs)
			host.inferior().reg_set_pc(addr.value(host.inferior()))
	
	def do_regstate(self, host, addr, **kwargs):
		if 'regstate' in kwargs:
			for (reg, val) in kwargs['regstate'].items():
				host.inferior().reg_set(reg, val)

	def notify_event_run(self, host):
		return self.notify_event(RUN, host)

	def notify_event_finish(self, host):
		return self.notify_event(FINISH, host)

	def clear_flags(self):
		self.flags = {}

	def set_flag(self, name):
		self.flags[name] = True
	
	def set_flag_stop(self):
		'''
		signals that the current inferior should be
		aborted and cleaned up. use this flag in a callback
		to cause host.run_inferior() to return.
		'''
		return self.set_flag("stop")

	def get_flag(self, name):
		if name in self.flags \
				and self.flags[name] == True:
			return True

		return False

	def get_flag_stop(self):
		return self.get_flag("stop")

	def set_flag_finished(self):
		'''
		once set, this flag shouldnt be
		reset by `clear_flags`, so we dont use
		the dictionary for this flag
		'''
		self.flag_finished = True

	def get_flag_finished(self):
		return self.flag_finished

	def each_break_addr(self, inferior):
		for addr in self.addr_cbs.keys():
			yield addr.value(inferior)

		for addr in self.mockups.keys():
			yield addr.value(inferior)

		for addr in self.function_cbs.keys():
			yield addr.value(inferior)

		for addr in self.skip_map.keys():
			yield addr.value(inferior)
