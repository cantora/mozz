import unittest

import mozz
import mozz.trace
from mozz.test import run_test_module, abs_path

class Test(unittest.TestCase):

	def test_trace(self):
		s = mozz.Session(abs_path(__file__, "trace_test.bin"))

		d = {
			'seq': 0
		}

		@s.at_addr("loop")
		def at_loop(host):
			self.assertEqual(d['seq'], 0)
			d['seq'] += 1
			d['tracer'] = mozz.trace.X86Tracer(host, s)
			self.assertTrue(d['tracer'].running())

		@s.at_addr(0x400535)
		def at_loop_end(host):
			self.assertTrue(d['tracer'].running())
			d['tracer'].stop(host)
			self.assertFalse(d['tracer'].running())
			self.assertEqual(d['seq'], 1)
			d['seq'] += 1

		mozz.run_session(s)
		self.assertEqual(d['seq'], 2)

run_test_module(__name__, __file__)
