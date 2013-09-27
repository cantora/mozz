import unittest

import mozz
from mozz.test import run_test_module
from mozz.algorithm import pattern

class Test(unittest.TestCase):
	
	def gen_pattern(self):
		alphabet = [chr(x) for x in range(0x41, 0x5b)]
		
	def test_example(self):
		f = pattern.Foo()
		


run_test_module(__name__, __file__)
