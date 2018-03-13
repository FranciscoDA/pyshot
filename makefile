INTERPRETER=/usr/bin/env python3

pyshot: *.py
	$(INTERPRETER) -m zipapp . -o $@ -p="$(INTERPRETER)"
