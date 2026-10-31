# Deck builder

A configuration-driven deck layout engine. Describe a deck in TOML, validate its
layout, and generate OpenSCAD and layered DXF drawings without writing Python.

## Quick start

Install [uv](https://docs.astral.sh/uv/getting-started/installation/), then run:

```sh
uv sync --locked
uv run deck-builder validate examples/rectangle.toml
uv run deck-builder export examples/rectangle.toml --output build/
```

Open `build/deck.scad` in OpenSCAD to preview the 3D model. Export also creates
`top.dxf`, `front.dxf`, `left.dxf`, `right.dxf`, and `assembly.json`. The JSON
manifest includes each part's identity, role, material, cutting metadata, and
world-space geometry. OpenSCAD itself is not needed to generate these files.

Copy [examples/rectangle.toml](examples/rectangle.toml) to start a project. Run
`uv run deck-builder --help` or `uv run deck-builder export --help` for CLI options.
The package also supports `uv run python -m deck_builder`.

## Supported layouts

Supported footprints are rectangles and named orthogonal polygons, including
concave L and U shapes. The engine generates framing, tapered support blocks,
straight decking, mitered borders with automatic backing, and stacked box stairs.
Both joist directions are supported. All lengths are inches; finished decking
elevation is measured from z=0.

For a bordered deck with stairs:

```sh
uv run deck-builder export examples/border-and-stairs.toml --output build/stairs/
uv run deck-builder export examples/l-shaped.toml --output build/l-shaped/
uv run deck-builder export examples/u-shaped.toml --output build/u-shaped/
```

Spacing limits are explicit project inputs; the engine does not calculate loads,
select structural spans, or enforce building codes. Blocks have flat bearing tops
and uniform height. Concave decks are partitioned into rectangular framing bays
joined by touching double rims; the manifest records those connections. Border
backing uses continuous bearing assembled from ripped framing stock. Stair framing
is a stack of fully decked box platforms, with boards ripped to match equal rises.

Angled or curved footprints, holes, stringer stairs, railings, purchased stock
length limits, hardware, load calculations, and terrain modeling are outside the
current supported profile. Unsupported configuration fields and layouts that
cannot accommodate the selected framing are rejected.

Explicit support locations and extra blocking are supported; see
[examples/manual-layout.toml](examples/manual-layout.toml). Manual placements are
validated against joist alignment, coverage, spacing, and framing intersections.

DXF output shows each part's projected outline on a layer named by its role.
It includes hidden parts and does not remove hidden lines. Set
`dimensions = true` in `[exports]` to add overall deck dimensions.

See the [configuration reference](docs/configuration.md) for defaults and layout
rules, and the [architecture notes](docs/architecture.md) for extension points.

## Development

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
uv build
```

The project uses Python 3.12 or newer, with Python 3.13 selected for development.
Commit `uv.lock` when changing dependencies. Pre-commit uses the locked uv
environment so hooks and direct checks use the same tool versions.

Use Google-style docstrings for public APIs. Ruff checks docstring conventions,
lint, import ordering, and formatting; ty checks package and test types. Pytest
covers validation, layout invariants, transforms, CAD round trips, and CLI behavior.
GitHub Actions runs the same hooks on Python 3.12 and 3.13 and builds distributions.

The package lives in `src/deck_builder`. The original project-specific scripts are
archived in [legacy/](legacy/README.md), outside the installed package and checks.
