import gdb
import os
import re
import sys

import mozz.host

host = None

class GDBInf(mozz.host.Inf):

	def __init__(self, inf_id, **kwargs):
		super(GDBInf, self).__init__(**kwargs)
		self.inf_id = inf_id

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
		print("inferior: %r" % inf)
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
		return (not self.has_inferior()) \
			or (not self.selected_is_my_inf())

	def on_stop(self, event):
		print("stop event: signal=%r" % event.stop_signal)

		if self.ignore_callback():
			return

		if isinstance(event, gdb.SignalEvent):
			#gdb seems to use the same names as python std lib for signals
			self.inferior().on_stop(event.stop_signal)
		elif isinstance(event, gdb.BreakpointEvent):
			self.inferior().on_break()


	def on_cont(self, event):
		print("cont event: %r" % event)

		if self.ignore_callback():
			return

		self.inferior().on_start()
		self.inferior().dump()

	def on_exit(self, event):
		print("exit event: %r" % event)
		if self.ignore_callback():
			return

		self.inferior().on_exit()
		
	def run_inferior(self, *args, **kwargs):
		gdb.execute("file %s" % self.session.target)

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

		#runs the inferior until the first stop
		gdb.execute(cmd)
		
		while self.should_continue():
			gdb.execute("cont")

		self.clear_inferior()
		

class Cmd(gdb.Command):
	
	def __init__ (self, name, type):
		self.name = "mozz-"+name
		super (Cmd, self).__init__(self.name, type)


def run_session(fpath):
	global host
	if not host is None:
		raise Exception("host already exists")

	sess_module = __import__(re.sub(r'\.py$', '', fpath))
	sess = sess_module.main()

	host = GDBHost(sess)
	sess.notify_event_run(host)


def init_cmds():
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
				return
			else:				
				return run_session(arg)

	Run()

def on_stop(event):
	if host is not None:
		host.on_stop(event)

def on_cont(event):
	if host is not None:
		host.on_cont(event)

def on_exit(event):
	if host is not None:
		host.on_exit(event)

def run(options):
	gdb.execute("set python print-stack full")
	gdb.execute("set pagination off")
	
	init_cmds()
	
	gdb.events.stop.connect(on_stop)
	gdb.events.cont.connect(on_cont)
	#gdb.events.new_objfile.connect(on_objfile)
	gdb.events.exited.connect(on_exit)

	#CREATE host object
	if options.session:
		#gdb.post_event(lambda : gdb.execute("mozz-run %s" % options.session))
		gdb.execute("mozz-run %s" % options.session)


