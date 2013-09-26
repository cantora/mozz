import unittest

import mozz
from mozz.test import run_test_module, abs_path
import mozz.sig

class Test(unittest.TestCase):

	def test_run_exit(self):
		s = mozz.Session(abs_path(__file__, "run_exit_test.bin"), 2)

		state = [0]

		@s.on_run()
		def run(host):
			mozz.debug("cb run")
			self.assertEqual(s.iteration(), 0)
			self.assertEqual(state[0], 0)
			state[0] += 1

		def offset():
			return (s.iteration()-1)*4

		@s.on_inferior_pre()
		def inf_pre(host):
			mozz.debug("cb inf pre")
			self.assertEqual(state[0], offset() + 1)
			state[0] += 1

		@s.at_entry()
		def entry(host):
			pc = host.inferior().reg_pc()
			mozz.debug("entry point is 0x%x" % (pc))
			self.assertEqual(pc, 0x400410)
			self.assertEqual(state[0], offset() + 2)
			state[0] += 1

		@s.on_exit()
		def on_exit(host):
			mozz.debug("cb exit")
			self.assertEqual(state[0], offset() + 3)
			state[0] += 1

		@s.on_inferior_post()
		def on_inf_post(host):
			mozz.debug("cb inf post")
			self.assertEqual(state[0], offset() + 4)
			state[0] += 1

		@s.on_finish()
		def finish(host):
			mozz.debug("cb finish")
			self.assertEqual(s.iteration(), 2)
			self.assertEqual(state[0], offset() + 5)
			state[0] += 1

		mozz.run_session(s)
		mozz.debug("session over")
		self.assertEqual(s.iteration(), 2)
		self.assertEqual(state[0], offset() + 6)

run_test_module(__name__, __file__)
