import unittest

import mozz
from mozz.test import run_test_module, abs_path

class Test(unittest.TestCase):

	def test_mockup_fake_file(self):
		s = mozz.Session(abs_path(__file__, "mockup_basic_test.bin"))

		d = {
			'got_sig':       False,
			'got_fake_fp':   0,
			'got_fake_read': 0,
			'goal_fn_execd': 0,
			'won':           0
		}

		@s.on_signal_default()
		def sig_default(host, sig):
			d['got_sig'] = True

		@s.at_addr("try_to_get_here")
		def goal_fn(host):
			d['goal_fn_execd'] += 1

		@s.at_addr(0x40069c)
		def victory(host):
			d['won'] += 1

		fp = 0xc0ffee
		@s.mockup(0x4006f4, 0x4006f9)
		def fake_fp(host):
			d['got_fake_fp'] += 1
			@host.with_inferior()
			def seteax(host):
				host.inferior().reg_set("rax", fp)

		@s.mockup(0x400730, 0x400735, regset=('rdi',) )
		def fake_read(host, rdi):
			host.log("rdi=0x%x" % rdi)
			d['got_fake_read'] += 1
			@host.with_inferior()
			def blah(host):
				inf = host.inferior()
				inf.mem_write_buf(rdi, "purpledrank\x00")
				inf.reg_set("rax", 0x10)

		mozz.run_session(s)
		self.assertFalse(d['got_sig'])
		self.assertEqual(d['got_fake_fp'], 1)
		self.assertEqual(d['got_fake_read'], 1)
		self.assertEqual(d['goal_fn_execd'], 1)
		self.assertEqual(d['won'], 1)

run_test_module(__name__, __file__)
