

.PHONY: example
example: example-bin
	./example.py

example-bin: example-bin.c
	gcc -fno-stack-protector -o $@ $< 

.PHONY: clean
clean:
	rm -f example-bin core
