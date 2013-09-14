import signal

def signals():
	result = []
	for k in signal.__dict__.keys():
		if k[0:3] == 'SIG':
			result.append(getattr(signal, k))

	return set(result)


