"""mDNS/Zeroconf announcement so phones can find the PC without a fixed IP."""

from __future__ import annotations

import logging
import socket
import threading
import time
from typing import Any

from pcremote.domain.errors import ExecutionError

logger = logging.getLogger(__name__)

SERVICE_TYPE = "_pcremote._tcp.local."


class ZeroconfDiscovery:
    def __init__(self) -> None:
        self._zeroconf: Any = None
        self._info: Any = None
        self._lock = threading.Lock()

    def start(self, server_id: str, name: str, ip: str, port: int, protocol_version: int) -> None:
        with self._lock:
            if self._zeroconf is not None:
                return
            try:
                from zeroconf import ServiceInfo, Zeroconf

                short_name = name.replace(".", "-")
                info = ServiceInfo(
                    SERVICE_TYPE,
                    f"{short_name} ({server_id[:6]}).{SERVICE_TYPE}",
                    addresses=[socket.inet_aton(ip)],
                    port=port,
                    properties={"id": server_id, "name": name, "v": str(protocol_version)},
                )
                zc = Zeroconf()
                try:
                    zc.register_service(info)
                except Exception:
                    zc.close()
                    raise
            except Exception as exc:  # noqa: BLE001 - third-party failures vary widely
                raise ExecutionError(f"Could not start discovery: {exc}") from exc
            self._zeroconf, self._info = zc, info
            logger.info("Discovery announced as %s", info.name)

    def stop(self) -> None:
        with self._lock:
            zc, info = self._zeroconf, self._info
            self._zeroconf = self._info = None
        if zc is None:
            return
        try:
            zc.unregister_service(info)
        except Exception:  # noqa: BLE001 - best effort during shutdown
            logger.warning("Could not unregister the discovery service", exc_info=True)
        finally:
            zc.close()


def discover_servers(timeout: float = 2.0) -> list[dict[str, Any]]:
    """Browse the network for PC Remote Control servers (used by tests and manual checks)."""
    from zeroconf import ServiceBrowser, ServiceListener, Zeroconf

    found: dict[str, dict[str, Any]] = {}

    class _Listener(ServiceListener):
        def add_service(self, zc: Zeroconf, type_: str, name: str) -> None:
            info = zc.get_service_info(type_, name, timeout=1500)
            if info is None:
                return
            props = {
                (k.decode() if isinstance(k, bytes) else k): (v.decode() if isinstance(v, bytes) else v)
                for k, v in info.properties.items()
            }
            found[name] = {
                "name": name,
                "addresses": [socket.inet_ntoa(a) for a in info.addresses if len(a) == 4],
                "port": info.port,
                "properties": props,
            }

        def update_service(self, zc: Zeroconf, type_: str, name: str) -> None:
            self.add_service(zc, type_, name)

        def remove_service(self, zc: Zeroconf, type_: str, name: str) -> None:
            found.pop(name, None)

    zc = Zeroconf()
    try:
        browser = ServiceBrowser(zc, SERVICE_TYPE, _Listener())
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline and not found:
            time.sleep(0.05)
        browser.cancel()
    finally:
        zc.close()
    return list(found.values())
