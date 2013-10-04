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
import re
import threading

import mozz.log

def python_file_basename(fpath):
	return os.path.basename(python_path_basename(fpath))

def python_path_basename(fpath):
	return re.sub(
		r'\.pyc?$', '', 
		os.path.abspath(fpath),
	)


class CallDuplicator(object):

	class ReceiverDisagreementErr(Exception):
		pass

	def __init__(self, obj_tuple, *args):
		if 'duped_methods' in args:
			raise ValueError("'duped_methods' is reserved!")

		self.duped_methods = args
		self.receivers = obj_tuple

	def __getattr__(self, attr):
		if attr in self.duped_methods:
			def duplicate(*args, **kwargs):
				results = [
					getattr(obj, attr)(*args, **kwargs) for obj in self.receivers
				]
				collapsed = set(results)
				if len(collapsed) != 1:
					raise ReceiverDisagreementErr(
						"not all receivers returned the " + \
						"same result: %r" % (collapsed)
					)

				return results[0] #all items should be the same

			return duplicate
		else:
			return super(CallDuplicator, self).__getattr__(attr)


class IOWriteDuplicator(CallDuplicator):

	def __init__(self, *args):
		super(IOWriteDuplicator, self).__init__(
			args,
			'flush',
			'writable',
			'writelines',
			'write',
			'writeln'			
		)


class StateMachine(object):
	INIT 		= 'init'

	@staticmethod
	def default_log(s):
		pass

	def __init__(self, log=None):
		self.state = self.INIT
		self.n = 0
		self.lock = threading.Lock()
		self.cbs = {}
		if callable(log):
			self.log = log
		else:
			self.log = self.default_log

	def iteration(self):
		self.lock.acquire()
		result = self.n
		self.lock.release()
		return result

	def currently(self, *args):
		self.lock.acquire()
		try:
			for name in args:
				if self.state == name:
					return True
		finally:
			self.lock.release()

		return False

	def current(self):
		self.lock.acquire()
		result = self.state
		self.lock.release()
		return result

	def a_block_until(self, from_state, to_state):
		'''
		blocks at end of code sequence until the
		specified transition occurs
		'''
		event = threading.Event()
		@self.register_callback(from_state, to_state)
		def notify_fn():
			event.set()

		st = self
		class Wait(object):

			def __enter__(self):
				pass

			def __exit__(self, ty, val, traceback):
				if ty is None:
					event.wait()
				st.delete_callback(from_state, to_state, notify_fn)
				return False

		return Wait()

	def register_callback(self, from_state, to_state, *args, **kwargs):
		def tmp(fn):
			self.lock.acquire()
			try:
				edge = (from_state, to_state)
				if edge not in self.cbs:
					self.cbs[edge] = []
				self.cbs[edge].append( (fn, args, kwargs) )
			finally:
				self.lock.release()

			return fn

		return tmp
	
	def delete_callback(self, from_state, to_state, fn):
		self.lock.acquire()
		try:
			edge = (from_state, to_state)
			if not edge in self.cbs:
				return

			self.cbs[edge] = [
				(cb_fn, cb_args, cb_kwargs) \
					for (cb_fn, cb_args, cb_kwargs) in self.cbs.get(edge, []) \
					if cb_fn != fn
			]
		finally:
			self.lock.release()

	def transition(self, to_state, *args, **kwargs):
		self.lock.acquire()
		edge = (self.state, to_state)

		try:
			trans = 'trans_%s_%s' % edge
			fn = getattr(self, trans, False)
			if not fn or not callable(fn):
				raise Exception(("no such transition from %s " + \
								"to %s") % (self.state, to_state))

			self.log(("transition (%d) " % self.n) + \
						("%s -> %s, " % edge) + \
						"args=%r, kwargs=%r" % (args, kwargs))

			fn(*args, **kwargs)
			self.state = to_state
			if edge[1] == self.INIT:
				self.n += 1

			for x in (edge, (edge[0], None), (None, edge[1])):
				for (cb_fn, cb_args, cb_kwargs) in self.cbs.get(x, []):
					self.log("transition callback %s -> %s " % x + \
								" to %s" % cb_fn.__name__)
					cb_fn(*cb_args, **cb_kwargs)

		finally:
			self.lock.release()

		return edge[0] #return previous state