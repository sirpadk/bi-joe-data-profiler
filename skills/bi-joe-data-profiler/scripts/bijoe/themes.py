"""Colour themes for the HTML tables in the wiki.

GitHub strips <style> blocks, so every colour is written inline and a wiki has exactly one theme,
chosen when it is rendered. Change it later with `bijoe render <dir> --theme <name>`.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

DEFAULT_THEME = "light-gray"

#: Each theme: page cell colours, label colours, header colours, and for the three row groups
#: (Data Profiling Results, Variation, Distribution, Sample Data) the label block colours and the row tint.
THEMES: Dict[str, Dict[str, Any]] = {
    "dark": {
        "title": "Dark: Charcoal and Neon Edge",
        "dark": True,
        "cell": "#161616", "fg": "#eaeaea", "line": "#2c2c2c",
        "label": "#1d1d1d", "label_fg": "#dcdcdc", "head": "#242424", "head_fg": "#ffffff",
        "groups": [  # (label background, label text, row tint, edge colour)
            ("#0f2f2c", "#2de2c9", "#161616", "#2de2c9"),
            ("#2d1530", "#ff6fd8", "#161616", "#ff6fd8"),
            ("#0b2a3d", "#4cc2ff", "#161616", "#4cc2ff"),
            ("#33290a", "#ffd23f", "#161616", "#ffd23f"),
        ],
        "bar": "#4cc2ff", "bar_warn": "#ff9f43", "bar_gap": "#8a8a8a",
        "page": "#101010", "link": "#4cc2ff",
        "mermaid": {"primaryColor": "#1d1d1d", "primaryTextColor": "#eaeaea", "primaryBorderColor": "#8a8a8a",
                    "lineColor": "#8a8a8a", "secondaryColor": "#242424", "tertiaryColor": "#101010",
                    "background": "#101010", "mainBkg": "#1d1d1d", "nodeBorder": "#8a8a8a"},
    },
    "light-gray": {
        "title": "Light: Gray with Color",
        "dark": False,
        "cell": "#ffffff", "fg": "#1f2328", "line": "#d0d4da",
        "label": "#e4e7eb", "label_fg": "#1f2328", "head": "#cfd5dd", "head_fg": "#1f2328",
        "groups": [
            ("#c5dcee", "#12405f", "#f3f8fc", None),
            ("#d9cdee", "#40286b", "#f7f3fc", None),
            ("#cfe6d3", "#1d4d2b", "#f4faf5", None),
            ("#f2dcb6", "#6b4208", "#fcf8f0", None),
        ],
        "bar": "#2f7ea3", "bar_warn": "#d9822b", "bar_gap": "#9aa0a6",
        "page": "#f4f5f7", "link": "#0b5cad",
        "mermaid": {"primaryColor": "#e4e7eb", "primaryTextColor": "#1f2328", "primaryBorderColor": "#8b929a",
                    "lineColor": "#6b7280", "secondaryColor": "#ffffff", "tertiaryColor": "#f4f5f7",
                    "background": "#f4f5f7", "mainBkg": "#e4e7eb", "nodeBorder": "#8b929a"},
    },
    "light-blue": {
        "title": "Light: Light Blue with Color",
        "dark": False,
        "cell": "#ffffff", "fg": "#14283c", "line": "#bcd3e8",
        "label": "#d4e6f8", "label_fg": "#14283c", "head": "#b9d6f2", "head_fg": "#0d2a47",
        "groups": [
            ("#a9d4f5", "#0b3a63", "#f3f9ff", None),
            ("#b8e6df", "#0b4a43", "#f1fbf9", None),
            ("#f6dcc0", "#6b3a08", "#fdf7f0", None),
            ("#d9d0f5", "#3b2a78", "#f6f3ff", None),
        ],
        "bar": "#2b6cb0", "bar_warn": "#d9822b", "bar_gap": "#8aa0b8",
        "page": "#eaf3fb", "link": "#0b5cad",
        "mermaid": {"primaryColor": "#d4e6f8", "primaryTextColor": "#14283c", "primaryBorderColor": "#5f93c9",
                    "lineColor": "#5f93c9", "secondaryColor": "#ffffff", "tertiaryColor": "#eaf3fb",
                    "background": "#eaf3fb", "mainBkg": "#d4e6f8", "nodeBorder": "#5f93c9"},
    },
}
ALIASES = {"light": "light-gray", "gray": "light-gray", "grey": "light-gray", "light-grey": "light-gray",
           "blue": "light-blue", "lightblue": "light-blue", "night": "dark"}


def resolve(name: Optional[str]) -> str:
    """Theme key for a user's word ('dark', 'light', 'light-blue', ...). Unknown names raise ValueError."""
    if not name:
        return DEFAULT_THEME
    key = name.strip().lower().replace("_", "-").replace(" ", "-")
    key = ALIASES.get(key, key)
    if key not in THEMES:
        raise ValueError(f"Unknown theme '{name}'. Choose one of: {', '.join(THEMES)} (or 'light' for light-gray).")
    return key


def names() -> List[str]:
    return list(THEMES)
