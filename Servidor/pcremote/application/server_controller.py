"""Server lifecycle use case: pick a port, start/stop transport and monitor."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass

from pcremote.application.auth_service import AuthService
from pcremote.application.settings_service import SettingsService
from pcremote.domain.errors import ExecutionError
from pcremote.domain.events import ServerStarted, ServerStopped
from pcremote.domain.ports import (
    ActivityMonitor,
    DiscoveryService,
    EventPublisher,
    NetworkInspector,
    TransportServer,
)

logger = logging.getLogger(__name__)

DEFAULT_PORT = 5723
FALLBACK_PORTS = range(5000, 5101)
PROTOCOL_VERSION = 1


@dataclass(frozen=True)
class ServerInfo:
    ip: str
    port: int
    pin: str
    server_id: str
    server_name: str


class ServerController:
    def __init__(
        self,
        network: NetworkInspector,
        transport: TransportServer,
        monitor: ActivityMonitor,
        auth: AuthService,
        publisher: EventPublisher,
        discovery: DiscoveryService,
        settings: SettingsService,
    ) -> None:
        self._network = network
        self._transport = transport
        self._monitor = monitor
        self._auth = auth
        self._publisher = publisher
        self._discovery = discovery
        self._settings = settings
        self._info: ServerInfo | None = None

    @property
    def running(self) -> bool:
        return self._info is not None

    @property
    def info(self) -> ServerInfo | None:
        return self._info

    def pick_port(self, preferred: int = DEFAULT_PORT) -> int:
        for port in (preferred, *FALLBACK_PORTS):
            if self._network.is_port_free(port):
                return port
        raise ExecutionError("No free port available")

    def start(self, preferred_port: int = DEFAULT_PORT) -> ServerInfo:
        if self._info is not None:
            return self._info
        pin = self._auth.ensure_pin()
        port = self.pick_port(preferred_port)
        self._transport.start(port)
        self._monitor.start()
        self._info = ServerInfo(
            ip=self._network.local_ip(),
            port=port,
            pin=pin,
            server_id=self._settings.settings.server_id,
            server_name=self._network.hostname(),
        )
        self._start_discovery(self._info)
        logger.info("Server started on %s:%d", self._info.ip, port)
        self._publisher.publish(ServerStarted(self._info.ip, port))
        return self._info

    def stop(self) -> None:
        if self._info is None:
            return
        self._monitor.stop()
        self._stop_discovery()
        self._transport.stop()
        self._info = None
        logger.info("Server stopped")
        self._publisher.publish(ServerStopped())

    def _start_discovery(self, info: ServerInfo) -> None:
        # Discovery is a convenience: a failure must never prevent the server from running.
        try:
            self._discovery.start(info.server_id, info.server_name, info.ip, info.port, PROTOCOL_VERSION)
        except Exception:  # noqa: BLE001 - optional feature boundary
            logger.warning("Discovery could not be started", exc_info=True)

    def _stop_discovery(self) -> None:
        try:
            self._discovery.stop()
        except Exception:  # noqa: BLE001 - optional feature boundary
            logger.warning("Discovery could not be stopped cleanly", exc_info=True)

    @staticmethod
    def qr_payload(info: ServerInfo) -> str:
        return json.dumps(
            {
                "ip": info.ip,
                "port": info.port,
                "code": info.pin,
                "id": info.server_id,
                "name": info.server_name,
                "v": PROTOCOL_VERSION,
            }
        )
