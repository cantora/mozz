# Copyright 2013 anthony cantor
# This file is part of mozz.
# 
# mozz is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#  
# mozz is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#  
# You should have received a copy of the GNU General Public License
# along with mozz.  If not, see <http://www.gnu.org/licenses/>.
import gdb
import os
import threading
import traceback
import re
import threading
import logging
import sys

import mozz.host
import mozz.adapter
import mozz.log

#this is pretty hacky, but its the only solution ive found
#for the following problem: sometimes we want to silence
#output from gdb commands to the console, so we call
#gdb.execute(..., False, True), but this will also silence
#all of our mozz.log.*, and host.log(...) output, which is
#bad. under the hood, gdb simply replaces sys.stdout with
#their own I/O object (which doesnt support the .fileno method),
#so we can circumvent it by opening stdout directly from the
#file descriptor.
real_stdout = os.fdopen(1, 'w')

def gdb_log(msg):
	real_stdout.write(msg+"\n")
	real_stdout.flush()

class BrkPoint(gdb.Breakpoint, mozz.host.Breakpoint):

	def __init__(self, host, *args, **kwargs):
		super(BrkPoint, self).__init__(*args, **kwargs)
		self.host = host
		self.silent = True

	def stop(self):
		try:
			mozz.debug("mozz_gdb bp %d: hit_count=%r, visible=%r" % (
				self.number, self.hit_count, self.visible
			))
	
			self.host.on_break()
			if self.host.need_to_flush_inferior_procs():
				gdb.post_event(lambda: self.host.flush_inferior_procs())
				return True
	
			if self.host.drop_into_cli() \
					or not self.host.should_continue() \
					or self.host.inferior().is_in_step_mode():
				return True
		except Exception as e:
			gdb_log("exception during breakpoint processing: %s\n%s" % (e, traceback.format_exc()))
			self.host.set_drop_into_cli()
			return True

		return False

def gdb_int_exec(cmd):
	'''
	need to defer all printing and catch all exceptions during this
	functions execution, and then print and re-raise.
	'''	
	return gdb.execute(cmd, False, True)
	
class GDBInf(mozz.host.Inf):

	def __init__(self, inf_id, **kwargs):
		super(GDBInf, self).__init__(**kwargs)
		self.inf_id = inf_id

	def _entry_point(self):
		s = gdb_int_exec("info files")
		m = re.search(r'Entry point: 0x([a-fA-F0-9]+)', s)
		if not m:
			raise Mozz.InfErr("failed to find entry point of inferior")

		return int(m.group(1), 16)

	def kill(self):
		gdb_int_exec("kill inferiors %d" % self.inf_id)

	def is_alive(self):
		inf = self.gdb_inf()
		if inf.pid != 0:
			return True
		return False

	def _pid(self):
		return self.gdb_inf().pid

	def gdb_inf(self):
		for inf in gdb.inferiors():
			if self.inf_id == inf.num:
				return inf

	def dump(self):
		inf = self.gdb_inf()
		mozz.debug("inferior attrs: num=%r, pid=%r, is_valid=%r" % (
			inf.num, inf.pid, inf.is_valid()
		))

	def reg_pc(self):
		return self.reg("pc")

	def reg_sp(self):
		return self.reg("sp")

	def reg_set(self, name, value):
		gdb_int_exec("set $%s = 0x%x" % (name, value))

	def reg_set_pc(self, value):
		return self.reg_set("pc", value)

	def reg_set_sp(self, value):
		return self.reg_set("sp", value)

	def reg(self, name):
		v = gdb.parse_and_eval("$%s" % name)
		return long(v)

	'''
	not needed, but might be useful later
	def get_frame(self):
		try:
			frame = gdb.selected_frame()
		except gdb.error:
			raise NoFrame("no frame is selected")

		self.assert_frame(frame)

		return frame

	def assert_frame(self, frame):
		if not frame.is_valid():
			raise Exception("expected valid frame")
		#if frame.type() != gdb.NORMAL_FRAME:
		#	raise Exception("expected frame.type == NORMAL_FRAME. got: %s" % frame.type())
	'''

	def _run(self, *args):
		cmd = "run "

		if len(args) > 0:
			cmd += " ".join(args) + " "

		if self.stdin().filename():
			cmd += "< %s " % (self.stdin().filename())

		if self.stdout().filename():
			cmd += "> %s " % (self.stdout().filename())

		if self.stderr().filename():
			cmd += "2> %s " % (self.stderr().filename())

		mozz.debug("run inferior with command %r" % cmd)
		gdb_int_exec(cmd)

	def _cont(self):
		#print "cont: \n%s" % 
		gdb_int_exec("continue")

	def _step_into(self):
		#print "si: \n%s" % 
		gdb_int_exec("si")

	def _step_over(self):
		#print "so: \n%s" % 
		gdb_int_exec("ni")

	def _symbol_addr(self, name):
		v = gdb.parse_and_eval("(%s)+0" % name)
		return long(v)

	def mem_write(self, addr, data):
		bs = "".join([chr(x) for x in data])
		self.mem_write_buf(addr, bs)

	def mem_write_buf(self, addr, data):
		self.gdb_inf().write_memory(addr, data)

	def mem_read(self, addr, sz):
		data = self.gdb_inf().read_memory(addr, sz)
		if isinstance(data, memoryview):
			return data.tolist()
		else:
			return [ord(x) for x in data]

	def mem_read_buf(self, addr, sz):
		data = self.gdb_inf().read_memory(addr, sz)
		if isinstance(data, memoryview):
			return data.tobytes()
		else:
			return bytes(data)

	def registers(self):
		s = gdb_int_exec("info reg")
		reg = r'([^\s]+)\s'
		result = set([])

		for line in s.split('\n'):
			m = re.match(reg, line)
			if not m:
				raise InfErr("could not parse reg name from line %r" % line)

			result.add(m[1])

		return result

	def disassemble(self, addr, amt=1):
		for i in gdb.Architecture.disassemble(start_pc=addr, count=amt):
			data = self.mem_read(i['addr'], i['length'])
			yield mozz.host.Instruction(i['asm'], i['addr'], data)

class GDBHost(mozz.host.Host):

	def __init__(self, session):
		super(GDBHost, self).__init__(session)

	def log(self, msg):
		gdb_log(msg)

	def selected_is_my_inf(self):
		return gdb.selected_inferior().num == self.inferior().inf_id

	def ignore_callback(self):
		return super(GDBHost, self).ignore_callback() \
			or (not self.selected_is_my_inf())

	def gdb_stop(self, event):
		#mozz.debug("gdb stop event: signal=%r" % event.stop_signal)

		if isinstance(event, gdb.SignalEvent):
			#gdb seems to use the same names as python std lib for signals
			self.on_stop(event.stop_signal)

	def gdb_cont(self, event):
		#mozz.debug("cont event: %r" % event)

		self.on_start()

	def gdb_exit(self, event):
		#mozz.debug("exit event: %r" % event)

		self.on_exit()

	def set_breakpoint(self, addr):
		if isinstance(addr, (int,long)):
			s = ("*0x%x" % addr)
		else:
			raise TypeError("unexpected address type %r" % addr)

		return BrkPoint(self, spec=s, type=gdb.BP_BREAKPOINT, internal=True)

	def _run_inferior(self, *args, **kwargs):
		try:
			gdb_int_exec("file %s" % self.session.target)
		except gdb.error as e:
			raise mozz.host.HostErr("session target error: %s" % e)

		self.set_inferior(GDBInf(gdb.selected_inferior().num, **kwargs))
		#runs the inferior until the first stop
		self.inferior().run(*args)
		
		return self.continue_inferior()


class Cmd(gdb.Command):
	
	def __init__ (self, name, type):
		self.name = "mozz-"+name
		super (Cmd, self).__init__(self.name, type)

class GDBLogHandler(logging.Handler):

	def flush(self):
		pass

	def emit(self, record):
		try:
			msg = self.format(record)
			gdb_log(msg)
		except:
			self.handleError(record)

class GDBAdapter(mozz.adapter.CLIAdapter):

	class State(mozz.adapter.CLIAdapter.State):
		def create_host(self, sess):
			return GDBHost(sess)

	def __init__(self, options):
		super(GDBAdapter, self).__init__(options)
		self.exiting = False		
		mozz.log.set_default_logger(verbosity=options.verbose, handler=GDBLogHandler())

		gdb_int_exec("set python print-stack full")
		gdb_int_exec("set pagination off")
		
		self.init_cmds()
		
		gdb.events.stop.connect(self.on_stop)
		gdb.events.cont.connect(self.on_cont)
		#gdb.events.new_objfile.connect(self.on_objfile)
		gdb.events.exited.connect(self.on_exit)

	def exit(self):
		gdb_int_exec("quit")

	def exit_if_exception(self, fn):
		try:
			fn()
		except Exception as e:
			self.err_exit("error during callback", e)

	def on_stop(self, event):
		if self.running_or_stopped() and not self.exiting:
			self.exit_if_exception(lambda: self.state.host.gdb_stop(event))
	
	def on_cont(self, event):
		if self.running_or_stopped() and not self.exiting:
			self.exit_if_exception(lambda: self.state.host.gdb_cont(event))
	
	def on_exit(self, event):
		if self.running_or_stopped() and not self.exiting:
			self.exit_if_exception(lambda: self.state.host.gdb_exit(event))
	
	def run(self):
		if self.options.session:
			gdb.execute("mozz-run %s" % self.options.session)
	
	def err_exit(self, s, e):
		self.exiting = True
		gdb_log("%s: %s\n%s" % (s, e, traceback.format_exc()))
		self.exit()

	def init_cmds(self):
		ad = self
		class Run(Cmd):
			"""run session. pass the filepath of the session to run"""
	
			def __init__(self):
				super(Run, self).__init__("run", gdb.COMMAND_RUNNING)
	
			def usage(self):
				print("usage: %s FILEPATH" % (self.name))
				
			def invoke(self, arg, from_tty):
				try:
					self.dont_repeat()
					if not os.path.isfile(arg):
						print("invalid session %r" % arg)
						self.usage()
					else:
						ad.cmd_run(arg)
				except Exception as e:
					ad.err_exit("uncaught exception in %r command" % self.name, e)

		Run()

		class Cont(Cmd):
			"""continue the stopped session."""
	
			def __init__(self):
				super(Cont, self).__init__("cont", gdb.COMMAND_RUNNING)
	
			def invoke(self, arg, from_tty):
				try:
					self.dont_repeat()
					ad.cmd_cont()
				except Exception as e:
					ad.err_exit("uncaught exception in %r command" % self.name, e)

		Cont()
	
