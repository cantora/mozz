import unittest

import mozz
from mozz.test import run_test_module, abs_path
import mozz.sig

class Test(unittest.TestCase):

	def test_default_sig(self):
		s = mozz.Session(abs_path(__file__, "signal1_test.bin"))

		d = {
			'sig_count': 0
		}

		@s.on_signal_default()
		def default_sig(host, sig):
			d['sig_count'] += 1
			self.assertEqual(sig, mozz.sig.SIGINT)

		mozz.run_session(s)
		self.assertEqual(d['sig_count'], 1)

	def test_sig_handler(self):
		s = mozz.Session(abs_path(__file__, "signal1_test.bin"))

		d = {
			'int_count': 0
		}
	
		@s.on_signal_default()
		def default_sig(host, sig):
			self.assertTrue(False) # shouldnt get here

		@s.on_signal(mozz.sig.SIGINT)
		def on_sigint(host):
			d['int_count'] += 1

		mozz.run_session(s)
		self.assertEqual(d['int_count'], 1)

	def test_start(self):
		s = mozz.Session(abs_path(__file__, "signal1_test.bin"))
	
		d = {
			'start': 0,
			'sigs': 0
		}

		@s.on_start()
		def on_start(host):
			d['start'] += 1

		@s.on_signal(mozz.sig.SIGINT)
		def on_sigint(host):
			d['sigs'] += 1
			self.assertEqual(d['start'], 1)

		mozz.run_session(s)
		self.assertEqual(d['start'], 2)
		self.assertEqual(d['sigs'], 1)

run_test_module(__name__, __file__)
