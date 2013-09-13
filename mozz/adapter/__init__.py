

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
		f.write("from mozz.adapter import mozz_gdb\n")
		f.write("with open(%r, 'r') as f:\n" % (f_args))
		f.write("\tmozz_opts = pickle.load(f)\n")
		f.write("mozz_gdb.run(mozz_opts)\n")

	os.execlp("gdb", "gdb", "-x", f_boot, *options.host_args)
	raise Exception("shouldnt get here")



