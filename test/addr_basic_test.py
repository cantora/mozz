import unittest

import mozz
import mozz.test

class Test(unittest.TestCase):

	def test_addr_basic(self):
		s = mozz.Session("test_run_exit")
		
		s.set_target_rel(__file__, "addr_basic_test.bin")

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

mozz.test.run_test_module(__name__, __file__)
