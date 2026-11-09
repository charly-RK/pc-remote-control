"""Network inspection helpers."""

from __future__ import annotations

import socket


class SocketNetworkInspector:
    def local_ip(self) -> str:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
                # No packet is sent; connecting a UDP socket selects the outbound interface.
                sock.connect(("8.8.8.8", 80))
                return sock.getsockname()[0]
        except OSError:
            return "127.0.0.1"

    def hostname(self) -> str:
        return socket.gethostname()

    def is_port_free(self, port: int) -> bool:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            try:
                sock.bind(("0.0.0.0", port))
            except OSError:
                return False
            return True
