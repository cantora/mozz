import gdb
import os

import mozz.host
import mozz.adapter

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
			self.on_break()


	def gdb_cont(self, event):
		#print("cont event: %r" % event)

		self.on_start()

	def gdb_exit(self, event):
		#print("exit event: %r" % event)

		self.on_exit()
		
	def _run_inferior(self, *args, **kwargs):
		try:
			gdb.execute("file %s" % self.session.target)
		except gdb.error as e:
			raise mozz.host.HostErr("session target error: %s" % e)

		self.set_inferior(GDBInf(gdb.selected_inferior().num, **kwargs))
		cmd = "run "

		if len(args) > 0:
			cmd += " ".join(args)

		if self.inferior().stdin().filename():
			cmd += "< %s " % (self.inferior().stdin().filename())

		if self.inferior().stdout().filename():
			cmd += "> %s " % (self.inferior().stdout().filename())

		if self.inferior().stderr().filename():
			cmd += "2> %s " % (self.inferior().stderr().filename())

		self.invoke_callback(mozz.cb.INFERIOR_PRE)
		#runs the inferior until the first stop
		gdb.execute(cmd)
		
		while self.should_continue():
			gdb.execute("cont")

		self.clear_inferior()


class Cmd(gdb.Command):
	
	def __init__ (self, name, type):
		self.name = "mozz-"+name
		super (Cmd, self).__init__(self.name, type)

class Adapter(mozz.adapter.Adapter):
	
	def __init__(self):
		self.host = None

		gdb.execute("set python print-stack full")
		gdb.execute("set pagination off")
		
		self.init_cmds()
		
		gdb.events.stop.connect(self.on_stop)
		gdb.events.cont.connect(self.on_cont)
		#gdb.events.new_objfile.connect(self.on_objfile)
		gdb.events.exited.connect(self.on_exit)

	def run_session(self, sess):
		if not self.host is None:
			raise Exception("host already exists")
	
		self.host = GDBHost(sess)
		sess.notify_event_run(self.host)
		self.host = None
	
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
					try:
						ad.import_session_file(arg)
					except mozz.host.HostErr as e:
						print(str(e))
	
		Run()
	
	def on_stop(self, event):
		if self.host is not None:
			self.host.gdb_stop(event)
	
	def on_cont(self, event):
		if self.host is not None:
			self.host.gdb_cont(event)
	
	def on_exit(self, event):
		if self.host is not None:
			self.host.gdb_exit(event)
	
	def run(self, options):
		if options.session:
			#gdb.post_event(lambda : gdb.execute("mozz-run %s" % options.session))
			gdb.execute("mozz-run %s" % options.session)
			if options.exit:
				gdb.execute("quit")
	
