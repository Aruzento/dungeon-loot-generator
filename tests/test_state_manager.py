from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from app.state_manager import AppState, StateManager


class StateManagerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.path = Path(self.temp_dir.name) / "nested" / "state.json"
        self.manager = StateManager(self.path)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_missing_state_is_created_at_one_percent(self) -> None:
        self.assertEqual(self.manager.load(), AppState(1))
        self.assertTrue(self.path.exists())

    def test_state_survives_new_manager_instance(self) -> None:
        self.manager.save(AppState(37))
        self.assertEqual(StateManager(self.path).load(), AppState(37))

    def test_corrupt_state_is_recovered(self) -> None:
        self.path.parent.mkdir(parents=True)
        self.path.write_text("not json", encoding="utf-8")
        self.assertEqual(self.manager.load(), AppState(1))
        self.assertIn('"lucky_chance": 1', self.path.read_text(encoding="utf-8"))

    def test_out_of_range_state_is_recovered(self) -> None:
        self.path.parent.mkdir(parents=True)
        self.path.write_text('{"lucky_chance": 101}', encoding="utf-8")
        self.assertEqual(self.manager.load(), AppState(1))
