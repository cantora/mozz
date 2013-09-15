import unittest

import mozz
import mozz.test
import mozz.sig

class Test(unittest.TestCase):

	def test_run_exit(self):
		s = mozz.Session("test_run_exit")
		
		s.set_target_rel(__file__, "run_exit_test.bin")

		state = [0]

		@s.to_run()
		def run(host):
			self.assertEqual(state[0], 0)
			state[0] += 1
			host.run_inferior()

		@s.on_inferior_pre()
		def inf_pre(host):
			self.assertEqual(state[0], 1)
			state[0] += 1

		@s.on_exit()
		def on_exit(host):
			self.assertEqual(state[0], 2)
			state[0] += 1

		@s.on_inferior_post()
		def on_inf_post(host):
			self.assertEqual(state[0], 3)
			state[0] += 1

		mozz.run_session(s)
		self.assertEqual(state[0], 4)

mozz.test.run_test_module(__name__, __file__)
