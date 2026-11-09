"""Paired device management (list and revoke)."""

from __future__ import annotations

import logging

from pcremote.domain.devices import PairedDevice
from pcremote.domain.events import DeviceRevoked
from pcremote.domain.ports import DeviceRepository, EventPublisher

logger = logging.getLogger(__name__)


class DeviceService:
    def __init__(self, devices: DeviceRepository, publisher: EventPublisher) -> None:
        self._devices = devices
        self._publisher = publisher

    def list_devices(self) -> list[PairedDevice]:
        return sorted(self._devices.list(), key=lambda d: d.last_seen, reverse=True)

    def revoke(self, device_id: str) -> bool:
        removed = self._devices.remove(device_id)
        if removed:
            logger.info("Device revoked: %s", device_id)
            self._publisher.publish(DeviceRevoked(device_id))
        return removed
