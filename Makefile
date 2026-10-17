.PHONY: test lint format spell check fix

test:
	uv run pytest

lint:
	uv run ruff check .

format:
	uv run ruff format --check .

spell:
	uv run codespell

# Everything, read-only, fix separated
check: test lint format spell

fix:
	uv run ruff check . --fix
	uv run ruff format .
	$(MAKE) check
