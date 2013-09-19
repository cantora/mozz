import mozz.session
from mozz.err import Err
from mozz.ioconfig import *

from mozz.session import Session, NumericAddr
import mozz.adapter

from mozz.log import debug, info, warning, error, traceback_error

def run_session(sess):
	return mozz.adapter.current().run_session(sess)

