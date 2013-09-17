import unittest

import mozz
from mozz.test import run_test_module, abs_path

class Test(unittest.TestCase):

	def test_session_iter(self):
		s = mozz.Session(abs_path(__file__, "session_iter_test.bin"), 10)

		state = [0]
		@s.on_inferior_pre()
		def inf_pre(host):
			state[0] += 1
			mozz.debug("i=%d" % state[0])
			self.assertEqual(s.iteration(), state[0])

		mozz.run_session(s)
		self.assertEqual(s.iteration(), 10)

run_test_module(__name__, __file__)
