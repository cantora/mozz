import os, tempfile

class IOConfig(object):
	MODES = ('r', 'w')				

	@property
	def modes(self):
		return self.__class__.MODES

	def __init__(self, mode):
		if not mode in self.modes:
			raise ValueError("invalid mode %r" % mode)
		self._mode = mode
	
	def mode(self):
		return self._mode

	def filename(self):
		raise NotImplementedError("this IOConfig doesnt have a filename")

	def io_object(self):
		raise NotImplementedError("this IOConfig doesnt have an io_object")

	def is_redirected(self):
		return False

	def cleanup(self):
		pass

class DefaultIOConfig(IOConfig):
	'''
	non-specified configuration. basically defers
	to what the host does by default
	'''
	def filename(self):
		return None

	def io_object(self):
		return None

class FifoConfig(IOConfig):

	@staticmethod
	def make_fifo(mode):
		tmpfile = tempfile.NamedTemporaryFile()
		filename = tmpfile.name
		tmpfile.close() #just wanted it for the name :b

		try:
			os.mkfifo(filename)
		except OSError as e:
		    raise OSError("Failed to create FIFO: %s" % e)

		return (
			filename,
			open(filename, mode)
		)
	
	def __init__(self, mode):
		super(self, FifoConfig).__init__(mode)
		(self._filename, self._io_object) = self.__class__.make_fifo(mode)

	def filename(self):
		return self._filename

	def io_object(self):
		return self._io_object

	def is_redirected(self):
		return True

class RedirConfig(IOConfig):
	def __init__(self, mode, filepath):
		super(self, RedirConfig).__init__(mode)
		self._filename = filepath

	def filename(self):
		return self._filename

	def is_redirected(self):
		return True

def redirect_stdin_to(filename):
	return RedirConfig("w", filename)

def redirect_stdout_to(filename):
	return RedirConfig("r", filename)

def redirect_stderr_to(filename):
	return RedirConfig("r", filename)
