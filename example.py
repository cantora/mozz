#!/usr/bin/env python

import mozz
import mozz.sig

def main():
	s = mozz.Session("test1")
	
	s.set_target("./example-bin")

	@s.at_entry()
	def at_entry(host):
		host.log("program entry %d" % host.session.iteration())
	
	@s.at_addr(0x004005c3)
	def at_main(host):
		host.log("at main %d" % host.session.iteration())
	
	@s.mockup(0x40077b, 0x4007a5)
	def fake_fp(host):
		host.log("make fake fp")
		raise Exception("Qwerqwer")
	
	s.skip(0x4007bf, 0x4007cb)
	
	@s.mockup(0x4006cc, 0x4006d1)
	def fake_read(host):
		host.log("do fake read")
		raise Exception("Asdfa")

	@s.on_signal_default()
	def default_sig(host, sig):
		host.log("got signal: %r" % sig)

	@s.on_signal(mozz.sig.SIGFPE)
	def on_fpe(host):
		host.log("got fpe. set stop flag")
		host.session.set_flag_stop()

	@s.on_start()
	def on_start(host):
		host.log("start inferior")

	@s.on_exit()
	def on_exit(host):
		host.log("inferior exited")

	@s.to_run()
	def run(host):
		for i in range(0, 4):
			host.log("===========================================")
			host.log("run inferior %d" % i)
			host.run_inferior()

	return s
