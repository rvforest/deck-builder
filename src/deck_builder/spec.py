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


class Decking(ConfigModel):
    """Decking stock and fixed gaps, with a final ripped board when needed."""

    material: str = Field(default="composite", min_length=1)
    width: Positive = 5.5
    thickness: Positive = 0.94
    direction: Literal["x", "y"] = "x"
    gap: NonNegative = 0.25


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
