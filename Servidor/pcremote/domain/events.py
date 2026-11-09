"""Domain events published through the EventPublisher port."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ServerStarted:
    ip: str
    port: int


@dataclass(frozen=True)
class ServerStopped:
    pass


@dataclass(frozen=True)
class ClientAuthenticated:
    session_id: str
    device_name: str


@dataclass(frozen=True)
class ClientDisconnected:
    session_id: str
    was_authenticated: bool


@dataclass(frozen=True)
class ActiveWindowChanged:
    """The foreground window changed. Used to hint the app to show the keyboard."""

    title: str
    accepts_text: bool
    timestamp: float


@dataclass(frozen=True)
class DevicePaired:
    device_id: str
    name: str


@dataclass(frozen=True)
class DeviceRevoked:
    device_id: str
