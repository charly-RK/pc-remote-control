"""Minimal HTTP routes. They never expose the PIN or any pairing data."""

from __future__ import annotations

import platform
import time
from collections.abc import Callable
from typing import Any

from flask import Flask, jsonify

from pcremote.application.session_registry import SessionRegistry


def register_routes(
    app: Flask,
    registry: SessionRegistry,
    info_provider: Callable[[], dict[str, Any]],
) -> None:
    """Register `/`, `/status` and `/health`.

    `info_provider` returns a dict with `port` and `started_at` (epoch seconds).
    """

    def _status() -> dict[str, Any]:
        info = info_provider()
        started_at = info.get("started_at")
        uptime = max(0.0, time.time() - started_at) if started_at else 0.0
        return {
            "server_running": True,
            "uptime_seconds": round(uptime, 1),
            "connections": registry.count(),
            "authenticated_connections": registry.authenticated_count(),
            "platform": platform.system(),
        }

    @app.route("/health")
    def health():
        return jsonify({"status": "ok"})

    @app.route("/status")
    def status():
        return jsonify(_status())

    @app.route("/")
    def index():
        return jsonify(_status())
