import re
import imp
import os

import mozz.err
import mozz.util

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
		f.write("sys.path.append(%r)\n" % (code_dir))
		f.write("import pickle\n")
		f.write("import mozz.adapter\n")
		f.write("from mozz.adapter import mozz_gdb\n")
		f.write("with open(%r, 'r') as f:\n" % (f_args))
		f.write("\tmozz_opts = pickle.load(f)\n")
		f.write("ad = mozz_gdb.Adapter()\n")
		f.write("mozz.adapter.set_current(ad)\n")
		f.write("ad.run(mozz_opts)\n")

	os.execlp("gdb", "gdb", "-x", f_boot, *options.host_args)
	raise Exception("shouldnt get here")

class Adapter(object):
	
	def filepath_module_name(self, fpath):
		mozz.util.python_file_basename(fpath)

	def import_session_file(self, fpath):
		mname = self.filepath_module_name(fpath)
		sess_module = imp.load_source(
			'mozz.session.%s' % mname,
			fpath
		)
	
