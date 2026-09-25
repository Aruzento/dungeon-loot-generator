from __future__ import annotations

import re
import statistics
import unittest
from collections import Counter

from app.repository import LootRepository


class DatasetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.repo = LootRepository()
        cls.items = cls.repo.all_items()
        cls.artifacts = cls.repo.all_artifacts()

    def test_required_volume_and_distribution(self) -> None:
        self.assertGreaterEqual(len(self.items), 1645)
        for roll in range(1, 20):
            with self.subTest(roll=roll):
                self.assertGreaterEqual(len(self.repo.items_for_roll(roll)), 80)
        self.assertGreaterEqual(len(self.repo.items_for_roll(20)), 125)
        self.assertGreater(len(self.artifacts), 0)

    def test_fields_values_and_ids(self) -> None:
        ids = [entry.id for entry in (*self.items, *self.artifacts)]
        self.assertEqual(len(ids), len(set(ids)))
        for item in self.items:
            with self.subTest(item=item.id):
                self.assertIn(item.roll, range(1, 21))
                self.assertTrue(item.name)
                self.assertTrue(item.description)
                self.assertGreater(item.value_cp, 0)
                self.assertTrue(item.lucky_name)
                self.assertTrue(item.lucky_description)
                self.assertGreater(item.lucky_value_cp, 0)
                self.assertGreaterEqual(item.lucky_value_cp, item.value_cp)
                self.assertTrue(item.tags)

    def test_no_exact_duplicate_records_names_or_descriptions(self) -> None:
        records = [
            (
                item.roll,
                item.name,
                item.description,
                item.value_cp,
                item.lucky_name,
                item.lucky_description,
                item.lucky_value_cp,
            )
            for item in self.items
        ]
        self.assertEqual(len(records), len(set(records)))
        for values, label in (
            ([item.name.casefold() for item in self.items], "names"),
            ([item.lucky_name.casefold() for item in self.items], "lucky names"),
            ([item.description.casefold() for item in self.items], "descriptions"),
            ([item.lucky_description.casefold() for item in self.items], "lucky descriptions"),
        ):
            with self.subTest(label=label):
                self.assertEqual(len(values), len(set(values)))

    def test_no_numbered_filler_or_large_prefix_series(self) -> None:
        numbered = re.compile(r"(?:^|\s)(?:вариант|версия|предмет)?\s*\d+$", re.IGNORECASE)
        self.assertFalse([item.name for item in self.items if numbered.search(item.name)])
        prefixes = Counter()
        for item in self.items:
            prefixes["normal:" + " ".join(item.name.casefold().split()[:2])] += 1
            prefixes["lucky:" + " ".join(item.lucky_name.casefold().split()[:2])] += 1
        self.assertLessEqual(max(prefixes.values()), 5)

    def test_normal_value_medians_have_clear_long_term_growth(self) -> None:
        medians = {
            roll: statistics.median(item.value_cp for item in self.repo.items_for_roll(roll))
            for roll in range(1, 21)
        }
        for lower, upper in ((1, 5), (5, 10), (10, 15), (15, 17), (17, 18), (18, 19), (19, 20)):
            with self.subTest(lower=lower, upper=upper):
                self.assertLess(medians[lower], medians[upper])
        inversions = sum(medians[roll] > medians[roll + 1] for roll in range(1, 20))
        self.assertLessEqual(inversions, 2)

    def test_roll_twenty_items_are_not_artifacts_or_absurdly_priced(self) -> None:
        artifact_ids = {artifact.id for artifact in self.artifacts}
        artifact_names = {
            name.casefold()
            for artifact in self.artifacts
            for name in (artifact.name, artifact.official_name)
        }
        for item in self.repo.items_for_roll(20):
            with self.subTest(item=item.id):
                self.assertNotIn(item.id, artifact_ids)
                self.assertNotIn(item.name.casefold(), artifact_names)
                self.assertNotIn("artifact", item.tags)
                self.assertLess(item.value_cp, 10_000_000)

    def test_artifact_prices_form_a_separate_jackpot_band(self) -> None:
        prices = [artifact.value_cp for artifact in self.artifacts]
        self.assertGreaterEqual(min(prices), 10_000_000)
        self.assertLessEqual(max(prices), 100_000_000)
        self.assertGreater(min(prices), max(item.value_cp for item in self.repo.items_for_roll(20)))

    def test_low_tiers_do_not_use_adventuring_magic_tags(self) -> None:
        forbidden = {"weapon", "armor", "shield", "dagger", "sword", "axe", "bow", "projectile", "magic"}
        for roll in range(1, 11):
            for item in self.repo.items_for_roll(roll):
                with self.subTest(item=item.id):
                    self.assertIn("household", item.tags)
                    self.assertTrue(forbidden.isdisjoint(item.tags))

    def test_rolls_eleven_to_fifteen_are_equipment_tiers(self) -> None:
        for roll in range(11, 16):
            for item in self.repo.items_for_roll(roll):
                with self.subTest(item=item.id):
                    self.assertIn("equipment", item.tags)

    def test_high_tiers_have_explicit_semantic_band_tags(self) -> None:
        expected = {
            16: "transition-magic",
            17: "good-magic",
            18: "strong-magic",
            19: "very-rare",
            20: "exceptional",
        }
        for roll, tag in expected.items():
            for item in self.repo.items_for_roll(roll):
                with self.subTest(item=item.id):
                    self.assertIn(tag, item.tags)

    def test_artifact_fields_and_polarities(self) -> None:
        polarities = {artifact.polarity for artifact in self.artifacts}
        self.assertEqual(polarities, {"GOOD", "DANGEROUS"})
        for artifact in self.artifacts:
            with self.subTest(artifact=artifact.id):
                self.assertEqual(artifact.roll, 20)
                self.assertTrue(artifact.name)
                self.assertTrue(artifact.official_name)
                self.assertTrue(artifact.description)
                self.assertGreater(artifact.value_cp, 0)
                self.assertTrue(artifact.source)
