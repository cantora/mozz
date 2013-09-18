#include <stdio.h>
#include <stdlib.h>

void try_to_get_here(char a) {
	if(a == 'p')
		printf("betcha cant get this to execute!\n");
	else
		printf("oops, 'a' wasnt right. you lose :D\n");
}

int main(int argc, char *argv[]) {
	FILE *fp;
	char buf[24];

	printf("%s: start\n", __FILE__);

	fp = fopen("/tmp/blah/doesntexist.txt", "r");
	if(fp == NULL) {
		printf("file open failed!\n");
		exit(1);
	}

	if(fread(buf, 16, 1, fp) != 16) {
		printf("read failed\n");
		exit(1);
	}
	
	buf[16] = '\0';
	if(strcmp(buf, "purpledrank") == 0)
		try_to_get_here(buf[3]);
	else
		printf("bad password!\n");

	printf("%s: exit\n", __FILE__);
	return 0;
}


