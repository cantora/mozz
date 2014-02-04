#include <stdio.h>
#include <stdlib.h>

int test_function(int a, char b, const char *buf1, const char *buf2, int *output_var) {
	if(strcmp(buf1, "c00lpass1337") == 0) {
		*output_var = 1234;
		return 0xc001f00d;
	}

	if(strcmp(buf2, "secretadminpass") == 0) {
		*output_var = 3456;
		return 0xa1f;
	}

	if(a == b) {
		*output_var = 4567;
		return 0xc0bb13;
	}

	*output_var = -1;
	return 0;
}

int main(int argc, char *argv[]) {
	char buf[25] = 
		"8*3+1 ch"
		"ars of s"
		"tring...";
	int status, status2;

	printf("%s: start\n", __FILE__);
	
	status = test_function(2345, 'x', buf, "secretadminpass", &status2);
	if(status == 3456 && status2 == 0xa1f) {
		printf("admin pass accepted\n");
		goto done;
	}

	status = test_function(84739, 'z', "c00lpass1337", buf, &status2);
	if(status == 84739 && status2 == 0xc001f00d) {
		printf("normal pass accepted\n");
		goto done;
	}

	status = test_function(72, 72, "asdf", "qwer", &status2);
	if(status == 4567 && status2 == 0xc0bb13) {
		printf("asdfqwer\n");
		goto done;
	}

	printf("default case\n");
done:
	printf("%s: exit\n", __FILE__);
	return 0;
}


