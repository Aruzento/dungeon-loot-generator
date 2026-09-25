from __future__ import annotations

import re
import statistics
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.repository import LootRepository


NUMBERED_FILLER = re.compile(
    r"(?:^|\s)(?:вариант|версия|предмет)?\s*\d+$",
    re.IGNORECASE,
)


def duplicates(values: list[str]) -> list[str]:
    return [value for value, count in Counter(values).items() if count > 1]


def main() -> int:
    repo = LootRepository()
    items = repo.all_items()
    artifacts = repo.all_artifacts()
    errors: list[str] = []
    medians: dict[int, int] = {}

    print("Обычные items по уровням")
    print("-" * 62)
    for roll in range(1, 21):
        pool = repo.items_for_roll(roll)
        median = int(statistics.median(item.value_cp for item in pool)) if pool else 0
        if not pool:
            errors.append(f"roll {roll}: пул пуст")
        medians[roll] = median
        print(f"{roll:>2}: {len(pool):>3} | normal median: {median:>9,} cp".replace(",", " "))

    print("-" * 62)
    print(f"TOTAL ITEMS: {len(items)}")
    print(f"ARTIFACTS: {len(artifacts)}")
    print(f"GRAND TOTAL: {len(items) + len(artifacts)}")
    if artifacts:
        artifact_prices = [artifact.value_cp for artifact in artifacts]
        print(
            "ARTIFACT PRICE RANGE: "
            f"{min(artifact_prices):,}–{max(artifact_prices):,} cp".replace(",", " ")
        )

    if len(items) < 1645:
        errors.append(f"обычных items {len(items)}, требуется не менее 1645")
    for roll in range(1, 20):
        count = len(repo.items_for_roll(roll))
        if count < 80:
            errors.append(f"roll {roll}: {count} items, требуется не менее 80")
    if len(repo.items_for_roll(20)) < 125:
        errors.append("roll 20: требуется не менее 125 обычных items")

    ids = [entry.id for entry in (*items, *artifacts)]
    if duplicate_ids := duplicates(ids):
        errors.append(f"дублируются ID: {duplicate_ids[:5]}")

    normal_records: set[tuple[object, ...]] = set()
    for item in items:
        if item.roll not in range(1, 21):
            errors.append(f"{item.id}: roll вне диапазона 1–20")
        text_fields = (item.name, item.description, item.lucky_name, item.lucky_description)
        if not all(field.strip() for field in text_fields) or not item.tags:
            errors.append(f"{item.id}: есть пустое поле")
        if item.value_cp <= 0 or item.lucky_value_cp <= 0:
            errors.append(f"{item.id}: цена должна быть положительной")
        if item.lucky_value_cp < item.value_cp:
            errors.append(f"{item.id}: lucky-цена ниже normal-цены")
        record = (
            item.roll,
            item.name,
            item.description,
            item.value_cp,
            item.lucky_name,
            item.lucky_description,
            item.lucky_value_cp,
            item.tags,
        )
        if record in normal_records:
            errors.append(f"{item.id}: полный дубликат записи")
        normal_records.add(record)

    for values, label in (
        ([item.name.casefold() for item in items], "name"),
        ([item.lucky_name.casefold() for item in items], "lucky_name"),
        ([item.description.casefold() for item in items], "description"),
        ([item.lucky_description.casefold() for item in items], "lucky_description"),
    ):
        if repeated := duplicates(values):
            errors.append(f"дублируется {label}: {repeated[:3]}")

    numbered = [item.name for item in items if NUMBERED_FILLER.search(item.name)]
    if numbered:
        errors.append(f"подозрение на numbered filler: {numbered[:5]}")
    prefixes: Counter[str] = Counter()
    for item in items:
        prefixes["normal: " + " ".join(item.name.casefold().split()[:2])] += 1
        prefixes["lucky: " + " ".join(item.lucky_name.casefold().split()[:2])] += 1
    suspicious = [(prefix, count) for prefix, count in prefixes.items() if count > 5]
    if suspicious:
        errors.append(f"подозрительные серии (>5): {suspicious[:5]}")

    for lower, upper in ((1, 5), (5, 10), (10, 15), (15, 17), (17, 18), (18, 19), (19, 20)):
        if medians[lower] >= medians[upper]:
            errors.append(f"медиана roll {lower} не ниже roll {upper}")

    forbidden_low_tags = {
        "weapon", "armor", "shield", "dagger", "sword", "axe", "bow", "projectile", "magic"
    }
    for roll in range(1, 11):
        for item in repo.items_for_roll(roll):
            if "household" not in item.tags:
                errors.append(f"{item.id}: нет household band tag")
            if not forbidden_low_tags.isdisjoint(item.tags):
                errors.append(f"{item.id}: боевой/магический тег в бытовом tier")

    for roll in range(11, 16):
        for item in repo.items_for_roll(roll):
            if "equipment" not in item.tags:
                errors.append(f"{item.id}: нет equipment band tag")

    expected_band = {
        16: "transition-magic",
        17: "good-magic",
        18: "strong-magic",
        19: "very-rare",
        20: "exceptional",
    }
    for roll, tag in expected_band.items():
        for item in repo.items_for_roll(roll):
            if tag not in item.tags:
                errors.append(f"{item.id}: нет semantic band tag {tag}")

    artifact_ids = {artifact.id for artifact in artifacts}
    artifact_names = {
        name.casefold()
        for artifact in artifacts
        for name in (artifact.name, artifact.official_name)
    }
    roll_twenty = repo.items_for_roll(20)
    for item in roll_twenty:
        if item.id in artifact_ids or item.name.casefold() in artifact_names or "artifact" in item.tags:
            errors.append(f"{item.id}: артефакт попал в обычный roll 20")
        if item.value_cp >= 10_000_000:
            errors.append(f"{item.id}: normal roll 20 оценён как jackpot")

    for artifact in artifacts:
        if artifact.roll != 20:
            errors.append(f"{artifact.id}: artifact.roll должен быть 20")
        if not all((artifact.name, artifact.official_name, artifact.description, artifact.source, artifact.tags)):
            errors.append(f"{artifact.id}: есть пустое поле")
        if not 10_000_000 <= artifact.value_cp <= 100_000_000:
            errors.append(f"{artifact.id}: цена artifact вне диапазона 10–100 млн")
    if artifacts and roll_twenty:
        if min(artifact.value_cp for artifact in artifacts) <= max(item.value_cp for item in roll_twenty):
            errors.append("диапазон artifact не отделён от normal roll 20")

    print("-" * 62)
    print(f"DUPLICATE NAMES: {len(duplicates([item.name.casefold() for item in items]))}")
    print(f"NUMBERED FILLER: {len(numbered)}")
    print(f"SUSPICIOUS PREFIX SERIES: {len(suspicious)}")
    if errors:
        print(f"VALIDATION FAILED: {len(errors)} error(s)")
        for error in errors[:25]:
            print(f"- {error}")
        return 1
    print("VALIDATION PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
