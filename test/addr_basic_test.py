import unittest

import mozz
from mozz.test import run_test_module, abs_path

class Test(unittest.TestCase):

	def test_addr_basic(self):
		s = mozz.Session(abs_path(__file__, "addr_basic_test.bin"))

		d = {
			'got_cb': False,
			'got_sig': False
		}

		@s.on_signal_default()
		def sig_default(host, sig):
			d['got_sig'] = True

		@s.at_addr(0x4004f4)
		def at_main(host):
			d['got_cb'] = True

		mozz.run_session(s)
		self.assertTrue(d['got_cb'])
		self.assertFalse(d['got_sig'])

run_test_module(__name__, __file__)
