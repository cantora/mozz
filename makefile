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
	@echo '######################################################################'; done
	@echo '############# TEST $(1) '
	@echo '######################################################################'; done
	@./cli --exit test/$(1).py > test/$(1).log 2>&1
	@cat test/$(1).out 2>/dev/null || { echo 'test $(1) failed to produce output'; false; }
	@echo

endef

$(foreach test, $(TESTS), $(eval $(call test-template,$(test)) ) )

tests: $(TESTS)

.PHONY: clean
clean:
	rm -f example-bin core
	find ./test -iname '*.out' -print -delete
	find . -iname '*.pyc' -print -delete
