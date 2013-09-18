import gdb
import os
import threading
import traceback

import mozz.host
import mozz.adapter
import mozz.log

class BrkPoint(gdb.Breakpoint, mozz.host.Breakpoint):

	def __init__(self, host, *args, **kwargs):
		super(BrkPoint, self).__init__(*args, **kwargs)
		self.host = host

	def stop(self):
		mozz.debug("mozz_gdb bp %d: hit_count=%r, visible=%r" % (
			self.number, self.hit_count, self.visible
			
		))

		self.host.on_break()
		if self.host.drop_into_cli():
			return True

		if self.host.need_to_flush_inferior_procs():
			gdb.post_event(lambda: self.host.flush_inferior_procs())
			return True

		return False


	
class GDBInf(mozz.host.Inf):

	def __init__(self, inf_id, **kwargs):
		super(GDBInf, self).__init__(**kwargs)
		self.inf_id = inf_id

	def kill(self):
		gdb.execute("kill inferiors %d" % self.inf_id)

	def state(self):
		inf = self.gdb_inf()
		result = 'dead'
		if inf.pid != 0:
			if self.running():
				result = 'running'
			else:
				result = 'stopped'

		return result

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
		frame = self.get_frame()
		pc = frame.pc()

		return pc

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

	def _run(self, *args):
		cmd = "run "

		if len(args) > 0:
			cmd += " ".join(args)

		if self.stdin().filename():
			cmd += "< %s " % (self.stdin().filename())

		if self.stdout().filename():
			cmd += "> %s " % (self.stdout().filename())

		if self.stderr().filename():
			cmd += "2> %s " % (self.stderr().filename())

		gdb.execute(cmd)

	def _cont(self):
		gdb.execute("continue")

	def _symbol_addr(self, name):
		v = gdb.parse_and_eval("(%s)+0" % name)
		return long(v)

class GDBHost(mozz.host.Host):

	def __init__(self, session):
		super(GDBHost, self).__init__(session)

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

		elif isinstance(event, gdb.BreakpointEvent):
			self.on_break_and_stop()


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
			gdb.execute("file %s" % self.session.target)
		except gdb.error as e:
			raise mozz.host.HostErr("session target error: %s" % e)

		self.set_inferior(GDBInf(gdb.selected_inferior().num, **kwargs))
		#runs the inferior until the first stop
		self.inferior().run(*args)
		mozz.debug("finished first exec")
		
		return self.continue_inferior()


class Cmd(gdb.Command):
	
	def __init__ (self, name, type):
		self.name = "mozz-"+name
		super (Cmd, self).__init__(self.name, type)

class GDBAdapter(mozz.adapter.CLIAdapter):

	class State(mozz.adapter.CLIAdapter.State):
		def create_host(self, sess):
			return GDBHost(sess)

	def __init__(self, options):
		super(GDBAdapter, self).__init__(options)
		mozz.log.set_default_logger(verbosity=options.verbose)

		gdb.execute("set python print-stack full")
		gdb.execute("set pagination off")
		
		self.init_cmds()
		
		gdb.events.stop.connect(self.on_stop)
		gdb.events.cont.connect(self.on_cont)
		#gdb.events.new_objfile.connect(self.on_objfile)
		gdb.events.exited.connect(self.on_exit)


	def exit(self):
		gdb.execute("quit")

	def on_stop(self, event):
		if self.running_or_stopped():
			self.state.host.gdb_stop(event)
	
	def on_cont(self, event):
		if self.running_or_stopped():
			self.state.host.gdb_cont(event)
	
	def on_exit(self, event):
		if self.running_or_stopped():
			self.state.host.gdb_exit(event)
	
	def run(self):
		if self.options.session:
			gdb.execute("mozz-run %s" % self.options.session)
	
	def err_exit(self, s, e):
		print("%s: %s\n%s" % (s, e, traceback.format_exc()))
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
	
