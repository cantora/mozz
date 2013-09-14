import signal

def signals():
	result = []
	for k in signal.__dict__.keys():
		if k[0:3] == 'SIG':
			result.append(k)

	return set(result)

for sig in signals():
	exec '%s = %r' % (sig, sig)
