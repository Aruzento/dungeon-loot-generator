from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class AppState:
    lucky_chance: int = 1


def default_state_path() -> Path:
    if sys.platform == "win32":
        base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
        return base / "DungeonLoot" / "state.json"
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / "DungeonLoot" / "state.json"
    base = Path(os.environ.get("XDG_STATE_HOME", Path.home() / ".local" / "state"))
    return base / "dungeon-loot" / "state.json"


class StateManager:
    def __init__(self, path: Path | None = None) -> None:
        self.path = path or default_state_path()

    def load(self) -> AppState:
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
            chance = payload.get("lucky_chance")
            if isinstance(chance, bool) or not isinstance(chance, int) or not 1 <= chance <= 100:
                raise ValueError("lucky_chance must be an integer from 1 to 100")
            return AppState(lucky_chance=chance)
        except (FileNotFoundError, OSError, ValueError, TypeError, json.JSONDecodeError):
            state = AppState()
            self.save(state)
            return state

    def save(self, state: AppState) -> None:
        chance = max(1, min(100, int(state.lucky_chance)))
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(".tmp")
        temporary.write_text(
            json.dumps({"lucky_chance": chance}, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        os.replace(temporary, self.path)
