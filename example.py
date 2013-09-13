#!/usr/bin/env python

import mozz

def main():
	print("start example")
	s = mozz.Session("test1")
	print("got session")
	
	s.set_target("./example-bin")

	@s.at_entry()
	def at_entry(host):
		print("program entry %d" % host.session.iteration())
	
	@s.at_addr(0x004005c3)
	def at_main(host):
		print("at main %d" % host.session.iteration())
	
	@s.mockup(0x40077b, 0x4007a5)
	def fake_fp(host):
		print("make fake fp")
		raise Exception("Qwerqwer")
	
	s.skip(0x4007bf, 0x4007cb)
	
	@s.mockup(0x4006cc, 0x4006d1)
	def fake_read(host):
		print("do fake read")
		raise Exception("Asdfa")

	@s.to_run()
	def run(host):
		host.run_inferior()

	return s
