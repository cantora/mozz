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
import random

def intrange(a, b):
	return random.randint(a, b)

def choice():
	return random.randint(0, 1) == 0

def intrange_gen(a, b):
	while True:
		yield intrange(a, b)

def n_intranges(n, a, b):
	i = 0
	for rint in intrange_gen(a, b):
		yield rint
		i += 1
		if i > (n-1):
			break

def byte():
	return intrange(0, 255)

def bytes():
	return intrange_gen(0, 255)

def n_bytes(n):
	return n_intranges(n, 0, 255)
		
def byte_buf(amt):
	return "".join([
		chr(b) for b in n_bytes(amt)
	])

def intrange_buf(amt, a, b):
	return "".join([
		chr(x) for x in n_intranges(amt, a, b)
	])

def printable():
	return intrange(0x20, 0x7e)

def printable_char():
	return chr(printable())

def alpha_lower():
	return intrange(0x61, 0x7a)

def alpha_upper():
	return intrange(0x41, 0x5a)
