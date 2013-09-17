import os
from collections import namedtuple

import mozz.err
from mozz.cb import *

class SessionErr(mozz.err.Err):
	pass

class Addr(namedtuple('AddrBase', 'addr base')):
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

		super(Addr, self).__init__(addr, base)

	def __int__(self):
		'''
		havent implemented self.base functionality yet,
		so only absolute addresses are supported now
		'''
		return self.addr

def addr_from_int(n):
	return Addr(n, None)

def convert_ints_to_addrs(*args):
	result = []
	for x in args:
		if isinstance(x, int):
			newx = Addr(x, None)
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
		(addr,) = convert_ints_to_addrs(addr)

		return self.add_addr_cb_fn(addr)

	def mockup(self, addr, jmp):
		(addr, jmp) = convert_ints_to_addrs(addr, jmp)

		def tmp(fn):
			self.mockups[addr] = (fn, jmp)
			return fn

		return tmp

	def skip(self, addr, end):
		'''
		skip instructions at address [@addr, @end). in otherwords,
		jump to @end when we arrive at @addr
		'''
		(addr, end) = convert_ints_to_addrs(addr, end)
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

	def find_addr(self, d, addr):
		i = int(addr)
		for (k, v) in d.items():
			if int(k) == i:
				return (k, v)

		return (None, None)

	def notify_addr(self, addr, *args, **kwargs):
		(k, v) = self.find_addr(self.addr_cbs, addr)
		if None in (k, v) or not callable(v):
			return False

		v(*args, **kwargs)
		return True

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

	def each_break_addr(self):
		for addr in self.addr_cbs.keys():
			yield int(addr)

		for addr in self.mockups.keys():
			yield int(addr)

		for addr in self.skip_map.keys():
			yield int(addr)
