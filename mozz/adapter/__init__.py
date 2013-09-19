import re
import imp
import os
import threading

import mozz.err
import mozz.util
import mozz.log

class AdapterErr(mozz.err.Err):
	pass

current_adapter = None
def current():
	global current_adapter
	if not current_adapter:
		raise AdapterErr("no adapter is currently selected")

	return current_adapter

def set_current(mod):
	global current_adapter
	current_adapter = mod

def gdb_run(options):
	import pickle
	import os

	code_dir = os.path.join(os.path.realpath(os.path.dirname(__file__)), "..", "..")
	f_args = "/tmp/mozz-arg.pkl"
	with open(f_args, 'w') as f:
		pickle.dump(options, f)
	f_boot = "/tmp/mozz-bootstrap.py"
	with open(f_boot, 'w') as f:
		map(f.write, [
			"sys.path.append(%r)\n" % (code_dir),
			"import pickle\n",
			"import mozz.adapter\n",
			"from mozz.adapter import mozz_gdb\n",
			"with open(%r, 'r') as f:\n" % (f_args),
			"\tmozz_opts = pickle.load(f)\n",
			"ad = mozz_gdb.GDBAdapter(mozz_opts)\n",
			"mozz.adapter.set_current(ad)\n",
			"ad.run()\n"
		])

	os.execlp("gdb", "gdb", "-x", f_boot, *options.host_args)
	raise Exception("shouldnt get here")

class Adapter(object):
	
	def __init__(self, options):
		self.options = options

	def filepath_module_name(self, fpath):
		mozz.util.python_file_basename(fpath)

	def import_session_file(self, fpath):
		mname = self.filepath_module_name(fpath)
		sess_module = imp.load_source(
			'mozz.session.%s' % mname,
			fpath
		)

	def exit(self):
		'''
		quit out of the adapter host
		'''
		raise NotImplementedError("not implemented")

class CLIAdapter(Adapter):

	class State(mozz.util.StateMachine):
		#INIT                               #we are ready import a session file
		EXECUTING       = 'executing'       #we are executing the session file
		SESSION         = 'session'         #we have a session
		RUNNING         = 'running'         #the session has a running inferior
		STOPPED         = 'stopped'         #the inferior for the session has stopped
		EXECFAIL        = 'execfail'        #something went wrong while executing the session file
		FINISHED        = 'finished'        #the current session has finished
		
		def __init__(self, log=None):
			super(CLIAdapter.State, self).__init__(log)
			self.reset()

		def reset(self):
			self.host = None
			self.sess = None

		def session(self):
			return self.host.session

		def trans_init_executing(self):
			pass

		def trans_executing_execfail(self):
			pass

		def trans_execfail_init(self):
			self.reset()

		def trans_executing_session(self, sess):
			self.sess = sess

		def trans_session_running(self):
			self.host = self.create_host(self.sess)

		def create_host(self, sess):
			raise NotImplementedError("not implemented")

		def trans_running_stopped(self):
			pass

		def trans_running_session(self):
			self.host = None

		def trans_stopped_running(self):
			pass

		def trans_running_finished(self):
			pass

		def trans_finished_session(self, sess):
			self.reset()
			self.sess = sess

		def trans_finished_init(self):
			self.reset()


	def __init__(self, options):
		super(CLIAdapter, self).__init__(options)
		self.state = self.State(mozz.debug)

	def run_session(self, sess):
		with self.state.a_block_until(None, self.state.FINISHED):
			self.state.transition(self.state.SESSION, sess)
	
		self.state.session().notify_event_finish(self.state.host)

	def import_session_file(self, fpath):
		itr = self.state.iteration()
		try:
			super(CLIAdapter, self).import_session_file(fpath)
		except Exception as e:
			mozz.traceback_error("failed to import session %r: %s" % (fpath, e))

		#if we never set the state to SESSION, `cmd_run` is still
		#waiting, so we have to release it
		if itr == self.state.iteration() \
				and self.state.currently(self.state.EXECUTING):
			self.state.transition(self.state.EXECFAIL)
		else:
			#reset the state so it can accept a new session
			self.state.transition(self.state.INIT)

	def import_session(self, fpath):		
		t = threading.Thread(target=self.import_session_file, args=(fpath,))
		t.start()

	def cmd_run(self, fpath):
		with self.state.a_block_until(self.state.EXECUTING, None):
			self.state.transition(self.state.EXECUTING)
			self.import_session(fpath)

		if not self.state.currently(self.state.SESSION): 
			#session file caused and error
			self.state.transition(self.state.INIT)
			raise Exception("failed to load session %r" % fpath)

		return self.cmd_cont(True)

	def trans_from_running(self):
		if self.state.host.has_inferior():
			state = self.state.STOPPED
		elif self.state.session().get_flag_finished():
			state = self.state.FINISHED
		else:
			state = self.state.SESSION

		return state

	def cmd_cont(self, session_starting=False):
		prev = self.state.transition(self.state.RUNNING)

		while True:
			if session_starting:
				#notify that the session is about to start
				self.state.session().notify_event_run(self.state.host)
				session_starting = False
			
			if prev == self.state.SESSION:
				self.state.host.run_inferior()
			elif prev == self.state.STOPPED:
				self.state.host.continue_inferior()
		
			state = self.trans_from_running()

			if state == self.state.FINISHED:
				#setup our notification before state transition to
				#avoid a race condition
				with self.state.a_block_until(self.state.FINISHED, None):
					self.state.transition(state)
					#wait until the session finishes. when the session
					#is done the state will change from FINISHED 
					#to INIT only if the session file completes its execution.
					#otherwise  it will run another session in which case we
					#will transition to SESSION

				#update the local state variable
				state = self.state.current()

				if self.options.exit and state == self.state.INIT:
					#if this is a one shot, we want to exit here, as
					#a transition from FINISHED to INIT signals the
					#end of execution of the session file
					self.exit()					
					raise Exception("shouldnt get here")
				elif state == self.state.SESSION:
					session_starting = True
			else:
				self.state.transition(state)

			if state != self.state.SESSION:
				break
			
			prev = self.state.transition(self.state.RUNNING)

	def running_or_stopped(self):
		return self.state.currently(
			self.state.RUNNING,
			self.state.STOPPED
		)

