#include <stdio.h>
#include <stdlib.h>

int test_function(int a, char b, short c, unsigned int d, int e,
					const char *buf1, const char *buf2,
					int *output_var) {
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

	printf("c=%x\n", c);
	printf("d=%x\n", d);
	printf("e=%x\n", e);
	if(c+d+e == 0x98989898) {
		*output_var = 345987;
		return 0x8000;
	}
		
	*output_var = -1;
	return 0;
}

void default_case() {
	printf("default case\n");
}

void checkpoint3(int status, int status2) {
	printf("checkpoint3\n");
}

int main(int argc, char *argv[]) {
	char buf[25] = 
		"8*3+1 ch"
		"ars of s"
		"tring...";
	int status, status2;

	printf("%s: start\n", __FILE__);
	
	status = test_function(2345, 'x', 98, 789, 2346,
				buf, "secretadminpass", &status2);
	printf("status = %d, status2 = %x\n", status, status2);
	if(status == 3456 && status2 == 0xa1f) {
		printf("admin pass accepted\n");
		goto done;
	}

	status = test_function(84739, 'z', 2847, 9308, 12345,
				"c00lpass1337", buf, &status2);
	printf("status = %d, status2 = %x\n", status, status2);
	if(status == 84739 && status2 == 0xc001f00d) {
		printf("normal pass accepted\n");
		goto done;
	}

	status = test_function(72, 72, 9374, 1038, 43879,
				"asdf", "qwer", &status2);
	printf("status = %d, status2 = %x\n", status, status2);
	checkpoint3(status, status2);
	if(status == 4567 && status2 == 0xc0bb13) {
		printf("asdfqwer\n");
		goto done;
	}

	default_case();
done:
	printf("%s: exit\n", __FILE__);
	return 0;
}


