from collections import namedtuple
import struct

import mozz.err
import mozz.abi.endian
import mozz.util

class SizeError(mozz.err.Err):
	pass

class TwosComplementSigned(object):
	@staticmethod
	def format(sz):
		fmt = mozz.util.size_to_struct_fmt(sz)
		if not fmt:
			raise SizeError('unknown int size %d' % sz)
		return fmt

class TwosComplementUnsigned(object):
	@staticmethod
	def format(sz):
		return TwosComplementSigned.format(sz).upper()

def to_int(data, *args, **kwargs):
	sz = 32
	endian = mozz.abi.endian.Little
	fmt = TwosComplementSigned

	if 'size' in kwargs:
		sz = kwargs['size']
	if 'endian' in kwargs:
		endian = kwargs['endian']
	if 'fmt' in kwargs:
		fmt = kwargs['fmt']

	if (len(data)*8) != sz:
		raise SizeError("data size = %d != %d" % (len(data)*8, sz))

	fmt_str = "%s%s" % (endian.format(), fmt.format(sz))

	return struct.unpack(fmt_str, data)[0]

def to_uint(data, *args, **kwargs):
	kwargs['fmt'] = TwosComplementUnsigned
	return to_int(data, *args, **kwargs)

def to_data(val, *args, **kwargs):
	sz = 32
	endian = mozz.abi.endian.Little
	fmt = TwosComplementSigned

	if 'size' in kwargs:
		sz = kwargs['size']
	if 'endian' in kwargs:
		endian = kwargs['endian']
	if 'fmt' in kwargs:
		fmt = kwargs['fmt']

	fmt_str = "%s%s" % (endian.format(), fmt.format(sz))

	return struct.pack(fmt_str, val)
