"""In-process synchronous event bus (Observer pattern)."""

from __future__ import annotations

import logging
import threading
from collections import defaultdict
from collections.abc import Callable
from typing import Any

logger = logging.getLogger(__name__)


class EventBus:
    """Delivers events to subscribers registered for the event's exact type.

    Handlers run on the publisher thread. A failing handler never prevents
    the remaining handlers from running.
    """

    def __init__(self) -> None:
        self._handlers: dict[type, list[Callable[[Any], None]]] = defaultdict(list)
        self._lock = threading.Lock()

    def subscribe(self, event_type: type, handler: Callable[[Any], None]) -> None:
        with self._lock:
            self._handlers[event_type].append(handler)

    def publish(self, event: object) -> None:
        with self._lock:
            handlers = list(self._handlers.get(type(event), ()))
        for handler in handlers:
            try:
                handler(event)
            except Exception:  # noqa: BLE001 - subscriber isolation boundary
                logger.exception("Event handler failed for %s", type(event).__name__)
