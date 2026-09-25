from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from app.loot_engine import LootEngine, format_price
from app.models import InvalidRollError, LootResult
from app.repository import LootRepository
from app.state_manager import StateManager


COLORS = {
    "window": "#15120f",
    "surface": "#211c17",
    "surface_raised": "#2b241d",
    "border": "#514232",
    "text": "#f2eadc",
    "muted": "#b9aa95",
    "accent": "#c99545",
    "accent_active": "#dda95a",
    "lucky": "#efd27b",
    "error": "#ef8d7d",
}


class DungeonLootApp:
    def __init__(self, root: tk.Tk, engine: LootEngine) -> None:
        self.root = root
        self.engine = engine
        self.root.title("Dungeon Loot")
        self.root.geometry("620x520")
        self.root.minsize(520, 450)
        self.root.configure(bg=COLORS["window"])

        self.roll_var = tk.StringVar()
        self.status_var = tk.StringVar(value="Введите результат физического броска d20")
        self.badge_var = tk.StringVar(value="НАХОДКА")
        self.name_var = tk.StringVar(value="Здесь появится предмет")
        self.description_var = tk.StringVar(
            value="Введите число от 1 до 20 и нажмите «Получить предмет»."
        )
        self.price_var = tk.StringVar(value="Стоимость: —")

        self._configure_styles()
        self._build_layout()
        self.root.bind("<Return>", self._on_submit)
        self.root.after_idle(self.roll_entry.focus_set)

    def _configure_styles(self) -> None:
        style = ttk.Style(self.root)
        style.theme_use("clam")
        style.configure(
            "Primary.TButton",
            font=("Segoe UI Semibold", 12),
            foreground="#18130e",
            background=COLORS["accent"],
            bordercolor=COLORS["accent"],
            padding=(18, 12),
            relief="flat",
        )
        style.map(
            "Primary.TButton",
            background=[("pressed", COLORS["accent_active"]), ("active", COLORS["accent_active"])],
            bordercolor=[("focus", COLORS["lucky"])],
        )
        style.configure(
            "Roll.TEntry",
            fieldbackground="#17130f",
            foreground=COLORS["text"],
            insertcolor=COLORS["text"],
            bordercolor=COLORS["border"],
            lightcolor=COLORS["accent"],
            darkcolor=COLORS["border"],
            padding=(14, 10),
            font=("Segoe UI", 14),
        )

    def _build_layout(self) -> None:
        shell = tk.Frame(self.root, bg=COLORS["window"], padx=34, pady=28)
        shell.pack(fill="both", expand=True)

        tk.Label(
            shell,
            text="DUNGEON LOOT",
            bg=COLORS["window"],
            fg=COLORS["accent"],
            font=("Georgia", 22, "bold"),
        ).pack(anchor="center")
        tk.Label(
            shell,
            text="Введите результат броска d20",
            bg=COLORS["window"],
            fg=COLORS["muted"],
            font=("Segoe UI", 10),
            pady=8,
        ).pack(anchor="center")

        controls = tk.Frame(shell, bg=COLORS["window"])
        controls.pack(fill="x", pady=(10, 24))
        controls.columnconfigure(0, weight=1)

        self.roll_entry = ttk.Entry(
            controls,
            textvariable=self.roll_var,
            justify="center",
            style="Roll.TEntry",
        )
        self.roll_entry.grid(row=0, column=0, sticky="ew", ipady=3)
        self.submit_button = ttk.Button(
            controls,
            text="ПОЛУЧИТЬ ПРЕДМЕТ",
            command=self._on_submit,
            style="Primary.TButton",
            cursor="hand2",
        )
        self.submit_button.grid(row=1, column=0, sticky="ew", pady=(12, 0))

        self.status_label = tk.Label(
            shell,
            textvariable=self.status_var,
            bg=COLORS["window"],
            fg=COLORS["muted"],
            font=("Segoe UI", 10),
            anchor="center",
        )
        self.status_label.pack(fill="x", pady=(0, 12))

        self.card = tk.Frame(
            shell,
            bg=COLORS["surface"],
            highlightthickness=1,
            highlightbackground=COLORS["border"],
            padx=28,
            pady=24,
        )
        self.card.pack(fill="both", expand=True)

        self.badge_label = tk.Label(
            self.card,
            textvariable=self.badge_var,
            bg=COLORS["surface"],
            fg=COLORS["muted"],
            font=("Segoe UI Semibold", 9),
        )
        self.badge_label.pack(anchor="w")
        self.name_label = tk.Label(
            self.card,
            textvariable=self.name_var,
            bg=COLORS["surface"],
            fg=COLORS["text"],
            font=("Georgia", 18, "bold"),
            justify="left",
            anchor="w",
        )
        self.name_label.pack(fill="x", pady=(9, 12))
        self.description_label = tk.Label(
            self.card,
            textvariable=self.description_var,
            bg=COLORS["surface"],
            fg=COLORS["muted"],
            font=("Segoe UI", 11),
            justify="left",
            anchor="nw",
        )
        self.description_label.pack(fill="both", expand=True)
        self.price_label = tk.Label(
            self.card,
            textvariable=self.price_var,
            bg=COLORS["surface"],
            fg=COLORS["accent"],
            font=("Segoe UI Semibold", 12),
            justify="left",
            anchor="w",
        )
        self.price_label.pack(fill="x", pady=(16, 0))

        self.card.bind("<Configure>", self._update_wraplength)

    def _update_wraplength(self, event: tk.Event) -> None:
        wrap = max(360, event.width - 58)
        self.name_label.configure(wraplength=wrap)
        self.description_label.configure(wraplength=wrap)

    def _on_submit(self, _event: tk.Event | None = None) -> str:
        try:
            result = self.engine.generate(self.roll_var.get())
        except InvalidRollError as error:
            self.status_var.set(str(error))
            self.status_label.configure(fg=COLORS["error"])
            self.roll_entry.focus_set()
            self.roll_entry.selection_range(0, tk.END)
            return "break"
        except Exception:
            self.status_var.set("Не удалось получить предмет. Проверьте файлы данных.")
            self.status_label.configure(fg=COLORS["error"])
            self.roll_entry.focus_set()
            return "break"

        self._show_result(result)
        self.roll_var.set("")
        self.roll_entry.focus_set()
        return "break"

    def _show_result(self, result: LootResult) -> None:
        self.status_var.set(f"Результат d20: {result.roll}")
        self.status_label.configure(fg=COLORS["muted"])
        self.badge_var.set("✦ НЕОБЫЧНАЯ НАХОДКА ✦" if result.is_lucky else "НАХОДКА")
        self.badge_label.configure(fg=COLORS["lucky"] if result.is_lucky else COLORS["muted"])
        self.card.configure(
            bg=COLORS["surface_raised"] if result.is_lucky else COLORS["surface"],
            highlightbackground=COLORS["lucky"] if result.is_lucky else COLORS["border"],
        )
        card_background = COLORS["surface_raised"] if result.is_lucky else COLORS["surface"]
        for label in (self.badge_label, self.name_label, self.description_label, self.price_label):
            label.configure(bg=card_background)
        self.name_var.set(result.name)
        self.description_var.set(result.description)
        self.price_var.set(f"Стоимость: {format_price(result.value_cp)}")


def run() -> None:
    repository = LootRepository()
    state_manager = StateManager()
    engine = LootEngine(repository, state_manager)
    root = tk.Tk()
    DungeonLootApp(root, engine)
    root.mainloop()
