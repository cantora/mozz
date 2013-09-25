#include <stdio.h>

int main(int argc, char *argv[]) {
	const char msg[] = "small lib function\n";

	printf("%s: start\n", __FILE__);
	write(1, msg, sizeof(msg));
	printf("%s: exit\n", __FILE__);
	return 0;
}


