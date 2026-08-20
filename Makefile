PY ?= python3

.PHONY: doctor validate test lint

doctor:
	$(PY) --version
	git --version

validate:
	$(PY) scripts/validate_scaffold.py
	$(PY) -m compileall -q src tests

test:
	pytest -q

lint:
	ruff check .
