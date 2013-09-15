import os
import re

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