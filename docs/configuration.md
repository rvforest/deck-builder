# Configuration reference

Projects use TOML. Unknown keys, invalid types, nonfinite dimensions, unsupported
features, and incompatible settings are errors. No expressions or Python code
are evaluated. The specification is immutable after validation.

## Minimal project

```toml
schema_version = 1
units = "inches"

[deck.footprint]
type = "rectangle"
width = 144
length = 192
```

All other settings have defaults. See [the complete example](../examples/rectangle.toml)
for a typical project.

## Fields and defaults

| Section | Field | Default | Meaning |
| --- | --- | --- | --- |
| root | `schema_version` | `1` | Supported configuration version |
| root | `units` | `"inches"` | The only supported unit system |
| `deck` | `elevation` | `24` | Top of the finished decking, above z=0 |
| `deck.footprint` | `type` | `"rectangle"` | Supported footprint shape |
| `deck.footprint` | `width` | required | Footprint extent along world x |
| `deck.footprint` | `length` | required | Footprint extent along world y |
| `framing.joists` | `size` | `"2x8"` | `"2x6"`, `"2x8"`, `"2x10"`, or `"2x12"` |
| `framing.joists` | `direction` | `"y"` | Direction of joist length: `"x"` or `"y"` |
| `framing.joists` | `max_spacing` | `16` | Maximum joist center-to-center spacing |
| `framing.joists` | `material` | `"lumber"` | Material label in the assembly manifest |
| `framing.supports` | `system` | `"blocks"` | Supported foundation representation |
| `framing.supports` | `max_spacing` | `72` | Maximum support center spacing along each joist |
| `framing.supports` | `edge_setback` | `12` | Distance of first/last support center from footprint ends |
| `framing.supports` | `block_height` | `7.75` | Height from block base to bearing surface |
| `framing.supports` | `base_width` | `10.75` | Width of square block base |
| `framing.supports` | `top_width` | `8` | Width of square bearing surface |
| `decking` | `material` | `"composite"` | Material label in the assembly manifest |
| `decking` | `width` | `5.5` | Actual full board width |
| `decking` | `thickness` | `0.94` | Actual board thickness |
| `decking` | `direction` | `"x"` | Board length direction, perpendicular to joists |
| `decking` | `gap` | `0.25` | Fixed gap between neighboring boards; zero is allowed |
| `exports` | `formats` | `["scad", "dxf"]` | Nonempty selection of supported formats |
| `exports` | `views` | `["top", "front", "left", "right"]` | Nonempty DXF view selection; `"back"` is also available |

All dimensions must be positive except gaps, which may be zero. Export selections
must not contain duplicates. Widths and heights are actual dimensions; nominal
lumber names resolve to 1.5-inch thickness and heights of 5.5, 7.25, 9.25, or 11.25.

## Layout rules

Two rim boards cap the joist ends. The first and last joists sit flush with the
other footprint boundaries. Intermediate joists are evenly spaced with centers
no farther apart than `max_spacing`. All framing uses the selected joist stock.

Each joist has support blocks at both end setbacks, with evenly spaced blocks
between them when needed. The setback must be at least the rim thickness and
less than half the joist run. The block top must fit the joist thickness and must
not exceed the base width. Overlapping block bases are rejected. Blocks at the
outer joists can extend beyond the footprint.

Elevation must accommodate decking thickness, joist height, and block height
without placing blocks below z=0. Uniform blocks float above that plane when a
higher elevation is chosen; terrain and elevation-dependent posts are not modeled.

Decking runs perpendicular to the joists and spans the entire footprint in its
length direction. Switching joists to `"x"` also requires setting decking to `"y"`.
Full-width boards are followed by a ripped final board when the remainder exceeds
the gap. A remainder no larger than the gap is left as edge clearance. Exact fits
produce no extra board. Comparisons use an absolute tolerance of 1e-8 inches.
Minimum rip width and purchased stock lengths are not enforced.

To bound resource use, the engine rejects layouts requiring approximately 10,000
members in one spacing operation or more than 10,000 support blocks.

## Coordinates and outputs

The footprint starts at x=0, y=0; z points up. Named views use these coordinates:

| View | Horizontal | Vertical |
| --- | --- | --- |
| top | x | y |
| front | x | z |
| back | -x | z |
| left | -y | z |
| right | y | z |

Opposite elevations mirror around the world origin, so negative drawing coordinates
are expected. DXF silhouettes use transformed geometry and are rounded to ten
decimal places. Layers are `rim`, `joist`, `support`, and `decking`. Each entity's
`DECK_BUILDER` extended data stores its assembly part ID.

`validate` resolves the layout and writes no files. `export` creates the output
directory and overwrites matching filenames. Unrelated files and old exports for
views no longer selected remain in the directory. Use a fresh directory when you
need an exact output set. Configuration and layout errors occur before creating
the output directory; a filesystem failure during export can leave partial output.

The manifest has `schema_version = 1`, inch units, and a `parts` array. Each part
contains its `id`, `role`, `material`, optional `stock` and `cut_length`, and a mesh
of vertices and faces. Mesh faces use outward right-hand winding. Part IDs and
ordering are deterministic for a fixed specification; inserting members may
renumber subsequent parts. DXF file metadata can vary between exports.
