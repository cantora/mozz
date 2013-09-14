import mozz.session
from mozz.err import Err
from mozz.ioconfig import *

from mozz.session import Session, Addr
import mozz.adapter

def run_session(sess):
	return mozz.adapter.current().run_session(sess)

