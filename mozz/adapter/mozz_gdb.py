import gdb
import os
import threading

import mozz.host
import mozz.adapter

class BrkPoint(gdb.Breakpoint, mozz.host.Breakpoint):

	def __init__(self, host, *args, **kwargs):
		super(BrkPoint, self).__init__(*args, **kwargs)
		self.host = host

	def stop(self):
		print("mozz_gdb bp %d: hit_count=%r, visible=%r" % (
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
		print("inferior attrs: num=%r, pid=%r, is_valid=%r" % (
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

class GDBHost(mozz.host.Host):

	def __init__(self, session):
		super(GDBHost, self).__init__(session)

	def log(self, s):
		print(s)

	def selected_is_my_inf(self):
		return gdb.selected_inferior().num == self.inferior().inf_id

	def ignore_callback(self):
		return super(GDBHost, self).ignore_callback() \
			or (not self.selected_is_my_inf())

	def gdb_stop(self, event):
		#print("gdb stop event: signal=%r" % event.stop_signal)

		if isinstance(event, gdb.SignalEvent):
			#gdb seems to use the same names as python std lib for signals
			self.on_stop(event.stop_signal)

		elif isinstance(event, gdb.BreakpointEvent):
			self.on_break_and_stop()


	def gdb_cont(self, event):
		#print("cont event: %r" % event)

		self.on_start()

	def gdb_exit(self, event):
		#print("exit event: %r" % event)

		self.on_exit()

	def set_breakpoint(self, addr):
		return BrkPoint(self, spec=("*0x%x" % addr), type=gdb.BP_BREAKPOINT, internal=True)

	def _run_inferior(self, *args, **kwargs):
		try:
			gdb.execute("file %s" % self.session.target)
		except gdb.error as e:
			raise mozz.host.HostErr("session target error: %s" % e)

		self.set_inferior(GDBInf(gdb.selected_inferior().num, **kwargs))
		#runs the inferior until the first stop
		self.inferior().run(*args)
		print("finished first exec")
		
		return self.continue_inferior()


class Cmd(gdb.Command):
	
	def __init__ (self, name, type):
		self.name = "mozz-"+name
		super (Cmd, self).__init__(self.name, type)

class GDBAdapter(mozz.adapter.Adapter):

	class State(mozz.util.StateMachine):
		IMPORTED 	= 'imported'
		READY 		= 'ready'
		RUNNING 	= 'running'
		STOPPED 	= 'stopped'
		
		def __init__(self, log=None):
			super(GDBAdapter.State, self).__init__(log)
			self.reset()

		def reset(self):
			self.host = None
			self.sess = None
			self.ready_event = None

		def session(self):
			return self.host.session

		def trans_init_imported(self):
			self.ready_event = threading.Event()

		def trans_imported_ready(self, sess):
			self.sess = sess
			self.ready_event.set()

		def wait_for_ready(self):
			self.ready_event.wait()

		def trans_ready_running(self):
			self.host = GDBHost(self.sess)

		def trans_running_stopped(self):
			pass

		def trans_running_ready(self):
			self.host = None

		def trans_stopped_running(self):
			pass

		def trans_running_init(self):
			self.reset()

			
	def __init__(self, options):
		super(GDBAdapter, self).__init__(options)
		def log_state(s):
			print(s)
		self.state = self.State(log_state)
		gdb.execute("set python print-stack full")
		gdb.execute("set pagination off")
		
		self.init_cmds()
		
		gdb.events.stop.connect(self.on_stop)
		gdb.events.cont.connect(self.on_cont)
		#gdb.events.new_objfile.connect(self.on_objfile)
		gdb.events.exited.connect(self.on_exit)

	def run_session(self, sess):
		finished = threading.Event()
		@self.state.register_callback(self.state.RUNNING, self.state.INIT)
		def on_finish():
			finished.set()					

		self.state.transition(self.state.READY, sess)
		finished.wait()
		self.state.delete_callback(
			self.state.RUNNING,
			self.state.INIT, 
			on_finish
		)

	def import_session(self, fpath):		
		t = threading.Thread(target=self.import_session_file, args=(fpath,))
		t.start()

	def cmd_run(self, fpath):
		self.state.transition(self.state.IMPORTED)
		self.import_session(fpath)

		self.state.wait_for_ready()
		return self.cmd_cont(True)

	def trans_from_running(self):
		if self.state.host.has_inferior():
			state = self.state.STOPPED
		elif self.state.session().get_flag_finished():
			state = self.state.INIT
		else:
			state = self.state.READY

		self.state.transition(state)
		return state

	def cmd_cont(self, session_starting=False):
		prev = self.state.transition(self.state.RUNNING)

		if session_starting:
			#notify that the session is about to start
			self.state.session().notify_event_run(self.state.host)
		
		while True:
			if prev == self.state.READY:
				self.state.host.run_inferior()
			elif prev == self.state.STOPPED:
				self.state.host.continue_inferior()
		
			state = self.trans_from_running()
			if state == self.state.INIT and self.options.exit:
				gdb.execute("quit")
				raise Exception("shouldnt get here")
			elif state != self.state.READY:
				break
			
			prev = self.state.transition(self.state.RUNNING)

	def running_or_stopped(self):
		return self.state.currently(
			self.state.RUNNING,
			self.state.STOPPED
		)

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
	
	def init_cmds(self):
		ad = self
		class Run(Cmd):
			"""run session. pass the filepath of the session to run"""
	
			def __init__(self):
				super(Run, self).__init__("run", gdb.COMMAND_RUNNING)
	
			def usage(self):
				print("usage: %s FILEPATH" % (self.name))
				
			def invoke(self, arg, from_tty):
				self.dont_repeat()
				if not os.path.isfile(arg):
					print("invalid session %r" % arg)
					self.usage()
				else:
					ad.cmd_run(arg)

		Run()

		class Cont(Cmd):
			"""continue the stopped session."""
	
			def __init__(self):
				super(Cont, self).__init__("cont", gdb.COMMAND_RUNNING)
	
			def invoke(self, arg, from_tty):
				self.dont_repeat()
				ad.cmd_cont()

		Cont()
	
