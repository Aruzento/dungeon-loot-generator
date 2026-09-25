from __future__ import annotations

import csv
import sys
from collections import defaultdict
from pathlib import Path

from app.models import Artifact, Item


def bundled_root() -> Path:
    """Return a path that works both from source and from a PyInstaller bundle."""
    bundle_dir = getattr(sys, "_MEIPASS", None)
    if bundle_dir:
        return Path(bundle_dir)
    return Path(__file__).resolve().parent.parent


class LootRepository:
    def __init__(self, data_dir: Path | None = None) -> None:
        self.data_dir = data_dir or bundled_root() / "data"
        self._items_by_roll: dict[int, list[Item]] = defaultdict(list)
        self._artifacts_by_polarity: dict[str, list[Artifact]] = defaultdict(list)
        self._load_items(self.data_dir / "items.csv")
        self._load_artifacts(self.data_dir / "artifacts.csv")

    def _load_items(self, path: Path) -> None:
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            for row in csv.DictReader(handle):
                item = Item(
                    id=row["id"].strip(),
                    roll=int(row["roll"]),
                    name=row["name"].strip(),
                    description=row["description"].strip(),
                    value_cp=int(row["value_cp"]),
                    lucky_name=row["lucky_name"].strip(),
                    lucky_description=row["lucky_description"].strip(),
                    lucky_value_cp=int(row["lucky_value_cp"]),
                    tags=tuple(tag.strip() for tag in row["tags"].split(",") if tag.strip()),
                )
                self._items_by_roll[item.roll].append(item)

    def _load_artifacts(self, path: Path) -> None:
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            for row in csv.DictReader(handle):
                artifact = Artifact(
                    id=row["id"].strip(),
                    roll=int(row["roll"]),
                    name=row["name"].strip(),
                    official_name=row["official_name"].strip(),
                    description=row["description"].strip(),
                    value_cp=int(row["value_cp"]),
                    polarity=row["polarity"].strip().upper(),
                    source=row["source"].strip(),
                    tags=tuple(tag.strip() for tag in row["tags"].split(",") if tag.strip()),
                )
                self._artifacts_by_polarity[artifact.polarity].append(artifact)

    def items_for_roll(self, roll: int) -> tuple[Item, ...]:
        """Return ordinary item rows for any physical d20 value, including 20."""
        return tuple(self._items_by_roll.get(roll, ()))

    def artifacts(self, polarity: str) -> tuple[Artifact, ...]:
        return tuple(self._artifacts_by_polarity.get(polarity.upper(), ()))

    def all_items(self) -> tuple[Item, ...]:
        return tuple(item for items in self._items_by_roll.values() for item in items)

    def all_artifacts(self) -> tuple[Artifact, ...]:
        """Return the separate jackpot pool; polarity is informational here."""
        return tuple(
            artifact
            for artifacts in self._artifacts_by_polarity.values()
            for artifact in artifacts
        )
