from __future__ import annotations

import unittest

from app.repository import LootRepository


class RepositoryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.repo = LootRepository()

    def test_every_regular_roll_can_be_loaded(self) -> None:
        for roll in range(1, 20):
            with self.subTest(roll=roll):
                self.assertGreaterEqual(len(self.repo.items_for_roll(roll)), 55)

    def test_artifact_pools_can_be_loaded(self) -> None:
        self.assertTrue(self.repo.artifacts("GOOD"))
        self.assertTrue(self.repo.artifacts("DANGEROUS"))
