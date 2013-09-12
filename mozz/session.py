from collections import namedtuple

import mozz.err

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
		return addr

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

	def __init__(self, name):
		self.name = name
		self.event_cbs = {}
		self.addr_cbs = {}
		self.mockups = {}
		self.skip_map = {}
		self.n = 0

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

	def notify_event(self, name, *args):
		if not name in self.event_cbs \
				or not callable(self.event_cbs[name]):
			return

		self.event_cbs[name](self, *args)

	def notify_entry(self):
		return self.notify_event("entry")

	def find_addr(self, d, addr):
		i = int(addr)
		for (k, v) in d.items():
			if int(k) == i:
				return (k, v)

		return (None, None)

	def notify_addr(self, addr, *args):
		(k, v) = self.find_addr(self.addr_cbs, addr)
		if None in (k, v) or not callable(v):
			return

		return v(self, k, *args)

	def run(self, host):
		raise Exception("Asdf")

