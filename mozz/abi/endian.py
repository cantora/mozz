
class Little(object):
	@staticmethod
	def format():
		return '<'

	@staticmethod
	def truncate(size, data):
		num_bytes = size >> 3
		return data[0:num_bytes]

class Big(object):
	@staticmethod
	def format():
		return '>'

	@staticmethod
	def truncate(size, data):
		num_bytes = size >> 3
		return data[-num_bytes:]
