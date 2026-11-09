"""Foreground window watcher (Windows)."""

from __future__ import annotations

import logging

from pcremote.domain.ports import EventPublisher
from pcremote.infrastructure.os._polling_watcher import DEFAULT_TEXT_APPS, PollingWatcher

logger = logging.getLogger(__name__)

__all__ = ["DEFAULT_TEXT_APPS", "WindowWatcher"]


class WindowWatcher(PollingWatcher):
    def __init__(
        self,
        publisher: EventPublisher,
        text_apps: tuple[str, ...] = DEFAULT_TEXT_APPS,
        interval: float = 0.5,
    ) -> None:
        super().__init__(publisher, self._read_foreground_title, interval, text_apps)

    def is_supported(self) -> bool:
        try:
            import win32gui  # noqa: F401
        except ImportError:
            logger.warning("win32gui is unavailable; window watcher disabled")
            return False
        return True

    @staticmethod
    def _read_foreground_title() -> str | None:
        import win32gui

        try:
            return win32gui.GetWindowText(win32gui.GetForegroundWindow())
        except win32gui.error:
            logger.debug("Could not read the foreground window", exc_info=True)
            return None
