#!/usr/bin/env python

import mozz

print("start example")
s = mozz.get_session("test1")
print("got session")


@s.at_entry()
def at_entry(sess):
	print("program entry %d" % sess.iteration())

@s.at_addr(0x004005c3)
def at_main(sess):
	print("at main %d" % sess.iteration())

@s.mockup(0x40077b, 0x4007a5)
def fake_fp(sess):
	print("make fake fp")
	raise Exception("Qwerqwer")

s.skip(0x4007bf, 0x4007cb)

@s.mockup(0x4006cc, 0x4006d1)
def fake_read(sess):
	print("do fake read")
	raise Exception("Asdfa")
