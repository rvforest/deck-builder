"""Strict, versioned project configuration. All internal lengths are inches."""

import tomllib
from pathlib import Path
from typing import Annotated, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

Positive = Annotated[float, Field(gt=0, allow_inf_nan=False)]
NonNegative = Annotated[float, Field(ge=0, allow_inf_nan=False)]
LumberSize = Literal["2x6", "2x8", "2x10", "2x12"]
LUMBER_DIMENSIONS: dict[LumberSize, tuple[float, float]] = {
    "2x6": (1.5, 5.5),
    "2x8": (1.5, 7.25),
    "2x10": (1.5, 9.25),
    "2x12": (1.5, 11.25),
}


class ConfigModel(BaseModel):
    """Base for immutable configuration sections with strict field validation."""

    model_config = ConfigDict(extra="forbid", frozen=True, strict=True, validate_default=True)


class Footprint(ConfigModel):
    """Rectangular plan dimensions measured along the world x and y axes."""

    type: Literal["rectangle"] = "rectangle"
    width: Positive
    length: Positive


class Deck(ConfigModel):
    """Footprint and elevation of the finished decking surface."""

    footprint: Footprint
    elevation: Positive = 24


class Joists(ConfigModel):
    """Joist stock, orientation, and maximum center-to-center spacing."""

    size: LumberSize = "2x8"
    direction: Literal["x", "y"] = "y"
    max_spacing: Positive = 16
    material: str = Field(default="lumber", min_length=1)


class Supports(ConfigModel):
    """Simplified tapered blocks beneath each joist at specified intervals."""

    system: Literal["blocks"] = "blocks"
    max_spacing: Positive = 72
    edge_setback: NonNegative = 12
    block_height: Positive = 7.75
    base_width: Positive = 10.75
    top_width: Positive = 8

    @model_validator(mode="after")
    def check_taper(self) -> Self:
        """Reject an inverted block taper."""
        if self.top_width > self.base_width:
            raise ValueError("supports.top_width must not exceed base_width")
        return self


class Framing(ConfigModel):
    """Framing and support layout options."""

    joists: Joists = Field(default_factory=Joists)
    supports: Supports = Field(default_factory=Supports)


class Border(ConfigModel):
    """Concentric mitered rows using the configured decking stock and gap."""

    rows: Annotated[int, Field(ge=0, le=10)] = 0


class Decking(ConfigModel):
    """Decking stock and fixed gaps, with a final ripped board when needed."""

    material: str = Field(default="composite", min_length=1)
    width: Positive = 5.5
    thickness: Positive = 0.94
    direction: Literal["x", "y"] = "x"
    gap: NonNegative = 0.25
    border: Border = Field(default_factory=Border)


BoundaryName = Literal["front", "right", "back", "left"]


class Stair(ConfigModel):
    """Stacked box stairs attached to a named footprint edge."""

    name: str = Field(pattern=r"^[a-z][a-z0-9_-]*$")
    system: Literal["box"] = "box"
    edge: BoundaryName
    offset: NonNegative = 0
    width: Positive = 48
    tread_depth: Positive = 11
    max_rise: Positive = 7.75
    ground_elevation: NonNegative = 0
    frame_size: LumberSize = "2x8"
    max_spacing: Positive = 16


class Exports(ConfigModel):
    """CAD file formats and orthographic views to generate."""

    formats: tuple[Literal["scad", "dxf"], ...] = ("scad", "dxf")
    views: tuple[Literal["top", "front", "back", "left", "right"], ...] = (
        "top",
        "front",
        "left",
        "right",
    )

    @field_validator("formats", "views", mode="before")
    @classmethod
    def freeze_arrays(cls, value: object) -> object:
        """Convert TOML arrays to tuples without coercing their elements."""
        return tuple(value) if isinstance(value, list) else value

    @model_validator(mode="after")
    def check_selections(self) -> Self:
        """Require unique, nonempty format and view selections."""
        for name, values in (("formats", self.formats), ("views", self.views)):
            if not values or len(values) != len(set(values)):
                raise ValueError(f"exports.{name} must be nonempty and contain no duplicates")
        return self


class Project(ConfigModel):
    """Versioned project specification, validated before layout or file writes."""

    schema_version: Literal[1] = 1
    units: Literal["inches"] = "inches"
    deck: Deck
    framing: Framing = Field(default_factory=Framing)
    decking: Decking = Field(default_factory=Decking)
    exports: Exports = Field(default_factory=Exports)
    stairs: tuple[Stair, ...] = ()

    @field_validator("stairs", mode="before")
    @classmethod
    def freeze_stairs(cls, value: object) -> object:
        """Accept TOML arrays while retaining an immutable stair collection."""
        return tuple(value) if isinstance(value, list) else value

    @model_validator(mode="after")
    def check_layout(self) -> Self:
        """Check dimensions and compatibility across configuration sections."""
        joists = self.framing.joists
        supports = self.framing.supports
        thickness, height = LUMBER_DIMENSIONS[joists.size]
        footprint = self.deck.footprint
        cross, run = footprint.width, footprint.length
        if joists.direction == "x":
            cross, run = run, cross
        if cross <= 2 * thickness or run <= 2 * thickness:
            raise ValueError("footprint must leave room inside the perimeter framing")
        if joists.max_spacing < thickness:
            raise ValueError("joist max_spacing must be at least the lumber thickness")
        if 2 * supports.edge_setback >= run:
            raise ValueError("support edge_setback must be less than half the joist run")
        if supports.edge_setback < thickness:
            raise ValueError("support edge_setback must be at least the rim thickness")
        if supports.top_width < thickness:
            raise ValueError("support top_width must be at least the joist thickness")
        if self.deck.elevation < height + self.decking.thickness + supports.block_height:
            raise ValueError("deck elevation would place support blocks below z=0")
        if joists.direction == self.decking.direction:
            raise ValueError("decking must run perpendicular to joists")
        inset = self.decking.border.rows * (self.decking.width + self.decking.gap)
        if 2 * inset >= min(footprint.width, footprint.length):
            raise ValueError("decking border leaves no room for interior boards")
        names = [stair.name for stair in self.stairs]
        if len(names) != len(set(names)):
            raise ValueError("stair names must be unique")
        for edge in ("front", "right", "back", "left"):
            attached = sorted((s for s in self.stairs if s.edge == edge), key=lambda s: s.offset)
            for a, b in zip(attached, attached[1:], strict=False):
                if a.offset + a.width > b.offset:
                    raise ValueError(f"stairs {a.name!r} and {b.name!r} overlap")
        for stair in self.stairs:
            edge_length = footprint.width if stair.edge in ("front", "back") else footprint.length
            if stair.offset + stair.width > edge_length:
                raise ValueError(f"stair {stair.name!r} extends beyond its edge")
            if stair.ground_elevation >= self.deck.elevation:
                raise ValueError(f"stair {stair.name!r} ground must be below the deck")
            if stair.max_rise <= self.decking.thickness:
                raise ValueError("stair max_rise must exceed decking thickness")
            if stair.width <= 3 or stair.tread_depth <= 3:
                raise ValueError("stairs must leave room inside their box framing")
            if stair.max_spacing < 1.5:
                raise ValueError("stair max_spacing must be at least the frame thickness")
        return self


def load_project(path: Path) -> Project:
    """Load and validate a project from TOML.

    Args:
        path: Path to the project configuration.

    Returns:
        An immutable, validated project specification.

    Raises:
        OSError: If the file cannot be read.
        tomllib.TOMLDecodeError: If the file is not valid TOML.
        pydantic.ValidationError: If the configuration is unsupported or invalid.
    """
    with path.open("rb") as stream:
        data = tomllib.load(stream)
    return Project.model_validate(data)
