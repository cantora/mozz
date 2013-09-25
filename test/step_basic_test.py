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
			'got_after_write': 0
		}

		@s.on_step()
		def each_step(host):
			if host.inferior().is_in_step_into_mode():
				lend = "\r"
			else:
				lend = "\n"

			sys.stdout.write("step %d%s" % (d['got_step'], lend))
			state[0] += 1
			d['got_step'] += 1

		@s.at_addr("main")
		def main(host):
			self.assertEqual(state[0], 0)
			state[0] += 1
			host.inferior().enter_step_over_mode()
			self.assertTrue(host.inferior().is_in_step_mode())
			self.assertTrue(host.inferior().is_in_step_over_mode())

		@s.at_addr(0x400622)
		def at_write(host):
			d['got_at_write'] += 1
			self.assertEqual(state[0], 23)
			state[0] += 1
			#host.inferior().enter_step_into_mode()
			#self.assertTrue(host.inferior().is_in_step_mode())
			#self.assertTrue(host.inferior().is_in_step_into_mode())
		
		@s.at_addr(0x400627)
		def after_write(host):
			d['got_after_write'] += 1
			state[0] += 1
			host.inferior().enter_step_over_mode()
			self.assertTrue(host.inferior().is_in_step_mode())
			self.assertTrue(host.inferior().is_in_step_over_mode())
			
		mozz.run_session(s)
		self.assertEqual(d['got_at_write'], 1)
		self.assertEqual(d['got_after_write'], 1)
		#self.assertEqual(state[0], 2+d['got_step'])
		#self.assertEqual(d['got_step'], 36)

run_test_module(__name__, __file__)
