import os
import re
import threading

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
		self.lock = threading.Lock()
		self.cbs = {}
		if callable(log):
			self.log = log
		else:
			self.log = self.default_log

	def currently(self, *args):
		self.lock.acquire()
		try:
			for name in args:
				if self.state == name:
					return True
		finally:
			self.lock.release()

		return False

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

		return tmp
	
	def delete_callback(self, from_state, to_state, fn):
		self.lock.acquire()
		try:
			edge = (from_state, to_state)
			l = self.cbs.get(edge, [])
			self.cbs[edge] = [
				(cb_fn, cb_args, cb_kwargs) \
					for (cb_fn, cb_args, cb_kwargs) in l \
					if cb_fn != fn
			]
		finally:
			self.lock.release()

	def transition(self, to_state, *args, **kwargs):
		self.lock.acquire()
		try:
			edge = (self.state, to_state)
			trans = 'trans_%s_%s' % edge
			fn = getattr(self, trans, False)
			if not fn or not callable(fn):
				raise Exception("no such transition from %s " + \
								"to %s" % (self.state, to_state))

			self.log(("transition %s -> %s, " % edge) + \
						"args=%r, kwargs=%r" % (args, kwargs))
			fn(*args, **kwargs)
			self.state = to_state

			for (cb_fn, cb_args, cb_kwargs) in self.cbs.get(edge, []):
				self.log("transition callback %s -> %s " % edge + \
							" to %s" % cb_fn.__name__)
				cb_fn(*cb_args, **cb_kwargs)
		finally:
			self.lock.release()
