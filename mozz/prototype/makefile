
.PHONY: all
all: .cog.__init__.py

.cog.__init__.py: __init__.py
	cog.py -cer __init__.py
	touch $@
