#include <stdio.h>

int loop(int n) {
	int i, j;

	for(i = 0; i < 200; i++) {
		for(j = 0; j < 50; j++) {
			n -= (j*i) << 8;
		}
	}

	return n;
}

int main(int argc, char *argv[]) {
	printf("%s: start\n", __FILE__);
	printf("n = %d\n", loop(0xc0ff));
	printf("%s: exit\n", __FILE__);
	return 0;
}

