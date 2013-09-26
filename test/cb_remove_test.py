import unittest

import mozz
from mozz.test import run_test_module, abs_path
import mozz.sig

class Test(unittest.TestCase):

	def test_run_exit(self):
		s = mozz.Session(abs_path(__file__, "cb_remove_test.bin"), 3)

		d = {
			'on_pre':      0,
			'on_post':     0,
			'at_entry':    0,
			'on_run':      0,
			'on_finish':   0,
			'on_sigint':   0,
            'on_sig_default': 0,
			'on_start':    0,
			'on_start2':   0,
			'on_exit':     0,
			'main':        0,
			'main2':       0
		}

		@s.on_run()
		def run():
			d['on_run'] += 1

		s.del_cb_run(run)

		@s.on_inferior_pre()
		def on_pre(host):
			d['on_pre'] += 1
			s.del_cb_inferior_pre(on_pre)

		@s.on_inferior_post()
		def on_post(host):
			d['on_post'] += 1
			s.del_cb_inferior_post(on_post)

		@s.at_entry()
		def entry(host):
			d['at_entry'] += 1
			s.del_cb_entry(entry)

		@s.on_signal(mozz.sig.SIGINT)
		def sigint(host):
			d['on_sigint'] += 1
			s.del_cb_signal(mozz.sig.SIGINT, sigint)
			@s.on_signal_default()
			def sig_default(host, sig):
				d['on_sig_default'] += 1
				s.del_cb_signal_default(sig_default)

		start1_first = [0]
		@s.on_start()
		def start(host):
			start1_first[0] += 1
			d['on_start'] += 1
			s.del_cb_start(start)

		@s.on_start()
		def start2(host):
			d['on_start2'] += 1
			self.assertEqual(start1_first[0], 1)
			if d['on_start2'] >= 3:
				s.del_cb_start(start2)

		@s.on_exit()
		def on_exit(host):
			d['on_exit'] += 1
			s.del_cb_exit(on_exit)

		@s.on_finish()
		def finish():
			d['on_finish'] += 1

		s.del_cb_finish(finish)

		main1_first = [0]
		@s.at_addr("main")
		def main(host):
			d['main'] += 1
			main1_first[0] += 1
			s.del_addr_cb_fn("main", main)

		@s.at_addr("main")
		def main2(host):
			d['main2'] += 1
			self.assertEqual(main1_first[0], 1)

		mozz.run_session(s)

		self.assertEqual(s.iteration(), 3)
		self.assertEqual(d['on_pre'], 1)
		self.assertEqual(d['on_post'], 1)
		self.assertEqual(d['at_entry'], 1)
		self.assertEqual(d['on_run'], 0)
		self.assertEqual(d['on_finish'], 0)
		self.assertEqual(d['on_sigint'], 1)
		self.assertEqual(d['on_sig_default'], 1)
		self.assertEqual(d['on_start'], 1)
		self.assertEqual(d['on_start2'], 3)
		self.assertEqual(d['on_exit'], 1)
		self.assertEqual(d['main'], 1)
		self.assertEqual(d['main2'], 3)

run_test_module(__name__, __file__)
