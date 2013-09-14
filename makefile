TESTS 		= $(notdir $(patsubst %.py, %, $(wildcard ./test/*_test.py) ) )

.PHONY: example
example: example-bin
	./cli --exit example.py

example-bin: example-bin.c
	gcc -fno-stack-protector -o $@ $< 

test/%_test.bin: test/%_test.c
	gcc -o $@ $<

define test-template
.PHONY: $(1)
$(1): test/$(1).bin
	./cli --exit test/$(1).py

endef

$(foreach test, $(TESTS), $(eval $(call test-template,$(test)) ) )

.PHONY: clean
clean:
	rm -f example-bin core
