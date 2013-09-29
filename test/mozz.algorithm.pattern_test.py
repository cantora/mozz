import unittest

import mozz
from mozz.test import run_test_module
from mozz.algorithm import pattern
import mozz.log
import mozz.rand
mozz.log.set_default_logger(2)

def seq_recs(s):
	return [
		pattern.SeqRecord(x) for x in s
	]

def rec_seq(cycles, *args):
	return [pattern.RecursiveSeq(cycles, args)]

class Test(unittest.TestCase):

	def chars_in_tree(self, seq):
		for subseq in seq:
			print repr(subseq)
			if isinstance(subseq, str) and len(subseq) == 1:
				print "yield %r" % subseq
				yield subseq
			else:
				self.chars_in_tree(subseq)

	def test_example(self):
		m = pattern.Matcher()
		tree = rec_seq(1, *(
			seq_recs("asdf") +
			rec_seq(3, *(
				seq_recs("a") +
				rec_seq(3, *seq_recs("x")) +
				seq_recs("b")
			)) +
			seq_recs("qwer")
		))[0]

		for x in tree.ids():
			m.add(x, {})

		result = rec_seq(1, *[x for (x, _) in m.finish()])[0]
		#print(repr(result))
		self.assertEqual(tree, result)

	def test_recursive_seq(self):
		tree = rec_seq(1, *(
			seq_recs("asdf") +
			rec_seq(3, *(
				seq_recs("a") +
				rec_seq(3, *seq_recs("x")) +
				seq_recs("b")
			)) +
			seq_recs("qwer")
		))[0]

		self.assertEqual(4 + 3*5 + 4, tree.actual_len())
		#print(repr(tree))
		ids = []
		for x in tree.ids():
			#print(repr(x))
			ids.append(x)

		self.assertEqual("asdfaxxxbaxxxbaxxxbqwer", "".join(ids))

	def random_tree(self, max_depth):
		def _random_tree(max_depth):
			n = mozz.rand.intrange(2, 20)
			children = []
			for i in range(n):
				if max_depth > 1 and mozz.rand.choice():
					children.append(
						rec_seq(mozz.rand.intrange(2, 10), *_random_tree(max_depth-1))[0]
					)
				else:
					children.append(pattern.SeqRecord(chr(mozz.rand.alpha_lower())))

			return children

		return rec_seq(1, *_random_tree(max_depth))[0]

	def test_random_trees(self):
		mozz.log.debug("\n")
		for i in range(1):
			tree = self.random_tree(2)
			#mozz.log.debug(tree.print_tree())
			m = pattern.Matcher()
			for id in tree.ids():
				m.add(id, {})

			result = rec_seq(1, *[x for (x, _) in m.finish()])[0]
			if tree != result:
				mozz.debug("tree:")
				mozz.debug(tree.print_tree())
				mozz.debug("result:")
				mozz.debug(result.print_tree())
			self.assertEqual(tree, result)
			

run_test_module(__name__, __file__)
