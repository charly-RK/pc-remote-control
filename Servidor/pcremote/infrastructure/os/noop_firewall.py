"""Firewall adapter for systems where no rule is managed by the application."""

from __future__ import annotations


class NoopFirewall:
    def is_configured(self) -> bool:
        return True

    def configure(self) -> bool:
        return True

    def remove(self) -> bool:
        return True
