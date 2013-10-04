# Copyright 2013 anthony cantor
# This file is part of mozz.
# 
# mozz is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#  
# mozz is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#  
# You should have received a copy of the GNU General Public License
# along with mozz.  If not, see <http://www.gnu.org/licenses/>.
import sys
import unittest
import mozz.util
import os

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

def abs_path(base_file, rel_path):
	return os.path.join(
		os.path.dirname(os.path.abspath(base_file)),
		rel_path
	)
