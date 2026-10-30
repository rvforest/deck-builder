# Deck builder

A configuration-driven deck layout engine. The new package lives in
`src/deck_builder`; the original project-specific implementation is archived in
`legacy/` as reference and is excluded from the package and development checks.

## Development

Install [uv](https://docs.astral.sh/uv/getting-started/installation/), then run:

```sh
uv sync --locked
uv run pre-commit install
uv run pre-commit run --all-files
```

Individual checks:

```sh
uv run ruff check .
uv run ruff format --check .
uv run ty check
uv run pytest
```

The project uses Python 3.12 or newer, with Python 3.13 selected for development.
Commit `uv.lock` when changing dependencies. Pre-commit uses the locked uv
environment so hooks and direct checks use the same tool versions.
