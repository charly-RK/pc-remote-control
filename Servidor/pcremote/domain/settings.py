"""Persisted application settings."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AppSettings:
    server_id: str = ""
    minimize_to_tray: bool = True
    auto_start_server: bool = True
