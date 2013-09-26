import unittest
import sys

import mozz
from mozz.test import run_test_module, abs_path
import mozz.sig

class Test(unittest.TestCase):

	def test_basic_step(self):
		s = mozz.Session(abs_path(__file__, "step_basic_test.bin"))

		state = [0]
		d = {
			'got_step':        0,
			'got_at_write':    0,
			'got_after_write': 0,
			'got_start':       0,
			'got_sig':         0,
			'got_on_exit':     0,
			'got_main_ret':    0
		}

		@s.on_start()
		def on_start(host):
			#host.log("start")
			d['got_start'] += 1

		@s.on_signal_default()
		def on_sig(host):
			d['got_sig'] += 1

		@s.on_step()
		def each_step(host):
			if host.inferior().is_in_step_into_mode():
				lend = "\r"
			else:
				lend = "\n"

			sys.stdout.write("step %d%s" % (d['got_step'], lend))
			d['got_step'] += 1

		@s.at_addr("main")
		def main(host):
			self.assertEqual(state[0], 0)
			self.assertEqual(d['got_step'], 0)
			state[0] += 1
			host.inferior().enter_step_over_mode()
			host.log("oiajsdofij")
			self.assertTrue(host.inferior().is_in_step_mode())
			self.assertTrue(host.inferior().is_in_step_over_mode())

		@s.at_addr(0x400622)
		def at_write(host):
			d['got_at_write'] += 1
			self.assertEqual(d['got_step'], 22)
			self.assertEqual(state[0], 1)
			state[0] += 1
			host.inferior().enter_step_into_mode()
			self.assertTrue(host.inferior().is_in_step_mode())
			self.assertTrue(host.inferior().is_in_step_into_mode())
		
		@s.at_addr(0x400627)
		def after_write(host):
			d['got_after_write'] += 1
			self.assertEqual(d['got_step'], 702)						
			self.assertEqual(state[0], 2)
			state[0] += 1
			host.inferior().enter_step_over_mode()
			self.assertTrue(host.inferior().is_in_step_mode())
			self.assertTrue(host.inferior().is_in_step_over_mode())

		@s.at_addr(0x400658)
		def main_ret(host):
			d['got_main_ret'] += 1
			self.assertEqual(state[0], 3)
			self.assertEqual(d['got_step'], 712)
			state[0] += 1
			host.inferior().exit_step_mode()
			self.assertFalse(host.inferior().is_in_step_mode())
		
		@s.on_exit()
		def on_exit(host):
			host.log("inferior exited")
			self.assertEqual(state[0], 4)
			self.assertEqual(d['got_step'], 712)
			d['got_on_exit'] += 1
			state[0] += 1
			host.log("asdfoaisjdfoij")

		mozz.run_session(s)

		self.assertEqual(d['got_at_write'], 1)
		self.assertEqual(d['got_after_write'], 1)
		self.assertEqual(state[0], 5)
		self.assertEqual(d['got_step'], 712)
		self.assertEqual(d['got_start'], 712+3)
		self.assertEqual(d['got_sig'], 0)
		self.assertEqual(d['got_on_exit'], 1)
		self.assertEqual(d['got_main_ret'], 1)

run_test_module(__name__, __file__)
