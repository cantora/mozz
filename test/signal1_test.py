import unittest

import mozz
import mozz.test

class Test(unittest.TestCase):

	def test_sig(self):
		s = mozz.Session("signal1_test")
		
		s.set_target_rel(__file__, "signal1_test.bin")
	
		@s.on_signal_default()
		def default_sig(host, sig):
			self.assertEqual(sig, "SIGSTOP")

		mozz.run_session(s)

mozz.test.run_test_module(__name__, __file__)
