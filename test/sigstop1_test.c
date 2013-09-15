#include <stdio.h>
#include <signal.h>


int main(int argc, char *argv[]) {
	printf("%s: start\n", __FILE__);
	raise(SIGSTOP);

	printf("%s: exit\n", __FILE__);
	return 0;
}


