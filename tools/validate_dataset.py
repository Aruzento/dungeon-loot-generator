from __future__ import annotations

import statistics
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.repository import LootRepository


def main() -> int:
    repo = LootRepository()
    all_names: list[str] = []
    all_descriptions: list[str] = []
    prefix_counts: Counter[str] = Counter()

    print("Распределение и медианы обычной стоимости")
    print("-" * 58)
    total = 0
    for roll in range(1, 20):
        items = repo.items_for_roll(roll)
        total += len(items)
        median = int(statistics.median(item.value_cp for item in items))
        print(f"roll {roll:>2}: {len(items):>3} | медиана: {median:>12,}".replace(",", " "))
        for item in items:
            all_names.extend((item.name.casefold(), item.lucky_name.casefold()))
            all_descriptions.extend((item.description.casefold(), item.lucky_description.casefold()))
            prefix_counts["обычный: " + " ".join(item.name.casefold().split()[:2])] += 1
            prefix_counts["lucky: " + " ".join(item.lucky_name.casefold().split()[:2])] += 1

    artifacts = repo.all_artifacts()
    all_names.extend(artifact.name.casefold() for artifact in artifacts)
    all_descriptions.extend(artifact.description.casefold() for artifact in artifacts)
    print(f"roll 20: {len(artifacts):>3} | артефакты GOOD/DANGEROUS")
    print(f"TOTAL:   {total + len(artifacts)} ({total} обычных + {len(artifacts)} артефактов)")

    duplicate_names = [name for name, count in Counter(all_names).items() if count > 1]
    duplicate_descriptions = [text for text, count in Counter(all_descriptions).items() if count > 1]
    suspicious = [(prefix, count) for prefix, count in prefix_counts.items() if count > 5]
    print("-" * 58)
    print(f"Полные дубликаты названий: {len(duplicate_names)}")
    print(f"Полные дубликаты описаний: {len(duplicate_descriptions)}")
    print(f"Подозрительные серии по первым двум словам (>5): {len(suspicious)}")
    return 1 if duplicate_names or duplicate_descriptions or suspicious else 0


if __name__ == "__main__":
    raise SystemExit(main())
