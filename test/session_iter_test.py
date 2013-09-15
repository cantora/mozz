import unittest

import mozz
import mozz.test

class Test(unittest.TestCase):

	def test_session_iter(self):
		s = mozz.Session("test_session_iter")
		
		s.set_target_rel(__file__, "session_iter_test.bin")

		@s.to_run()
		def run(host):
			for i in range(0, 10):
				host.log("i=%d" % i)
				host.run_inferior()
				self.assertEqual(s.iteration(), i+1)

		mozz.run_session(s)
		self.assertEqual(s.iteration(), 10)

mozz.test.run_test_module(__name__, __file__)
