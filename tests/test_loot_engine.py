from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from app.loot_engine import LootEngine, format_price, parse_roll
from app.models import InvalidRollError
from app.repository import LootRepository
from app.state_manager import AppState, StateManager


class StubRandom:
    def __init__(self, rolls: list[float]) -> None:
        self.rolls = iter(rolls)
        self.random_calls = 0
        self.choice_calls = 0

    def random(self) -> float:
        self.random_calls += 1
        return next(self.rolls)

    def choice(self, sequence):
        self.choice_calls += 1
        return sequence[0]


class LootEngineTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.state_path = Path(self.temp_dir.name) / "state.json"
        self.states = StateManager(self.state_path)
        self.repo = LootRepository()

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_first_failure_changes_one_to_two(self) -> None:
        rng = StubRandom([0.99])
        result = LootEngine(self.repo, self.states, rng).generate("1")
        self.assertFalse(result.is_lucky)
        self.assertEqual(self.states.load().lucky_chance, 2)

    def test_second_failure_changes_two_to_three(self) -> None:
        self.states.save(AppState(2))
        LootEngine(self.repo, self.states, StubRandom([0.99])).generate("7")
        self.assertEqual(self.states.load().lucky_chance, 3)

    def test_lucky_success_resets_thirty_seven_to_one(self) -> None:
        self.states.save(AppState(37))
        result = LootEngine(self.repo, self.states, StubRandom([0.10])).generate("9")
        self.assertTrue(result.is_lucky)
        self.assertEqual(self.states.load().lucky_chance, 1)

    def test_hundred_percent_is_guaranteed_without_probability_call(self) -> None:
        self.states.save(AppState(100))
        rng = StubRandom([])
        result = LootEngine(self.repo, self.states, rng).generate("12")
        self.assertTrue(result.is_lucky)
        self.assertEqual(rng.random_calls, 0)
        self.assertEqual(self.states.load().lucky_chance, 1)

    def test_invalid_input_neither_changes_state_nor_uses_rng(self) -> None:
        self.states.save(AppState(28))
        rng = StubRandom([0.0])
        engine = LootEngine(self.repo, self.states, rng)
        for raw in ("", "0", "21", "-1", "abc", "1.5"):
            with self.subTest(raw=raw), self.assertRaises(InvalidRollError):
                engine.generate(raw)
        self.assertEqual(self.states.load().lucky_chance, 28)
        self.assertEqual(rng.random_calls, 0)
        self.assertEqual(rng.choice_calls, 0)

    def test_low_roll_lucky_uses_variant_from_same_record(self) -> None:
        self.states.save(AppState(100))
        result = LootEngine(self.repo, self.states, StubRandom([])).generate("1")
        item = self.repo.items_for_roll(1)[0]
        self.assertEqual(result.item_id, item.id)
        self.assertEqual(result.name, item.lucky_name)
        self.assertFalse(result.is_artifact)
        self.assertNotIn(result.item_id, {a.id for a in self.repo.all_artifacts()})

    def test_roll_twenty_without_lucky_uses_regular_item(self) -> None:
        result = LootEngine(self.repo, self.states, StubRandom([0.99])).generate("20")
        self.assertIn(result.item_id, {item.id for item in self.repo.items_for_roll(20)})
        self.assertNotIn(result.item_id, {a.id for a in self.repo.all_artifacts()})
        self.assertFalse(result.is_artifact)

    def test_roll_twenty_with_lucky_uses_artifact(self) -> None:
        self.states.save(AppState(100))
        rng = StubRandom([])
        result = LootEngine(self.repo, self.states, rng).generate("20")
        self.assertIn(result.item_id, {a.id for a in self.repo.all_artifacts()})
        self.assertTrue(result.is_artifact)
        self.assertEqual(rng.choice_calls, 1)

    def test_artifact_can_never_drop_without_lucky(self) -> None:
        artifact_ids = {artifact.id for artifact in self.repo.all_artifacts()}
        for roll in range(1, 21):
            with self.subTest(roll=roll):
                self.states.save(AppState(1))
                result = LootEngine(self.repo, self.states, StubRandom([0.99])).generate(str(roll))
                self.assertNotIn(result.item_id, artifact_ids)
                self.assertFalse(result.is_artifact)

    def test_roll_nineteen_lucky_stays_non_artifact(self) -> None:
        self.states.save(AppState(100))
        result = LootEngine(self.repo, self.states, StubRandom([])).generate("19")
        item = self.repo.items_for_roll(19)[0]
        self.assertEqual(result.item_id, item.id)
        self.assertEqual(result.name, item.lucky_name)
        self.assertFalse(result.is_artifact)
        self.assertNotIn(result.item_id, {a.id for a in self.repo.all_artifacts()})

    def test_parsing_and_price_format(self) -> None:
        self.assertEqual(parse_roll(" 20 "), 20)
        self.assertEqual(format_price(2_450_000), "2 450 000 медных монет")
