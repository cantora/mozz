import mozz.session
from mozz.err import Err

class SessionAlreadyExists(Err):
	pass

class SessionNotFound(Err):
	pass

session_table = {}

def register_session(name, sess):
	global session_table

	if name in session_table:
		raise SessionAlreadyExists("session %s already exists" % self.name)
	else:
		mozz.session_table[name] = sess

	return sess

def get_session(name):
	'''
	find or create a mozz session named @name
	'''
	if not isinstance(name, str) or len(name) < 1:
		raise SessionNotFound("could not find session %s" % name)

	if not name in session_table:
		register_session(name, mozz.session.Session(name))

	return session_table[name]

def make_addr(addr, base=None):
	'''
	make a session runtime address
	'''
	return mozz.session.Addr(addr, base)
