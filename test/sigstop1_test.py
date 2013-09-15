import unittest

import mozz
import mozz.test
import mozz.sig

class Test(unittest.TestCase):

	#not sure why we get the stop signal twice
	@unittest.expectedFailure
	def test_sigstop(self):
		s = mozz.Session("test_sigstop")
		
		s.set_target_rel(__file__, "sigstop1_test.bin")

		d = {
			'stop_count': 0
		}
	
		@s.on_signal_default()
		def default_sig(host, sig):
			self.assertTrue(False) # shouldnt get here

		@s.on_signal(mozz.sig.SIGSTOP)
		def on_sigstop(host):
			d['stop_count'] += 1

		mozz.run_session(s)
		self.assertEqual(d['stop_count'], 1)


mozz.test.run_test_module(__name__, __file__)
