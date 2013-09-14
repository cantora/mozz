#include <stdio.h>
#include <signal.h>

int main(int argc, char *argv[]) {
	raise(SIGSTOP);

	return 0;
}


