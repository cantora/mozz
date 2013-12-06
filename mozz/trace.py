from collections import namedtuple

import mozz.log
import mozz.err

class AsmMatcher(object):
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

class X86Matcher(AsmMatcher):
	def __init__(self):
		super(X86Matcher, self).__init__(r'(?i)^call', r'(?i)^i?retd?')

class Tracer(object):

	def __init__(self, host, session, matcher):
		self.sess = session
		self.matcher = matcher
		self.seq = []
		self._running = True
		self.sess.on_step()(self.on_step)

		if host.inferior().is_in_step_into_mode():
			self.reset_to_mode = 'into'
		elif host.inferior().is_in_step_over_mode():
			self.reset_to_mode = 'over'
		else:
			self.reset_to_mode = False

		if self.reset_to_mode != 'into':
			host.inferior().enter_step_into_mode()

	def running(self):
		return self._running

	def stop(self, host):
		if self.reset_to_mode == False:
			host.inferior().exit_step_mode()
		elif self.reset_to_mode == 'over':
			host.inferior().enter_step_over_mode()

		self.sess.del_cb_step(self.on_step)
		self._running = False

	def on_step(self, host):
		inf = host.inferior()
		'''
		instr = inf.current_instruction()
		reg_dict = {}
		for (name, v) in inf.register_values():
			reg_dict[name] = v

		record = {
			'instr':         instr,
			'registers':     reg_dict
		}
		'''
		#self.seq.append()
	
class X86Tracer(Tracer):

	def __init__(self, host, session):
		super(X86Tracer, self).__init__(host, session, X86Matcher())

