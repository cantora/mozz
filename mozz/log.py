# Copyright 2013 anthony cantor
# This file is part of mozz.
# 
# mozz is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#  
# mozz is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#  
# You should have received a copy of the GNU General Public License
# along with mozz.  If not, see <http://www.gnu.org/licenses/>.
import logging
import sys

log_obj = None

def set_default_logger(verbosity=0, handler=logging.StreamHandler(sys.stderr)):
	lgr = logging.getLogger("mozz")
	if verbosity >= 2:
		lgr.setLevel(logging.DEBUG)
	elif verbosity == 1:
		lgr.setLevel(logging.INFO)
	else:
		lgr.setLevel(logging.ERROR)

	handler.setLevel(lgr.level)
	lgr.addHandler(handler)
	set_logger(lgr)

def set_logger(logger):
	global log_obj
	#print "set logger to %r at level %d" % (logger, logger.level)
	log_obj = logger

def get_logger():
	global log_obj
	return log_obj

def debug(str):
	global log_obj
	#print("log_obj: %r(%d)" % (log_obj, log_obj.level))
	if log_obj:
		return log_obj.debug(str)
	else:
		return None

def info(str):
	global log_obj
	if log_obj:
		return log_obj.info(str)
	else:
		return None

def warning(str):
	global log_obj
	if log_obj:
		return log_obj.warning(str)
	else:
		return None

def error(str):
	global log_obj
	if log_obj:
		return log_obj.error(str)
	else:
		return None

def traceback_error(str):
	import traceback
	return error(
		"%s\n%s" % (str, traceback.format_exc())
	)
