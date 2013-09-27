from collections import namedtuple
import logging

import mozz.log

verbosity = 2
log = logging.getLogger("mozz.pattern")
if verbosity >= 2:
	log.setLevel(logging.DEBUG)
elif verbosity == 1:
	log.setLevel(logging.INFO)
else:
	log.setLevel(logging.ERROR)

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
handler = PatternLogHandler()
handler.setLevel(log.level)
log.addHandler(handler)

class SeqRecord(namedtuple('SeqRecordBase', 'id')):
	def __init__(self, id):
		super(SeqRecord, self).__init__(id)

	def __hash__(self):
		return hash(self.id)

	def __eq__(self, other):
		if not isinstance(other, self.__class__):
			return False

		return (self.id == other.id)

	def records(self):
		yield self

class RecursiveSeq(namedtuple('RecursiveSeqBase', 'cycles seq')):
	def __init__(self, cycles, seq):
		if not isinstance(seq, tuple):
			raise TypeError("seq must be a tuple")

		if len(seq) < 1:
			raise ValueError("cannot create empty recursive sequence")

		for a in seq:
			if not isinstance(Record) and not isinstance(RecordTuple):
				raise TypeError("each arg must be a Record or RecordTuple")

		if cycles < 1:
			raise ValueError("cycles must be >= 1. got %d" % cycles)

		super(RecordTuple, self).__init__(cycles, seq)

	def __eq__(self, other):
		if not isinstance(other, self.__class__):
			return False

		return self == other

	@property
	def id(self):
		return self.seq[0].id

	def records(self):
		with depth.plus_one():
			for x in self.seq:
				for record in x.records():
					yield record

	def actual_len(self):
		l = 0
		for r in self.records():
			l += 1

		return l*self.cycles

class Pattern(list):
	def __init__(self, cycles=1, *args, **kwargs):
		super(Pattern, self).__init__(*args, **kwargs)
		self._itrs = 0
		self._offset = 0
		self._cycles = cycles

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

	def expected(self):
		return self[self._offset % len(self)]

	def flattened(self):
		l = []
		for x in self:
			for record in x.records():
				l.append(record)

		return l

	def actual_len(self):
		return len(self.flattened())*self._cycles*(self.iterations+1)

class Foo(object):
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

		if self.pattern.iterations() > 0:
			log.debug("reduce: reduce pattern with %d iterations" % self.pattern.iterations())

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
		else:
			#we only come to reduce if the newest record
			#doesnt match the current pattern, nor any
			#sub-sequences of the current pattern, so
			#this pattern cant possibly work out
			log.debug("reduce: current pattern didnt find any repetitions, so just trash it")
			self.pattern_stack.pop()

	def check_subpatterns(self, new_rec, pattern, parents=[]):
		if isinstance(pattern.expected(), SeqRecord):
			log.debug("check subpatterns: return False")
			return False

		p = Pattern.from_recursive_seq(pattern.expected())
		log.debug("check subpatterns: %r" % p)
		if p.expected() == new_rec:
			for parent in parents:
				self.pattern_stack.push(parent)
			self.pattern_stack.push(p)
			self.pattern.inc_offset()
			log.debug("->subpattern matched. pushed %d patterns" % len(parents)+1)
			return True
		
		with depth.plus_one():
			return self.check_subpatterns(new_rec, p, parents+[pattern])
		
	def check_pattern(self, new_rec):
		log.debug("check pattern: %r" % new_rec)

		if self.known.get(new_rec, 0) < 1:
			log.debug("check pattern: new record is unknown")
			#this will get incremented when new_rec is pushed onto the stack
			self.known[new_rec] = 0 
			with depth.plus_one():
				self.reduce()
		elif self.pattern:
			if self.pattern.expected() == new_rec:
				log.debug("got expected. inc offset")
				self.pattern.inc_offset()
			else:
				log.debug("check pattern: not expected. check subpatterns")
				if not self.check_subpatterns(new_rec, self.pattern):
					log.debug("check pattern: no subpatterns matched. reduce")
					with depth.plus_one():
						self.reduce()
		else:
			log.debug("check pattern: new record not new, but no current pattern")
		
	def reduce_pattern(self):
		log("reduce_pattern: enter")
		plen = len(self.pattern)
		recs = []
		attr_list = []
		
		assert(plen > 1)
		for i in range(plen):
			(rec, attrs)  = self.stack.pop()
			self.known[rec] -= 1
			assert(self.known[rec] >= 0)
			recs.insert(0, rec)
			for attr in attrs:
				attr_list.insert(0, attr)

		assert(len(recs) == plen)
		assert(len(attr_list) == self.pattern.actual_len())
		new_rec = RecursiveSeq(self.pattern.iterations+1, tuple(recs))
		log.debug("reduce pattern: created new record from stack")
		self.pattern_stack.pop()

		self.check_pattern(new_rec)
		self.stack.append( (new_rec, attrs) )
		self.known[new_rec] += 1

	def append(self, id, rec_attrs):
		'''
		@id is a hashable identifier for a data class; i.e. the
		pattern matching alphabet is the set of all data classes.
		@rec_attrs are instance specific attributes of @id
		(attributes that are specific to this location/instance of the
		data class represented by @id in the pattern).
		'''
		log.debug("append: enter")
		new_rec = self.SeqRecord(id)

		self.check_pattern(new_rec)
			
		if not self.pattern and self.known[new_rec] > 0:
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

			log.debug("append: found pattern %r" % p)
			self.pattern_stack.append(p)
			#this current record counts as the first record
			#in the pattern, so we increment the pattern offset
			#right away.
			self.pattern.inc_offset()

		self.stack.append( (new_rec, rec_attrs) )
		self.known[new_rec] += 1
