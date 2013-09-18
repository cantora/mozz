import unittest

import mozz
from mozz.test import run_test_module, abs_path

class Test(unittest.TestCase):

	def test_mockup_jump(self):
		s = mozz.Session(abs_path(__file__, "mockup_basic_test.bin"))

		d = {
			'got_sig':       False,
			'got_mockup':    0,
			'goal_fn_execd': 0
		}

		@s.on_signal_default()
		def sig_default(host, sig):
			d['got_sig'] = True

		@s.mockup(0x4006f4, 0x400786)
		def skip_file_stuff(host):
			self.assertEqual(host.inferior().reg_pc(), 0x4006f4)
			d['got_mockup'] += 1

		@s.at_addr("try_to_get_here")
		def goal_fn(host):
			d['goal_fn_execd'] += 1

		mozz.run_session(s)
		self.assertFalse(d['got_sig'])
		self.assertEqual(d['got_mockup'], 1)
		self.assertEqual(d['goal_fn_execd'], 1)

	def test_mockup_modify(self):
		s = mozz.Session(abs_path(__file__, "mockup_basic_test.bin"))

		d = {
			'got_sig':       False,
			'got_mockup':    0,
			'goal_fn_execd': 0,
			'won':           0
		}

		@s.on_signal_default()
		def sig_default(host, sig):
			d['got_sig'] = True

		@s.mockup(0x4006f4, 0x400786)
		def skip_file_stuff(host):
			self.assertEqual(host.inferior().reg_pc(), 0x4006f4)
			d['got_mockup'] += 1
			@host.with_inferior()
			def seteax(host):
				host.inferior().reg_set("rax", ord('p'))

		@s.at_addr("try_to_get_here")
		def goal_fn(host):
			d['goal_fn_execd'] += 1

		@s.at_addr(0x40069c)
		def victory(host):
			d['won'] += 1

		mozz.run_session(s)
		self.assertFalse(d['got_sig'])
		self.assertEqual(d['got_mockup'], 1)
		self.assertEqual(d['goal_fn_execd'], 1)
		self.assertEqual(d['won'], 1)

run_test_module(__name__, __file__)
