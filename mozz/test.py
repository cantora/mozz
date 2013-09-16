import sys
import unittest
import mozz.util

#helper function for test module
def run_test_module(name, file):
	outputfile = mozz.util.python_path_basename(file) + '.out'

	m = sys.modules[name]
	ldr = unittest.loader.defaultTestLoader
	tests = ldr.loadTestsFromModule(m)

	with open(outputfile, 'w') as f:
		duper = mozz.util.IOWriteDuplicator(
			sys.stderr, f
		)
		unittest.runner.TextTestRunner(
			verbosity = 2,
			stream = duper
		).run(tests)