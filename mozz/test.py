import sys
import unittest

#helper file for tests
def run_test_module(name, file):
	return unittest.main(module=sys.modules[name], argv=[file], verbosity=2, exit=False)
