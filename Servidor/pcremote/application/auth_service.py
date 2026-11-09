"""PIN pairing, token authentication and per-IP rate limiting.

A phone pairs once with the PIN and receives a long-lived token. Afterwards it
reconnects with the token only. The server stores a SHA-256 hash of each token.
"""

from __future__ import annotations

import hashlib
import hmac
import secrets
import threading
import time
import uuid
from collections.abc import Callable
from dataclasses import dataclass

from pcremote.domain.devices import PairedDevice
from pcremote.domain.errors import InvalidPinError, InvalidTokenError, RateLimitedError
from pcremote.domain.events import ClientAuthenticated, DevicePaired
from pcremote.domain.ports import DeviceRepository, EventPublisher, PinStore
from pcremote.domain.session import ClientSession

DEFAULT_DEVICE_NAME = "Dispositivo Desconocido"
MAX_DEVICE_NAME_LENGTH = 64


@dataclass(frozen=True)
class PairingResult:
    device_id: str
    token: str


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


class AuthService:
    def __init__(
        self,
        pin_store: PinStore,
        devices: DeviceRepository,
        publisher: EventPublisher,
        clock: Callable[[], float] = time.monotonic,
        wall_clock: Callable[[], float] = time.time,
        max_attempts: int = 5,
        lock_seconds: float = 60.0,
    ) -> None:
        self._store = pin_store
        self._devices = devices
        self._publisher = publisher
        self._clock = clock
        self._wall_clock = wall_clock
        self._max_attempts = max_attempts
        self._lock_seconds = lock_seconds
        self._pin: str | None = None
        self._failures: dict[str, int] = {}
        self._locked_until: dict[str, float] = {}
        self._guard = threading.Lock()

    @property
    def pin(self) -> str | None:
        return self._pin

    def ensure_pin(self) -> str:
        """Return the current PIN, loading the stored one or generating a new one."""
        if self._pin is None:
            stored = self._store.load()
            if stored and stored.isdigit():
                self._pin = stored
            else:
                self._pin = f"{secrets.randbelow(900_000) + 100_000}"
                self._store.save(self._pin)
        return self._pin

    def release_pin(self) -> None:
        """Forget the PIN (called when the application exits completely)."""
        self._pin = None
        self._store.clear()

    def is_locked(self, ip: str) -> bool:
        with self._guard:
            until = self._locked_until.get(ip)
            if until is None:
                return False
            if self._clock() >= until:
                del self._locked_until[ip]
                self._failures.pop(ip, None)
                return False
            return True

    def authenticate(self, session: ClientSession, pin: str, device_name: str | None) -> PairingResult:
        """Pair a new device with the PIN. Returns the token, shown only once."""
        if self.is_locked(session.ip):
            raise RateLimitedError()
        expected = self.ensure_pin()
        if not hmac.compare_digest(str(pin).encode(), expected.encode()):
            self._register_failure(session.ip)
            raise InvalidPinError()
        self._clear_failures(session.ip)
        name = self._clean_name(device_name)
        token = secrets.token_urlsafe(32)
        now = self._wall_clock()
        device = PairedDevice(uuid.uuid4().hex, name, hash_token(token), now, now)
        self._devices.add(device)
        self._mark_authenticated(session, device)
        self._publisher.publish(DevicePaired(device.device_id, name))
        return PairingResult(device.device_id, token)

    def authenticate_token(self, session: ClientSession, token: str) -> PairedDevice:
        """Authenticate a previously paired device by its token."""
        if self.is_locked(session.ip):
            raise RateLimitedError()
        digest = hash_token(str(token))
        device = self._devices.find_by_token_hash(digest)
        if device is None or not hmac.compare_digest(device.token_hash, digest):
            self._register_failure(session.ip)
            raise InvalidTokenError()
        self._clear_failures(session.ip)
        self._devices.touch(device.device_id, self._wall_clock())
        self._mark_authenticated(session, device)
        return device

    def _mark_authenticated(self, session: ClientSession, device: PairedDevice) -> None:
        session.authenticated = True
        session.device_name = device.name
        session.device_id = device.device_id
        self._publisher.publish(ClientAuthenticated(session.session_id, device.name))

    @staticmethod
    def _clean_name(device_name: str | None) -> str:
        return (device_name or DEFAULT_DEVICE_NAME).strip()[:MAX_DEVICE_NAME_LENGTH] or DEFAULT_DEVICE_NAME

    def _clear_failures(self, ip: str) -> None:
        with self._guard:
            self._failures.pop(ip, None)
            self._locked_until.pop(ip, None)

    def _register_failure(self, ip: str) -> None:
        with self._guard:
            count = self._failures.get(ip, 0) + 1
            self._failures[ip] = count
            if count >= self._max_attempts:
                self._locked_until[ip] = self._clock() + self._lock_seconds
                raise RateLimitedError()
