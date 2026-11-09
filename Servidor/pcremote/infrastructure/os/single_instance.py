"""Prevent two copies of the app from running at the same time."""

from __future__ import annotations

import logging
import socket
import sys
from typing import Any

logger = logging.getLogger(__name__)

_ERROR_ALREADY_EXISTS = 183


class SingleInstance:
    def __init__(self, name: str) -> None:
        self._name = name
        self._handle: Any = None
        self._socket: socket.socket | None = None

    def acquire(self) -> bool:
        if self._handle is not None or self._socket is not None:
            return True
        if sys.platform == "win32":
            return self._acquire_mutex()
        return self._acquire_socket()

    def release(self) -> None:
        handle, self._handle = self._handle, None
        if handle is not None:
            try:
                import win32api

                win32api.CloseHandle(handle)
            except Exception:  # noqa: BLE001 - best effort during shutdown
                logger.warning("Could not release the instance mutex", exc_info=True)
        sock, self._socket = self._socket, None
        if sock is not None:
            sock.close()

    def _acquire_mutex(self) -> bool:
        import win32api
        import win32event

        handle = win32event.CreateMutex(None, False, f"Local\\{self._name}")
        if win32api.GetLastError() == _ERROR_ALREADY_EXISTS:
            win32api.CloseHandle(handle)
            return False
        self._handle = handle
        return True

    def _acquire_socket(self) -> bool:
        # A localhost port derived from the name acts as the lock on non-Windows systems.
        port = 49152 + (sum(self._name.encode()) * 31) % 16000
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sock.bind(("127.0.0.1", port))
        except OSError:
            sock.close()
            return False
        self._socket = sock
        return True
