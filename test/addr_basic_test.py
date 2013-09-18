import unittest

import mozz
from mozz.test import run_test_module, abs_path

class Test(unittest.TestCase):

	def test_addr_basic(self):
		s = mozz.Session(abs_path(__file__, "addr_basic_test.bin"))

		d = {
			'got_cb': 		0,
			'got_sig': 		False,
			'got_sym_cb':	0
		}

		@s.on_signal_default()
		def sig_default(host, sig):
			d['got_sig'] = True

		@s.at_addr(0x4004f4)
		def at_main(host):
			d['got_cb'] += 1

		@s.at_addr("main")
		def at_main(host):
			self.assertEqual(0x4004f4, host.inferior().reg_pc())
			d['got_sym_cb'] += 1

		mozz.run_session(s)
		self.assertEqual(d['got_cb'], 1)
		self.assertFalse(d['got_sig'])
		self.assertEqual(d['got_sym_cb'], 1)

run_test_module(__name__, __file__)
