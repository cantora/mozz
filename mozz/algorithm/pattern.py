from collections import namedtuple
import logging

import mozz.log

class PatternLogHandler(logging.Handler):

	def flush(self):
		pass

	def emit(self, record):
		try:
			msg = (" "*depth.n) + self.format(record)
			mozz.log.debug(msg)
		except:
			self.handleError(record)

class Depth(object):

	def __init__(self):
		self._n = 0

	@property
	def n(self):
		return self._n

	def plus_one(self):
		depth = self
		class Tmp(object):
			def __enter__(self):
				depth._n += 1

			def __exit__(self, ty, val, traceback):
				depth._n -= 1

		return Tmp()

depth = Depth()

verbosity = 2
log = logging.getLogger("pattern")

if verbosity >= 2:
	log.setLevel(logging.DEBUG)
elif verbosity == 1:
	log.setLevel(logging.INFO)
else:
	log.setLevel(logging.ERROR)

handler = PatternLogHandler()
handler.setLevel(log.level)
log.addHandler(handler)

class SeqRecord(namedtuple('SeqRecord', 'id')):
	def __init__(self, id):
		super(SeqRecord, self).__init__(id)

	def __str__(self):
		return str(self.id)

	def __repr__(self):
		return repr(self.id)

	def __hash__(self):
		return hash(self.id)

	def __eq__(self, other):
		if not isinstance(other, self.__class__):
			return False

		return (self.id == other.id)

	def ids(self):
		yield self.id

	def actual_len(self):
		return 1

class RecursiveSeq(namedtuple('RecursiveSeq', 'cycles seq')):
	def __init__(self, cycles, seq):
		l = 0
		for a in seq:
			l += 1
			if not isinstance(a, RecursiveSeq) \
					and not isinstance(a ,SeqRecord):
				raise TypeError("each arg must be a RecursiveSeq or SeqRecord, got %r" % (seq,))

		if l < 1:
			raise ValueError("cannot create empty recursive sequence")

		if cycles < 1:
			raise ValueError("cycles must be >= 1. got %d" % cycles)

		super(RecursiveSeq, self).__init__(cycles, seq)

	def __repr__(self):
		return "%r*%d" % (self.seq, self.cycles)

	def print_tree(self, depth=0):
		ws = " "*depth
		s = ["%s(\n" % ws]
		for x in self.seq:
			pt = getattr(x, 'print_tree', False)
			if pt:
				s.append(pt(depth+1))
			else:
				s.append(ws + " ")
				s.append(repr(x) + "\n")

		s.append("%s)*%d\n" % (ws, self.cycles))
		return "".join(s)

	def __eq__(self, other):
		if not isinstance(other, self.__class__):
			return False

		return self.seq == other.seq and self.cycles == other.cycles

	@property
	def id(self):
		return self.seq[0].id

	def ids(self):
		with depth.plus_one():
			for i in range(self.cycles):
				for x in self.seq:
					for id in x.ids():
						yield id

	def actual_len(self):
		l = 0
		for r in self.ids():
			l += 1

		return l*self.cycles

class Pattern(list):
	def __init__(self, cycles=1, *args, **kwargs):
		super(Pattern, self).__init__(*args, **kwargs)
		self._itrs = 0
		self._offset = 0
		self._cycles = cycles

	def __repr__(self):
		return "%s*%d" % (super(Pattern, self).__repr__(), self._cycles)

	@staticmethod
	def from_recursive_seq(rs):
		if isinstance(rs, SeqRecord):
			return Pattern(1, [rs])
		else:
			return Pattern(rs.cycles, rs.seq)

	@property
	def cycles(self):
		return self._cycles

	@property
	def iterations(self):
		return self._itrs

	def inc_iterations(self):
		self._itrs += 1

	@property
	def offset(self):
		return self._offset

	def inc_offset(self):
		'''
		increment pattern offset and increment pattern iterations
		if offset overflows signifying a completion of the pattern.
		'''
		self._offset += 1
		if self._offset >= (len(self)*self._cycles):
			self._offset = 0
			self.inc_iterations()

	def el_at_offset(self, offset):
		return self[offset % len(self)]

	def expected(self):
		return self.el_at_offset(self._offset)

	def actual_len(self):
		return self.iterations*self.cycles*len(self) + self.offset

class Matcher(object):
	'''
	a sequence of items and/or segments.
	'''

	def __init__(self):
		self.stack = []
		self.known = {}
		self.pattern_stack = []

	@property
	def pattern(self):
		if len(self.pattern_stack) > 0:
			return self.pattern_stack[-1]

		return None

	def reduce(self):
		if not self.pattern:
			log.debug("reduce: no pattern to reduce")
			return

		if self.pattern.iterations >= 2 \
				or (self.pattern.iterations == 1 and \
					self.pattern.cycles > 1):
			log.debug("reduce: reduce pattern with %d iterations" % self.pattern.iterations)

			#this pattern found some repetitions
			if self.pattern.offset != 0:
				log.debug("reduce: pattern is incomplete with offset %d" % self.pattern.offset)
				#the current repetition got broken unevenly, but
				#the earlier repetitions are still usable, so pull
				#the bad stuff off the stack temporarily
				tmp = self.stack[-(self.pattern.offset+1):-1]
				log.debug("reduce: saved %d items from the stack" % len(tmp))
			else:
				tmp = None

			self.reduce_pattern()
			if tmp:
				#restore the stack
				log.debug("reduce: restore %d items from the stack" % len(tmp))
				self.stack.extend(tmp)
			return True
		else:
			#we only come to reduce if the newest record
			#doesnt match the current pattern, nor any
			#sub-sequences of the current pattern, so
			#this pattern cant possibly work out
			log.debug("reduce: current pattern didnt find any repetitions")
			log.debug("-->trashing %r" % self.pattern)
			self.pattern_stack.pop()
			return False

	def check_subpatterns(self, new_rec, pattern, parents=[]):
		if isinstance(pattern.expected(), SeqRecord):
			log.debug("check subpatterns: expected is a SeqRecord")
			return False

		log.debug("check subpatterns: of pattern %r, expected=%r" % (
			pattern, pattern.expected())
		)
		p = Pattern.from_recursive_seq(pattern.expected())
		log.debug("check subpatterns: subpattern=%r" % p)
		if p.expected() == new_rec:
			log.debug("->subpattern matched.")
			for parent in parents:
				log.debug("->push subpattern %r" % (parent))
				self.pattern_stack.append(parent)
			log.debug("->push subpattern %r" % (p))
			self.pattern_stack.append(p)
			self.pattern.inc_offset()
			return True
		
		with depth.plus_one():
			return self.check_subpatterns(new_rec, p, parents+[pattern])
		
	def check_pattern(self, new_rec):
		log.debug("check pattern: new_rec=%r" % (new_rec,))

		if not self.is_known(new_rec):
			log.debug("check pattern: %r is unknown" % (new_rec,))

		if self.pattern:
			if self.pattern.expected() == new_rec:
				log.debug("got expected. inc offset")
				self.pattern.inc_offset()
			else:
				log.debug("check pattern: not expected, expected %r" % (self.pattern.expected(),) )
				if not self.check_subpatterns(new_rec, self.pattern):
					log.debug("check pattern: no subpatterns matched. reduce")
					with depth.plus_one():
						if self.reduce():
							with depth.plus_one():
								self.check_pattern(new_rec)
		else:
			log.debug("check pattern: no current pattern")
		
	def reduce_pattern(self):
		plen = len(self.pattern)
		actual_len = self.pattern.actual_len()
		attr_list = []
		log.debug("reduce_pattern: %d sequence, %d iters, total=%d" % (
			plen, self.pattern.iterations, actual_len
		))
		
		assert(plen > 0)
		assert(actual_len >= plen*2)
		for i in range(actual_len):
			(rec, attrs)  = self.stack.pop()
			self.sub_from_known(rec)
			assert(self.known[rec] >= 0)
			for attr in attrs:
				attr_list.insert(0, attr)

		log.debug("reduce pattern: attr_list=%r" % attr_list)
		assert(len(attr_list) == actual_len)
		new_rec = RecursiveSeq(
			self.pattern.cycles*self.pattern.iterations,
			tuple(self.pattern)
		)
		log.debug("reduce pattern: created new record from stack")
		self.pattern_stack.pop()

		self.check_pattern(new_rec)
		self.stack.append( (new_rec, attrs) )
		self.add_to_known(new_rec)

	def is_known(self, rec):
		return self.known.get(rec, 0) > 0

	def add_to_known(self, rec):
		self.known[rec] = self.known.get(rec, 0) + 1

	def sub_from_known(self, rec):
		self.known[rec] = self.known.get(rec, 0) - 1

	def add(self, id, rec_attrs):
		'''
		@id is a hashable identifier for a data class; i.e. the
		pattern matching alphabet is the set of all data classes.
		@rec_attrs are instance specific attributes of @id
		(attributes that are specific to this location/instance of the
		data class represented by @id in the pattern).
		'''
		log.debug("append: %r" % id)
		new_rec = SeqRecord(id)

		self.check_pattern(new_rec)
			
		if not self.pattern and self.is_known(new_rec):
			log.debug("append: no current pattern, search for pattern starting with %r" % new_rec)
			#if we dont currently have any patterns we should find a new
			#pattern where we are.
			p = Pattern()
			for i in range(len(self.stack)):
				idx = -(i+1)
				(rec, _) = self.stack[idx]
				p.insert(0, rec)
				if new_rec == rec:
					break
			else:
				raise Exception("%r in known set, but not found in stack!" % new_rec)

			p.inc_iterations()
			log.debug("append: found pattern %r" % p)
			self.pattern_stack.append(p)
			#this current record counts as the first record
			#in the pattern, so we increment the pattern offset
			#right away.
			self.pattern.inc_offset()

		self.stack.append( (new_rec, [rec_attrs]) )
		self.add_to_known(new_rec)
		log.debug("append: current stack=%r" % [x for (x,y) in self.stack])
		log.debug("append: current pattern stack=%r" % self.pattern_stack)

	def finish(self):
		self.reduce()
		return self.stack
