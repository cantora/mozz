import os
from collections import namedtuple

import mozz.err
from mozz.cb import *
import mozz.log

class SessionErr(mozz.err.Err):
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
		self.event_cbs = {}
		self.addr_cbs = {}
		self.mockups = {}
		self.skip_map = {}
		self.n = 0
		self.target = target
		self.flags = {}
		self.flag_finished = False
		if limit >= 0:
			self.limit = limit
		else:
			self.limit = 1

	def iteration(self):
		return self.n

	def add_cb_fn(self, d, k):
		def tmp(fn):
			d[k] = fn
			return fn

		return tmp

	def add_event_cb_fn(self, name):
		return self.add_cb_fn(self.event_cbs, name)

	def add_addr_cb_fn(self, addr):
		return self.add_cb_fn(self.addr_cbs, addr)

	def on_inferior_pre(self):
		'''
		called just after inferior object is created
		and before it is run
		'''
		return self.add_event_cb_fn(mozz.cb.INFERIOR_PRE)

	def on_inferior_post(self):
		'''
		called just after inferior finishes and just
		before it the inferior object is destroyed
		'''
		return self.add_event_cb_fn(mozz.cb.INFERIOR_POST)

	def at_entry(self):
		'''
		invoke the decorated function at the execution of
		the entry point
		'''
		return self.add_event_cb_fn("entry")

	def at_addr(self, addr):
		(addr,) = convert_values_to_addrs(addr)

		return self.add_addr_cb_fn(addr)

	def mockup(self, addr, jmp, *args, **kwargs):
		(addr, jmp) = convert_values_to_addrs(addr, jmp)

		def tmp(fn):
			self.mockups[addr] = (fn, jmp, kwargs)
			return fn

		return tmp

	def skip(self, addr, end):
		'''
		skip instructions at address [@addr, @end). in otherwords,
		jump to @end when we arrive at @addr
		'''
		(addr, end) = convert_values_to_addrs(addr, end)
		self.skip_map[addr] = end

	def on_run(self):
		'''
		invoke this callback when the host is ready to
		run the session.
		'''
		return self.add_event_cb_fn("run")

	def on_finish(self):
		'''
		invoke this callback when the session is finished
		and about to be destroyed.
		'''
		return self.add_event_cb_fn("finish")

	def on_signal_default(self):
		return self.add_event_cb_fn(SIGNAL_DEFAULT)

	def on_signal(self, sig):
		return self.add_event_cb_fn(sig)

	def on_signal_unknown(self):
		return self.add_event_cb_fn(SIGNAL_UNKNOWN)

	def on_start(self):
		return self.add_event_cb_fn(START)

	def on_exit(self):
		return self.add_event_cb_fn(EXIT)

	def process_event(self, name, *args, **kwargs):
		if name == mozz.cb.INFERIOR_PRE:
			self.n += 1
		elif name == mozz.cb.INFERIOR_POST:
			if self.limit > 0 and self.n >= self.limit:
				self.set_flag_finished()
		
	def notify_event(self, name, *args, **kwargs):
		self.process_event(name, *args, **kwargs)

		if not name in self.event_cbs \
				or not callable(self.event_cbs[name]):
			return False

		self.event_cbs[name](*args, **kwargs)
		return True

	def find_addrs(self, d, addr, inferior):
		i = addr.value(inferior)
		for (k, v) in d.items():
			kval = k.value(inferior)
			if kval == i:
				yield (k, v) 

	def notify_addr(self, addr, host, *args, **kwargs):
		mozz.log.debug("notify address %r" % (addr,))
		handled = False
		
		for (k, v) in self.find_addrs(self.addr_cbs, addr, host.inferior()):
			if not callable(v):
				continue
	
			handled = True
			v(host, *args, **kwargs)

		for (k, (fn, jmp, options)) in self.find_addrs(self.mockups, addr, host.inferior()):
			if not callable(fn):
				continue
	
			handled = True
			self.do_mockup_callback(host, fn, jmp, options, *args, **kwargs)

		return handled

	def do_mockup_callback(self, host, fn, jmp, options, *args, **kwargs):
		regargs = []
		if 'regset' in options:
			for reg in options['regset']:
				regargs.append(host.inferior().reg(reg))
		
		args = tuple(regargs) + args
		fn(host, *args, **kwargs)
		@host.with_inferior()
		def set_pc(host):
			host.inferior().reg_set_pc(jmp.value(host.inferior()))

		
	def notify_event_run(self, host):
		return self.notify_event("run", host)

	def notify_event_finish(self, host):
		return self.notify_event("finish", host)

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

		for addr in self.skip_map.keys():
			yield addr.value(inferior)
