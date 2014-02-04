import unittest

import mozz
from mozz.test import run_test_module, abs_path

class Test(unittest.TestCase):

	def test_mockup_function(self):
		s = mozz.Session(abs_path(__file__, "function_test.bin"))

		mozz.run_session(s)

run_test_module(__name__, __file__)
