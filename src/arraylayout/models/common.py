"""Shared model types for circuit array specs."""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field

NonEmptyStr = Annotated[str, Field(min_length=1)]
PositiveInt = Annotated[int, Field(ge=1)]
NonNegativeFloat = Annotated[float, Field(ge=0)]
PositiveFloat = Annotated[float, Field(gt=0)]

VersionLiteral = Literal["0.1"]
UnsupportedOptionPolicy = Literal["ignore", "ignore_with_warning", "error"]
RoutingLevel = Literal["full", "partial", "none"]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class PydanticOutput(StrictModel):
    libname: NonEmptyStr
    cellname: NonEmptyStr


class GuardRingOptions(StrictModel):
    left: bool
    right: bool
    top: bool
    bottom: bool


class RoutingOptions(StrictModel):
    nVias: PositiveInt
    wireWidthHor: PositiveFloat
    wireWidthVer: PositiveFloat
    wireWidthPlus: PositiveFloat
    wireWidthMinus: PositiveFloat
    truncVerWires: bool
    truncHorWires: bool
    verWireAssignment: Literal["minus-plus", "separate-plus-minus"]
    horWireAssignment: Literal["all-bottom", "all-top", "symmetric", "separate-plus-minus"]
    verShielding: Literal["shield-pin", "Cdmy_n"]
    horShielding: Literal["device-bus", "plus-minus", "outer-edge"]
    guardRingOptions: GuardRingOptions
    addGuardRingSpacing: NonNegativeFloat


class Advanced(StrictModel):
    horDevSpacing: float
    verDevSpacing: float
    minHorDevBusSpacing: NonNegativeFloat
    minVerDevBusSpacing: NonNegativeFloat
    noRouting: bool
    onlyVerticalWires: bool
    omitHorizontalBus: bool
    deleteFloatingWires: bool
    wireSpaceHor: NonNegativeFloat
    wireSpaceVer: NonNegativeFloat
