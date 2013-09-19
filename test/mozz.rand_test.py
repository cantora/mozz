import unittest

import mozz
from mozz.test import run_test_module
from mozz import rand

class Test(unittest.TestCase):
	
	def test_intrange_gen(self):
		i = 0
		for rint in rand.intrange_gen(0, 56):
			self.assertTrue(isinstance(rint, int))
			i += 1
			if i > 99998:
				break

		self.assertEqual(i, 99999)

	def test_each_intrange(self):
		i = 0
		for rint in rand.n_intranges(20, 0, 987):
			self.assertTrue(isinstance(rint, int))
			i += 1
			if i > 25:
				break

		self.assertEqual(i, 20)

	def test_byte(self):
		self.assertTrue(isinstance(rand.byte(), int))

	def test_n_bytes(self):
		for b in rand.n_bytes(234):
			self.assertTrue(isinstance(b, int))

	def test_byte_buf(self):
		bb = rand.byte_buf(28)
		self.assertEqual(len(bb), 28)
		for b in bb:
			self.assertTrue(isinstance(b, bytes))

	
run_test_module(__name__, __file__)
