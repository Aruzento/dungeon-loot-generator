from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Item:
    id: str
    roll: int
    name: str
    description: str
    value_cp: int
    lucky_name: str
    lucky_description: str
    lucky_value_cp: int
    tags: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class Artifact:
    id: str
    roll: int
    name: str
    official_name: str
    description: str
    value_cp: int
    polarity: str
    source: str
    tags: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class LootResult:
    roll: int
    name: str
    description: str
    value_cp: int
    is_lucky: bool
    item_id: str


class InvalidRollError(ValueError):
    """Raised when the entered physical d20 result is not an integer from 1 to 20."""
