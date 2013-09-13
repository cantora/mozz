import gdb
import os
import re

import mozz.host

host = None

class GDBInf(mozz.Inf):
	pass

class GDBHost(mozz.Host):

	def __init__(self, session):
		super(self, GDBHost).__init__(session)

	def set_inferior_file(self, filepath):
		gdb.execute("file %s" % filepath)

	def run_inferior(self, *args, **kwargs):
		self.inf = GDBInf(**kwargs)

		cmd = "run "

		if len(args) > 0:
			cmd += " ".join(args)

		cmd += "< %s " % (inf.stdin_filename)
		cmd += "> %s " % (inf.stdout_filename)
		cmd += "2> %s " % (inf.stderr_filename)

		gdb.execute(cmd)
		if not self.inf.stopped():
			raise Exception("inferior is not stopped yet")

		self.inf.cleanup()
		self.inf = None
		

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
		
	raise Exception("now what?")

def init_cmds():
	class Run(Cmd):
		"""run session. pass the filepath of the session to run"""

		def __init__(self):
			super (Run, self).__init__("run", gdb.COMMAND_RUNNING)

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
	global host
	if host is not None:
		host.on_stop(event)

def on_cont(event):
	if host is not None:
		host.on_cont(event)

def run(options):
	gdb.execute("set python print-stack full")
	
	init_cmds()
	
	gdb.events.stop.connect(on_stop)
	gdb.events.cont.connect(on_cont)

	#create host object
	if options.session:
		gdb.post_event(lambda : gdb.execute("mozz-run %s" % options.session))


