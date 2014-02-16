MODULE_TESTS		= $(notdir $(patsubst %.py, %, $(wildcard ./test/mozz.*_test.py) ) )
SESSION_TESTS		= $(filter-out \
							$(MODULE_TESTS), \
							$(notdir $(patsubst %.py, %, $(wildcard ./test/*_test.py) ) ) \
					  )

.PHONY: example
example: example-bin
	./cli --exit example.py

example-bin: example-bin.c
	gcc -fno-stack-protector -o $@ $< 

test/%_test.bin: test/%_test.c
	gcc -o $@ $<

test/mockup_fakefile_test.bin: test/mockup_basic_test.bin
	cd test && ln -s $(notdir $<) $(notdir $@)

test/skip_basic_test.bin: test/mockup_basic_test.bin
	cd test && ln -s $(notdir $<) $(notdir $@)

test/cb_remove_test.bin: test/signal1_test.bin
	cd test && ln -s $(notdir $<) $(notdir $@)

define test-template
.PHONY: $(1)
$(1): $(3)
	@echo '######################################################################';
	@echo '############# TEST $(1) '
	@echo '######################################################################';
	@rm -f test/$(1).out test/$(1).log
	@$(2) > test/$(1).log 2>&1
	@cat test/$(1).out 2>/dev/null || { echo 'test $(1) failed to produce output'; false; }
	@echo

endef

define sess-test-template
$(call test-template,$(1),./cli --exit -vvvv test/$(1).py,test/$(1).bin)
endef

define mod-test-template
$(call test-template,$(1),PYTHONPATH='$(CURDIR):$$$$PYTHONPATH' python test/$(1).py)
endef

$(foreach test, $(SESSION_TESTS), $(eval $(call sess-test-template,$(test)) ) )
$(foreach test, $(MODULE_TESTS), $(eval $(call mod-test-template,$(test)) ) )

.PHONY: session-tests
session-tests: $(SESSION_TESTS)

.PHONY: module-tests
module-tests: $(MODULE_TESTS)

.PHONY: tests
tests: module-tests session-tests

.PHONY: clean
clean:
	rm -f example-bin core
	find ./test -iname '*.out' -print -delete
	find . -iname '*.pyc' -print -delete
