PY ?= python3

.PHONY: doctor validate test lint

doctor:
	$(PY) --version
	git --version

validate:
	$(PY) scripts/validate_scaffold.py
	PYTHONPATH=src $(PY) scripts/generate_schemas.py --check
	$(PY) -m compileall -q src tests

test:
	pytest -q

lint:
	ruff check .
