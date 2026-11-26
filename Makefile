# Implements: workflow/numbers-traced
.PHONY: check test build install

install:
	uv sync

build:
	@if [ -f scripts/build.py ]; then uv run python scripts/build.py; else echo "build: nothing to build yet"; fi

test:
	uv run pytest -q

check:
	@uv run python checks/check.py && uv run pytest -q
