from collections import namedtuple

import mozz.log
import mozz.err

AsmMatcher(object):
	'''
	object that matches certain key instructions
	that a Tracer needs to be able to recognize.
	'''

	def __init__(self, call_reg, ret_reg):
		self.call = call_reg
		self.ret = ret_reg

	def match_reg(self, reg, instruction):
		m = re.search(reg, instruction.str_val)
		if not m:
			return False

		return True

	def is_call(self, instruction):
		return self.match_reg(self.call, instruction)

	def is_ret(self, instruction):
		return self.match_reg(self.ret, instruction)

X86Matcher(object):
	def __init__(self):
		super(X86Matcher, self).__init__(r'(?i)^call', r'(?i)^i?retd?')

class TableRec(object):
	'''
	note: not thread safe.
	'''

	index = [0]

	def __init__(self, instr):
		self.instr = instr
		self._id = self.index[0]
		self.index[0] += 1

	@property
	def id(self):
		return self._id

	def __hash__(self):
		return hash( (self.id, self.instr) )


class Record(namedtuple('RecordBase', 'addr reg_dict')):
	def __init__(self, addr, reg_dict):
		super(Record, self).__init__(addr, frozenset(reg_dict.items()))

class RecordTuple(Tuple):
	def __init__(self, *args):
		for a in args:
			if not isinstance(Record) and not isinstance(RecordTuple):
				raise TypeError("each arg must be a Record or RecordTuple")

		super(RecordTuple, self).__init__(*args)

class PureSegment(SegmentBase):
	def __init__(self, elems):
		self.stack = elems

class Pattern(list):
	def __init__(self, *args, **kwargs):
		super(Pattern, self).__init__(*args, **kwargs)
		self._itrs = 0
		self._offset = 0

	@property
	def iterations(self):
		return self._itrs

	def inc_iterations(self):
		self._itrs += 1

	def inc_offset(self):
		'''
		increment pattern offset and increment pattern iterations
		if offset overflows signifying a completion of the pattern.
		'''
		self._offset += 1
		if self._offset >= len(self):
			self._offset = 0
			self.inc_iterations()

	def expected(self):
		return self[self._offset]


class Segment(SegmentBase):
	'''
	a sequence of instructions and/or segments.
	'''

	def __init__(self, matcher, addr_table):
		self.stack = []
		self.matcher = matcher
		self.addr_table = addr_table
		self.known = set([])
		self.pattern_stack = []

	def is_call(self, instr):
		return matcher.is_call(instr)

	def pop_pattern(self):
		pass

	def append(self, instr, reg_dict):
		addr = int(instr)
		if not addr in self.addr_table:
			tr = TableRec(instr)
			self.addr_table[addr] = tr
		else:
			tr = self.addr_table[addr]

		self.stack.append( 
			self.Record(addr, reg_dict)
		)

		
class Trace(Segment):
	'''
	a top level segment
	'''
	pass
		
class Tracer(object):

	def __init__(self, session, start_addr, matcher):
		self.sess = session
		self.matcher = matcher
		self.seqs = {}
		self.sess.on_step()(self.on_step)
		self.sess.at_addr(start_addr)(self.on_entry)

	def on_entry(self, host):
		host.inferior().enter_step_into_mode()
		#process the current instruction
		self.on_step(host)

	@property
	def seq(self):
		itr = self.session.iteration()
		if itr not in self.seqs:
			self.seqs[itr] = []

		return self.seqs[itr]

	def on_step(self, host):

		inf = host.inferior()
		instr = inf.current_instruction()
		reg_dict = {}
		for (name, v) inf.register_values():
			reg_dict[name] = v

		record = {
			'instr':         instr,
			'registers':     reg_dict
		}

		self.seq.append()

	