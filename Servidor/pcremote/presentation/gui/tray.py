"""System tray icon (Windows, macOS and Linux)."""

from __future__ import annotations

import logging
import threading
from collections.abc import Callable
from pathlib import Path
from typing import Any

from PIL import Image

logger = logging.getLogger(__name__)

_FALLBACK_COLOR = (67, 97, 238)
_READY_TIMEOUT_SECONDS = 2.0


class TrayIcon:
    """Thin wrapper over pystray. Callbacks run on the tray thread.

    `available` is False when no tray backend works (for example Linux without
    an appindicator). The caller must then keep the window reachable.
    """

    def __init__(
        self,
        image_path: Path,
        on_show: Callable[[], None],
        on_quit: Callable[[], None],
        platform_name: str = "Windows",
        title: str = "PC Remote Control",
    ) -> None:
        self.available = False
        self._platform = platform_name
        self._thread: threading.Thread | None = None
        self._ready = threading.Event()
        self._icon: Any = None
        try:
            import pystray
        except Exception:  # noqa: BLE001 - backend import can fail with platform specific errors
            logger.warning("System tray backend is not available", exc_info=True)
            return
        self._icon = pystray.Icon(
            "PC Remote",
            self._load_image(image_path),
            title,
            pystray.Menu(
                pystray.MenuItem("Mostrar", lambda icon, item: on_show(), default=True),
                pystray.MenuItem("Salir", lambda icon, item: on_quit()),
            ),
        )

    @staticmethod
    def _load_image(path: Path) -> Image.Image:
        try:
            return Image.open(path)
        except (OSError, ValueError):
            logger.warning("Tray icon image not found, using fallback")
            return Image.new("RGB", (64, 64), color=_FALLBACK_COLOR)

    def start(self) -> bool:
        """Show the tray icon. Returns whether the tray is usable."""
        if self._icon is None or self._thread is not None or self.available:
            return self.available
        if self._platform == "Darwin":
            # pystray must run on the main thread on macOS. run_detached() hooks the icon
            # into the Tk event loop that is already running on the main thread.
            try:
                self._icon.run_detached()
                self.available = True
            except Exception:  # noqa: BLE001 - backend specific failures
                logger.warning("System tray could not be started", exc_info=True)
            return self.available

        self._thread = threading.Thread(target=self._run_threaded, daemon=True)
        self._thread.start()
        self.available = self._ready.wait(_READY_TIMEOUT_SECONDS) and self._thread.is_alive()
        if not self.available:
            logger.warning("System tray did not become ready; the window will be minimized instead")
        return self.available

    def _run_threaded(self) -> None:
        def setup(icon: Any) -> None:
            icon.visible = True
            self._ready.set()

        try:
            self._icon.run(setup=setup)
        except Exception:  # noqa: BLE001 - backend specific failures (for example missing appindicator)
            logger.warning("System tray backend failed", exc_info=True)

    def stop(self) -> None:
        if self._icon is None or not self.available:
            return
        try:
            self._icon.stop()
        except Exception:  # noqa: BLE001 - backend specific failures
            logger.debug("Tray stop failed", exc_info=True)
        self.available = False
        self._thread = None

    def notify(self, message: str, title: str = "PC Remote Control") -> None:
        if self._icon is None or not self.available:
            return
        try:
            self._icon.notify(message, title)
        except (NotImplementedError, OSError):
            logger.debug("Tray notifications not supported", exc_info=True)
