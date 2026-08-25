format:
	uv run ruff format
	uv run ruff check --select I --fix

lint:
	uv run ruff check

lint-fix:
	uv run ruff check --fix

test:
	uv run pytest
