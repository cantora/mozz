# mozz
mozz is a programmatic debugging/fuzzing library with 
a CLI frontend for loading scripts and initializing the
environment. It facilitates effective fuzzing by providing
a simple API for hooking functions or instructions with
custom python code. In this way, users can easily provide
mockup functions to simulated I/O instead of actually dealing
with files and/or sockets.

## overview
mozz provides a platform for readable and concise
scripts for iteratively fuzzing and/or reverse engineering 
a binary. The general idea is to start reversing a binary,
write a bit of your mozz script to mockup any system calls
or functions as necessary, then repeat until you find a 
vulnerability. Below are a couple reasons why you might
want to use mozz:

 * You are sick of hex editing binaries to jump over fork
   calls or other things like that.
 * You want to be able to just call a function from the binary
   a bunch of times with different arguments without any big
   hassle.
 * You are sick of dealing with file I/O or socket I/O
   for fuzzing binaries.

## an example
The commented example below demonstrates the fundamental features
of mozz.
```python
#!/usr/bin/env python

import mozz
import mozz.sig
from mozz import rand

#open the binary, run the session only once before
#stopping
s = mozz.Session("some_binary", 1)

#log a message before the inferior starts
@s.on_inferior_pre()
def on_inferior_pre(host):
	host.log("start inferior")

#log a message when the inferior exits
@s.on_exit()
def on_exit(host):
	host.log("inferior exited")

#celebrate! everyone knows the exploitation phase
#is always the easy part! right!?
#the host.set_drop_into_cli method sets a flag
#that if the mozz backend has a CLI, it
#should be provided at this point for manual
#investigation. see the ## backends
#section below for info on mozz backends
@s.on_signal(mozz.sig.SIGSEGV)
def on_seg(host):
	host.log("may have found vuln!")
	host.set_drop_into_cli()

#log a signal. this wont log SEGV because
#it is the default handler, so it only
#handles signals that dont have a specific
#handler
@s.on_signal_default()
def default_sig(host, sig):
	host.log("got signal: %r" % sig)

#break at 0x80489a8 and immediately
#jump to 0x8048cd1. use skip to jump
#over forks and other dumb stuff you 
#dont want to be executed
s.skip(0x80489a8, 0x8048cd1)

#a fake file handle number
sockfd = 0xc0ffee

#uncomment this if you want to get into the
#backend cli at this address. mozz's use
#of python decorators means this callback
#wont happen when the decorator is commented.
#@s.at_addr(0x80488b0)
def blah(host):
	host.set_drop_into_cli()

#this is a mockup for a send call.
#break at 0x80488b0, and jump to 0x8048972 after
#executing the callback below. passing a tuple
#of register names to the mockup decorator
#will cause mozz to pass the register values
#to the callback function. the register names
#will be specific to the architecture and/or
#the backend
@s.mockup(0x80488b0, 0x8048972, regset=('sp',))
def fake_send(host, sp):
	#get the inferior object
	inf = host.inferior() 
	#read an uint32 from the inferior
	fd = inf.mem_read_uint32(sp+4)
	ret = inf.mem_read_uint32(sp)
	if fd == sockfd:
		amt = inf.mem_read_uint32(sp+12)
		addr = inf.mem_read_uint32(sp+8)
		data = host.inferior().mem_read_buf(addr, amt)
		print("sent to %x at %x" % (sockfd, ret-5))
		print(data)

		#modify inferior when its SAFE to do so.
		#many debuggers have rules about when an inferior
		#can be safely modified. this is guaranteed to 
		#happen before the inferior starts again.
		#to reiterate, dont modify the inferior directly
		#unless its within one of these callbacks.
		@host.with_inferior()
		def seteax(host):
			#set the return value to the amount sent
			inf.reg_set("eax", amt)
	else:
		print("cant handle fd=%x" % fd)

#function for writing data in a receive mockup
def recv_switch(host, ret, sp, fd, addr, amt):
	inf = host.inferior()
	if ret == 0x80492b2:
		#again, we safely modify inferior memory
		#using a callback within @host.with_inferior()
		@host.with_inferior()
		def mod(host):
			if n > 0:
				inf.mem_write_buf(addr, "B"*n)

			inf.reg_set("eax", n)

	elif ret == 0x8049346:
		@host.with_inferior()
		def mod(host):
			#we use the rand module to 
			#generate a random range for fuzzing
			n = rand.intrange(0, amt)
			if n > 0:
				#write a random buffer
				inf.mem_write_buf(addr, rand.byte_buf(n))

			inf.reg_set("eax", n)
			
	else:
		host.log("dont know this recv")

#similar to above send mockup, but for a recv
@s.mockup(0x8048890, 0x8048972, regset=('sp',))
def fake_recv(host, sp):
	inf = host.inferior() 
	fd = inf.mem_read_uint32(sp+4)
	ret = inf.mem_read_uint32(sp)
	host.log("recv from %x" % ret)
	if fd == sockfd:
		amt = inf.mem_read_uint32(sp+12)
		addr = inf.mem_read_uint32(sp+8)
		recv_switch(host, ret, sp, fd, addr, amt)

	else:
		print("cant handle fd=%x" % fd)

s.mockup(0x80486e0, 0x8048972, regset=('sp',))(fake_recv)

#skip at this address, but also set eax to 0 when
#we continue from 0x80490c1
s.skip(0x80490bc,0x80490c1,regstate={'eax': 0x0})

@s.at_addr(0x8048dee)
def quit(host):
	host.log("set stop flag")
	#signals to mozz that it should abort the
	#inferior and cleanup.
	s.set_flag_stop()

mozz.run_session(s)
```

## backends
mozz defers the task of managing and controlling an inferior
process to a debugger adapter/backend. The adapter must provide
implementations of the `mozz.host.Host` and the `mozz.host.Inf`
classes (see `mozz/host.py`). Additionally, an adapter must
provide an implementation based on the `mozz.adapter.Adapter`
class in `mozz/adapter/__init__.py`. Some backends may provide
a command line interface for use with the `host.set_drop_into_cli()`
flag.

Currently only GDB is supported as a backend (with support
for a command line interface as well; setting the CLI flag
will just put you into the familiar GDB CLI).

## project status
mozz is currently beta software so documentation and many 
features may be lacking.

## license
[GPLv3](http://www.gnu.org/licenses/gpl-3.0.html). See LICENSE or the 
given URL for details.  

