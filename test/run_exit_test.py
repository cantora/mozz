import unittest

import mozz
import mozz.test
import mozz.sig

class Test(unittest.TestCase):

	def test_run_exit(self):
		s = mozz.Session("test_run_exit")
		
		s.set_target_rel(__file__, "run_exit_test.bin")

		d = {
			'got_exit': False,
			'got_run': False
		}
	
		@s.on_exit()
		def on_exit(host):
			d['got_exit'] = True

		@s.to_run()
		def run(host):
			d['got_run'] = True
			host.run_inferior()

		mozz.run_session(s)
		self.assertEqual(d['got_exit'], True)
		self.assertEqual(d['got_run'], True)

mozz.test.run_test_module(__name__, __file__)
