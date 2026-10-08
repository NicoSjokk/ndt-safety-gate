.PHONY: install test lint validate-example

install:
	pip install -e ".[dev]"

test:
	pytest -q

lint:
	ruff check .
	ruff format --check .

validate-example:
	ndt-gate validate examples/actions/scale-out-safe.json
	ndt-gate validate examples/actions/scale-out-starves-neighbour.json || true
