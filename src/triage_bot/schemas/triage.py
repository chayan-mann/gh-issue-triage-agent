from typing import Literal

from pydantic import BaseModel, Field


class Classification(BaseModel):
    """Labels that describe a GitHub issue."""

    labels: list[Literal["bug", "feature", "docs"]] = Field(min_length=1, description="One or more of bug, feature, docs")
    confidence: float = Field(ge=0, le=1)
    reasoning: str = Field(description="One short sentence")


class ReproCheck(BaseModel):
    """Whether a bug report contains enough information to reproduce it."""

    has_repro_steps: bool
    missing: list[str] = Field(default_factory=list, description="Missing items, e.g. steps to reproduce, expected vs actual behaviour, version or environment")


class AssigneeSuggestion(BaseModel):
    """The CODEOWNERS rule that best matches the issue."""

    matched_pattern: str | None = Field(description="Exactly one pattern from the provided CODEOWNERS rules, or null if none fits")
    owners: list[str] = Field(default_factory=list)
    reasoning: str = Field(description="One short sentence")
