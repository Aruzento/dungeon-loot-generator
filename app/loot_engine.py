from __future__ import annotations

import random
from typing import Protocol, Sequence, TypeVar

from app.models import InvalidRollError, LootResult
from app.repository import LootRepository
from app.state_manager import AppState, StateManager

T = TypeVar("T")


class RandomSource(Protocol):
    def random(self) -> float: ...

    def choice(self, sequence: Sequence[T]) -> T: ...


def parse_roll(raw_value: str) -> int:
    value = raw_value.strip()
    try:
        roll = int(value)
    except (TypeError, ValueError) as error:
        raise InvalidRollError("Введите целое число от 1 до 20") from error
    if not 1 <= roll <= 20:
        raise InvalidRollError("Введите целое число от 1 до 20")
    return roll


class LootEngine:
    def __init__(
        self,
        repository: LootRepository,
        state_manager: StateManager,
        rng: RandomSource | None = None,
    ) -> None:
        self.repository = repository
        self.state_manager = state_manager
        self.rng = rng or random.Random()

    def generate(self, raw_roll: str) -> LootResult:
        # Validation deliberately happens before state access and every RNG call.
        roll = parse_roll(raw_roll)
        state = self.state_manager.load()
        chance = state.lucky_chance
        is_lucky = chance >= 100 or self.rng.random() < chance / 100

        if roll == 20:
            pool = self.repository.artifacts("GOOD" if is_lucky else "DANGEROUS")
            if not pool:
                raise RuntimeError("Для результата 20 не найден подходящий пул артефактов")
            artifact = self.rng.choice(pool)
            result = LootResult(
                roll=20,
                name=artifact.name,
                description=artifact.description,
                value_cp=artifact.value_cp,
                is_lucky=is_lucky,
                item_id=artifact.id,
            )
        else:
            pool = self.repository.items_for_roll(roll)
            if not pool:
                raise RuntimeError(f"В базе нет предметов для результата {roll}")
            item = self.rng.choice(pool)
            result = LootResult(
                roll=roll,
                name=item.lucky_name if is_lucky else item.name,
                description=item.lucky_description if is_lucky else item.description,
                value_cp=item.lucky_value_cp if is_lucky else item.value_cp,
                is_lucky=is_lucky,
                item_id=item.id,
            )

        next_chance = 1 if is_lucky else min(100, chance + 1)
        self.state_manager.save(AppState(lucky_chance=next_chance))
        return result


def format_price(value_cp: int) -> str:
    return f"{value_cp:,}".replace(",", " ") + " медных монет"
