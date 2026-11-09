"""Base class for activity monitors that poll the active window title."""

from __future__ import annotations

import logging
import threading
import time
from collections.abc import Callable

from pcremote.domain.events import ActiveWindowChanged
from pcremote.domain.ports import EventPublisher

logger = logging.getLogger(__name__)

DEFAULT_TEXT_APPS: tuple[str, ...] = (
    "Chrome", "Firefox", "Edge", "Word", "Notepad",
    "Visual Studio", "Excel", "PowerPoint", "Outlook",
    "Teams", "WhatsApp", "Discord", "Telegram", "Steam",
)


class PollingWatcher:
    """Polls `read_title` in a daemon thread and publishes ActiveWindowChanged on change.

    `read_title` returns the current title or None when it cannot be read.
    Subclasses may override `is_supported` to disable the monitor.
    """

    def __init__(
        self,
        publisher: EventPublisher,
        read_title: Callable[[], str | None],
        interval: float = 1.0,
        text_apps: tuple[str, ...] = DEFAULT_TEXT_APPS,
        name: str = "window-watcher",
    ) -> None:
        self._publisher = publisher
        self._read_title = read_title
        self._interval = interval
        self._text_apps = text_apps
        self._name = name
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None
        self._last_title: str | None = None

    def is_supported(self) -> bool:
        return True

    def start(self) -> None:
        if self._thread is not None and self._thread.is_alive():
            return
        if not self.is_supported():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, name=self._name, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        thread = self._thread
        if thread is not None and thread is not threading.current_thread():
            thread.join(timeout=2)
        self._thread = None

    def poll_once(self) -> None:
        title = self._read_title()
        if title is not None and title != self._last_title:
            self._last_title = title
            accepts_text = any(app in title for app in self._text_apps)
            self._publisher.publish(ActiveWindowChanged(title, accepts_text, time.time()))

    def _run(self) -> None:
        while not self._stop_event.is_set():
            try:
                self.poll_once()
            except Exception:  # noqa: BLE001 - the monitor thread must survive adapter failures
                logger.debug("Window title poll failed", exc_info=True)
            self._stop_event.wait(self._interval)
