import unittest

import mozz
from mozz.test import run_test_module, abs_path

class Test(unittest.TestCase):

	def test_mockup_modify(self):
		s = mozz.Session(abs_path(__file__, "skip_basic_test.bin"))

		d = {
			'got_sig':       False,
			'goal_fn_execd': 0,
			'won':           0
		}

		@s.on_signal_default()
		def sig_default(host, sig):
			d['got_sig'] = True

		@s.at_addr("try_to_get_here")
		def goal_fn(host):
			d['goal_fn_execd'] += 1

		@s.at_addr(0x40069c)
		def victory(host):
			d['won'] += 1

		s.skip(0x4006f4, 0x400786)
		s.skip("try_to_get_here", 0x400697)

		mozz.run_session(s)
		self.assertFalse(d['got_sig'])
		self.assertEqual(d['goal_fn_execd'], 1)
		self.assertEqual(d['won'], 1)

run_test_module(__name__, __file__)
