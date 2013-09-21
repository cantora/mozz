import random

def intrange(a, b):
	return random.randint(a, b)

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