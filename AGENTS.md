# Working in this repository

## Product direction

Decks are described in declarative TOML configuration. Users should not need to
write Python to build a supported design. Keep project-specific dimensions out
of library code. Only accept configuration options whose behavior is implemented.

The pipeline is configuration → validated specification → layout → immutable
assembly → exporters. Layout chooses physical parts; exporters draw those parts.
Keep drawing conventions separate from physical geometry. Layout assumptions and
unsupported configurations must be explicit rather than silently approximated.

## Code conventions

- Use the `src/deck_builder` package layout and Python 3.12-compatible syntax.
- Use uv for dependencies, environments, commands, and builds. Commit `uv.lock`
  with dependency changes. Do not maintain parallel pip requirements files.
- Use Typer for the CLI, Pydantic for strict immutable config, and frozen
  dataclasses for geometry and assemblies.
- Use type annotations and Google-style docstrings for public APIs.
- Keep modules focused. Extract reusable geometry and layout operations instead
  of growing another deck inheritance hierarchy or a large orchestration method.
- Preserve part identity, material, and cutting metadata through transforms.
- Use inches internally. Apply transforms before view projection, with outward
  right-hand face winding in internal meshes.
- Keep `legacy/` as reference. It is not a compatibility target or part of the
  supported package, and should remain outside normal tooling checks.

## Validation and tests

Run these checks as appropriate to each change:

```sh
uv run --locked ruff check .
uv run --locked ruff format --check .
uv run --locked ty check
uv run --locked pytest
uv run --locked pre-commit run --all-files
uv build
```

Pre-commit runs lint, formatting, type checking, and tests. Fix failures rather
than bypassing hooks. Test layout invariants, invalid configurations, transforms,
and exported geometry. Prefer semantic CAD round trips over complete DXF file
snapshots. Use CLI integration tests for user-visible behavior. Do not add tests
that merely repeat an implementation's formulas.

## Delivery

- Continue making incremental, reviewable commits as working stages complete.
- Update README, configuration reference, architecture notes, and examples when
  behavior or supported features change.
- Keep supported features and remaining roadmap work clearly distinguished.
- Report checks actually run and any material limits of the implementation.
- Preserve unrelated user changes. Do not publish, push, or contact others
  without an instruction authorizing it.
