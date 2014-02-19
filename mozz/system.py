import platform

ARCH_X86_64 = "x86_64"
ARCH_UNKNOWN = "unknown"

def architecture():
	mach = platform.uname()[4]

	if mach == ARCH_X86_64:
		return ARCH_X86_64
	else:
		return ARCH_UNKNOWN
