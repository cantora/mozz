import unittest

import mozz
from mozz.test import run_test_module, abs_path
from mozz.prototype import *
from mozz.abi.call import native_convention
import mozz.system

class Test(unittest.TestCase):

	def check_params(self,n,host,a,b,c,d,e,buf1,buf2):
		expected_params = [
			{ 	'a': 2345,
				'b': 0x78,
				'c': 98,
				'd': 789,
				'e': 2346,
				'buf1': "8*3+1 chars of string...",
				'buf2': "secretadminpass"
			},
			{	'a': 84739,
				'b': 0x7a,
				'c': 2847,
				'd': 9308,
				'e': 12345,
				'buf1': "c00lpass1337",
				'buf2': "8*3+1 chars of string..."
			},
			{	'a': 72,
				'b': 72,
				'c': 9374,
				'd': 1038,
				'e': 43879,
				'buf1': "asdf",
				'buf2': "qwer"
			}
		]

		if n >= 3:
			return False

		map = {'a': a, 'b': b, 'c': c, 'd': d, 'e': e}
		for (k,v) in map.items():
			if not (expected_params[n][k] == v.value()):
				return False

		map = {'buf1': buf1, 'buf2': buf2}
		for (k,v) in map.items():
			if expected_params[n][k] != v.string(host):
				return False

		return True

	def test_trace_function(self):
		arch = mozz.system.architecture()
		if arch != mozz.system.ARCH_X86_64:
			return #this test not yet supported on non x86_64 systems

		s = mozz.Session(abs_path(__file__, "function_test.bin"))
		s.set_calling_convention(native_convention())

		result = {
			'count': 0,
			'params_correct': [0,0,0]
		}

		@s.at_function(
			"test_function",
			TCInt32, TCInt8, TCInt16, TCUInt32, TCInt32,
			Pointer64, Pointer64, Pointer64
		)
		def test_function(host, fn_ctx, n, a, b, c, d, e, \
							buf1, buf2, output_var):
			host.log("test_function(%d):" % n)
			host.log("  a=%d" % a.value())
			host.log("  b=%d" % b.value())
			host.log("  c=%d" % c.value())
			host.log("  d=%d" % d.value())
			host.log("  e=%d" % e.value())
			host.log("  buf1=%x:%r" % (buf1.value(), buf1.string(host)))
			host.log("  buf2=%x:%r" % (buf2.value(), buf2.string(host)))
			host.log("  output_var=%x" % output_var.value())

			result['count'] += 1
			if n < 3 and self.check_params(n,host,a,b,c,d,e,buf1,buf2):
				result['params_correct'][n] = 1

		mozz.run_session(s)
		self.assertEqual(result['count'], 3)
		for i in range(3):
			print("check params #%d" % i)
			self.assertEqual(result['params_correct'][i], 1)

	def test_mockup_function(self):
		arch = mozz.system.architecture()
		if arch != mozz.system.ARCH_X86_64:
			return #this test not yet supported on non x86_64 systems

		s = mozz.Session(abs_path(__file__, "function_test.bin"))
		s.set_calling_convention(native_convention())

		result = {
			'count': 0,
			'params_correct': [0,0,0]
		}

		@s.at_function(
			"test_function",
			TCInt32, TCInt8, TCInt16, TCUInt32, TCInt32,
			Pointer64, Pointer64, Pointer64
		)
		def test_function(host, fn_ctx, n, a, b, c, d, e, \
							buf1, buf2, output_var):
			host.log("test_function(%d):" % n)
			host.log("  a=%d" % a.value())
			host.log("  b=%d" % b.value())
			host.log("  c=%d" % c.value())
			host.log("  d=%d" % d.value())
			host.log("  e=%d" % e.value())
			host.log("  buf1=%x:%r" % (buf1.value(), buf1.string(host)))
			host.log("  buf2=%x:%r" % (buf2.value(), buf2.string(host)))
			host.log("  output_var=%x" % output_var.value())

			result['count'] += 1
			if n < 3 and self.check_params(n,host,a,b,c,d,e,buf1,buf2):
				result['params_correct'][n] = 1

			return 0

		mozz.run_session(s)
		self.assertEqual(result['count'], 3)
		for i in range(3):
			print("check params #%d" % i)
			self.assertEqual(result['params_correct'][i], 1)

run_test_module(__name__, __file__)
