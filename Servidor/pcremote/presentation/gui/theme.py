"""Single source of truth for GUI colors and fonts."""

from __future__ import annotations

from dataclasses import dataclass

import customtkinter as ctk

FONT_FAMILY = "Segoe UI"
MONO_FAMILY = "Consolas"


@dataclass(frozen=True)
class Theme:
    primary: str = "#4361ee"
    secondary: str = "#3a0ca3"
    success: str = "#4cc9f0"
    danger: str = "#f72585"
    danger_hover: str = "#c0392b"
    warning: str = "#f8961e"
    dark_bg: str = "#111319"
    card_bg: str = "#1a1d29"
    sidebar_bg: str = "#0b0d12"
    border: str = "#2d3748"
    nav_hover: str = "#2d3748"
    input_bg: str = "#1a1d29"
    input_border: str = "#3a3f5d"
    switch_progress: str = "#2d3748"
    text_primary: str = "#ffffff"
    text_secondary: str = "#94a3b8"


def apply_appearance() -> None:
    """Configure global CustomTkinter appearance."""
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")


def font(size: int, bold: bool = False, mono: bool = False) -> ctk.CTkFont:
    """Build a font using the application font families."""
    return ctk.CTkFont(
        family=MONO_FAMILY if mono else FONT_FAMILY,
        size=size,
        weight="bold" if bold else "normal",
    )


def card(parent: ctk.CTkBaseClass, theme: Theme, radius: int = 16) -> ctk.CTkFrame:
    """Rounded bordered card used across views."""
    return ctk.CTkFrame(
        parent,
        fg_color=theme.card_bg,
        corner_radius=radius,
        border_width=1,
        border_color=theme.border,
    )
