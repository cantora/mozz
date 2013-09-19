#include <stdio.h>
#include <stdlib.h>
#include <signal.h>

void vuln(char *str, FILE *fd) {
	char buf[32];
	char buf2[32];
	int amt;

	if( (amt = fread(buf2, 1, 16, fd)) < 1)
		exit(2);
	buf2[amt] = '\0';

	sprintf(buf, "thing: %s: %s", buf2, str);

	puts(buf);
}

int main(int argc, char *argv[]) {
	int i, x;
	FILE *fd;

	printf("example.c: enter\n");
	printf("\targc = %d\n", argc);

	raise(SIGKILL);

	for(i = 0; i < argc; i++) {
		if(i == 2 && argv[2][0] == 'b')
			exit(2345);
		else if(i == 5) {
			if((fd = fopen("/tmp/doesntexist.txt", "r")) == NULL)
				exit(1);

			vuln(argv[5], fd);
			fclose(fd);
		}
	}

	printf("example.c: exit\n");
	x = 1/0;
	printf("div by zero %d\n", x);

	return 0;
}


