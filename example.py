#!/usr/bin/env python

import mozz
import mozz.sig
import mozz.rand

s = mozz.Session("./example-bin", 100)

s.set_target_kwargs(
	stdout=mozz.redirect_stdout_to('example-bin.out')
)

@s.on_inferior_pre()
def on_inferior_pre(host):
	host.log("start inferior")

	s.set_target_args(
		'guy',
		'chuy',
		'stuff',
		'blah',
		'A'*(mozz.rand.intrange(1, 200))
	)

@s.on_exit()
def on_exit(host):
	host.log("inferior exited")

@s.on_signal(mozz.sig.SIGSEGV)
def on_seg(host):
	host.log("may have found vuln!")
	host.set_drop_into_cli()

s.skip(0x40079f, 0x4007a4)

@s.mockup(0x4007e5, 0x4007ea)
def fake_fp(host):
	@host.with_inferior()
	def seteax(host):
		host.inferior().reg_set("rax", 0xc0ffee)

@s.mockup(0x40071c, 0x400721, regset=("rdi",))
def fake_read(host, rdi):
	@host.with_inferior()
	def do_read(host):
		itr = s.iteration()
		inf = host.inferior()
		l = mozz.rand.intrange(1, 16)
		v = mozz.rand.byte_buf(l)
		host.log("v=%r" % v)
		inf.mem_write_buf(rdi, v)
		inf.reg_set("rax", len(v))

s.skip(0x400820, 0x400825)

@s.mockup(0x400850, 0x400853)
def magic_div_by_0(host):
	@host.with_inferior()
	def seteax(host):
		host.inferior().reg_set("eax", 1234)

@s.on_signal_default()
def default_sig(host, sig):
	host.log("got signal: %r" % sig)

@s.on_signal(mozz.sig.SIGFPE)
def on_fpe(host):
	host.log("got fpe. set stop flag")
	host.session.set_flag_stop()

mozz.run_session(s)
