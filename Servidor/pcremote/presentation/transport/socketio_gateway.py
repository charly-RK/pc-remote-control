"""Socket.IO gateway: the only module that knows Flask-SocketIO.

It translates transport events into calls to the application layer and
translates domain errors into wire responses in a single place.
"""

from __future__ import annotations

import json
import logging
import platform
import socket
import threading
import time
from typing import Any

from flask import Flask, request
from flask_socketio import SocketIO, disconnect, emit
from werkzeug.serving import WSGIRequestHandler, make_server

from pcremote.application.auth_service import AuthService
from pcremote.application.command_dispatcher import CommandDispatcher
from pcremote.application.event_bus import EventBus
from pcremote.application.session_registry import SessionRegistry
from pcremote.domain.errors import (
    DomainError,
    InvalidPayloadError,
    InvalidPinError,
    InvalidTokenError,
    NotAuthenticatedError,
    RateLimitedError,
)
from pcremote.domain.events import ActiveWindowChanged, ClientDisconnected, DeviceRevoked
from pcremote.domain.session import ClientSession
from pcremote.presentation.http.routes import register_routes

logger = logging.getLogger(__name__)

DEFAULT_DEVICE_NAME = "Dispositivo Desconocido"


class _NoDelayRequestHandler(WSGIRequestHandler):
    """Disables Nagle's algorithm: small frames (mouse moves, acks) must not wait for ACKs."""

    def setup(self) -> None:
        super().setup()
        try:
            self.connection.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        except OSError:
            logger.debug("Could not set TCP_NODELAY", exc_info=True)


class SocketIOServer:
    """Implements the TransportServer port with Flask-SocketIO."""

    def __init__(
        self,
        registry: SessionRegistry,
        auth: AuthService,
        dispatcher: CommandDispatcher,
        events: EventBus,
        secret_key: str,
        protocol_version: int = 1,
    ) -> None:
        self._registry = registry
        self._auth = auth
        self._dispatcher = dispatcher
        self._events = events
        self._secret_key = secret_key
        self._protocol_version = protocol_version

        self._app: Flask | None = None
        self._socketio: SocketIO | None = None
        self._http_server: Any = None
        self._thread: threading.Thread | None = None
        self._sids: set[str] = set()
        self._sids_lock = threading.Lock()
        self._info: dict[str, Any] = {"port": None, "started_at": None}

        # Subscribed once; the handler is a no-op while the server is stopped.
        self._events.subscribe(ActiveWindowChanged, self._on_active_window_changed)
        self._events.subscribe(DeviceRevoked, self._on_device_revoked)

    # ------------------------------------------------------------------ lifecycle

    def build(self) -> tuple[Flask, SocketIO]:
        """Create a new Flask app and SocketIO instance with all handlers registered."""
        app = Flask(__name__)
        app.config["SECRET_KEY"] = self._secret_key
        app.config["DEBUG"] = False

        socketio = SocketIO(
            app,
            async_mode="threading",
            logger=False,
            engineio_logger=False,
            ping_timeout=60,
            ping_interval=25,
            max_http_buffer_size=1_000_000,
        )
        self._app = app
        self._socketio = socketio
        self._register_socket_handlers(socketio)
        register_routes(app, self._registry, lambda: dict(self._info))
        return app, socketio

    def start(self, port: int) -> None:
        if self._http_server is not None:
            return
        app, _ = self.build()
        # Binding happens in the constructor, so a busy port raises OSError here.
        server = make_server("0.0.0.0", port, app, threaded=True, request_handler=_NoDelayRequestHandler)
        self._info = {"port": port, "started_at": time.time()}
        self._http_server = server
        self._thread = threading.Thread(
            target=server.serve_forever, name="socketio-server", daemon=True
        )
        self._thread.start()
        logger.info("Transport server listening on port %s", port)

    def stop(self) -> None:
        server, thread = self._http_server, self._thread
        self._http_server = None
        self._thread = None
        if server is not None:
            server.shutdown()
            server.server_close()
        if thread is not None:
            thread.join(timeout=5)
        with self._sids_lock:
            sids, self._sids = self._sids, set()
        for sid in sids:
            self._registry.remove(sid)
        self._socketio = None
        self._app = None
        self._info = {"port": None, "started_at": None}
        logger.info("Transport server stopped")

    # ------------------------------------------------------------------ socket handlers

    def _register_socket_handlers(self, socketio: SocketIO) -> None:
        @socketio.on("connect")
        def on_connect(*_args):
            ip = request.remote_addr or "unknown"
            if self._auth.is_locked(ip):
                logger.warning("Rejected connection from locked IP %s", ip)
                return False
            self._registry.add(ClientSession(session_id=request.sid, ip=ip))
            with self._sids_lock:
                self._sids.add(request.sid)
            logger.info("Client connected: %s from %s", request.sid, ip)
            return None

        @socketio.on("disconnect")
        def on_disconnect(*_args):
            sid = request.sid
            session = self._registry.remove(sid)
            with self._sids_lock:
                self._sids.discard(sid)
            if session is not None:
                logger.info("Client disconnected: %s", sid)
                self._events.publish(
                    ClientDisconnected(session_id=sid, was_authenticated=session.authenticated)
                )

        @socketio.on("authenticate")
        def on_authenticate(payload=None):
            self._handle_authenticate(payload)

        @socketio.on("command")
        def on_command(payload=None):
            response = self._handle_command(payload)
            if isinstance(payload, dict) and payload.get("noack") is True:
                # Fire-and-forget input: no reply, not even on error.
                if not response.get("ok"):
                    logger.debug("noack command failed: %s", response.get("code"))
                return
            emit("command_response", response)

    def _handle_authenticate(self, payload: Any) -> None:
        session = self._registry.get(request.sid)
        if session is None:
            emit("authentication_result", _auth_failure("INVALID_PAYLOAD", "Connection not found"))
            return

        data = _parse_payload(payload)
        if not data or ("token" not in data and "pin" not in data):
            emit("authentication_result", _auth_failure("INVALID_PAYLOAD", "No pin provided"))
            return

        try:
            if "token" in data:
                result = self._authenticate_with_token(session, data["token"])
            else:
                result = self._pair_with_pin(session, data)
        except RateLimitedError as exc:
            logger.warning("Authentication rate limited for %s", session.ip)
            emit("authentication_result", _auth_failure(exc.code, exc.message))
            disconnect()
            return
        except (InvalidPinError, InvalidTokenError) as exc:
            logger.info("Failed authentication attempt from %s", session.ip)
            emit("authentication_result", _auth_failure(exc.code, exc.message))
            return

        logger.info("Client authenticated: %s (%s)", session.session_id, session.device_name)
        emit("authentication_result", result)
        emit(
            "system_info",
            {
                "platform": platform.system(),
                "platform_version": platform.version(),
                "machine": platform.machine(),
                "protocol_version": self._protocol_version,
            },
        )

    def _authenticate_with_token(self, session: ClientSession, token: Any) -> dict[str, Any]:
        if not isinstance(token, str) or not token:
            raise InvalidTokenError()
        device = self._auth.authenticate_token(session, token)
        return {"success": True, "message": "Authenticated successfully", "device_id": device.device_id}

    def _pair_with_pin(self, session: ClientSession, data: dict[str, Any]) -> dict[str, Any]:
        pin = str(data["pin"])
        device_name = str(data.get("device_name") or DEFAULT_DEVICE_NAME)
        pairing = self._auth.authenticate(session, pin, device_name)
        return {
            "success": True,
            "message": "Authenticated successfully",
            "token": pairing.token,
            "device_id": pairing.device_id,
        }

    def _handle_command(self, payload: Any) -> dict[str, Any]:
        action = payload.get("action", "unknown") if isinstance(payload, dict) else "unknown"
        try:
            session = self._registry.get(request.sid)
            if session is None:
                raise NotAuthenticatedError()
            if not isinstance(payload, dict):
                raise InvalidPayloadError("Command payload must be an object")
            result = self._dispatcher.dispatch(session, payload)
        except DomainError as exc:
            return _error_response(exc.code, exc.message, action)
        except Exception:
            # Never log the payload: it may contain typed text.
            logger.exception("Unexpected error while handling command '%s'", action)
            return _error_response("EXECUTION_FAILED", "Internal error", action)

        if result.ok:
            response: dict[str, Any] = {"ok": True, "message": result.message}
            if result.data is not None:
                response["data"] = result.data
            return response
        return _error_response(result.code or "EXECUTION_FAILED", result.message, action)

    # ------------------------------------------------------------------ events

    def _on_active_window_changed(self, event: ActiveWindowChanged) -> None:
        socketio = self._socketio
        if socketio is None:
            return
        message = {
            "event": "show" if event.accepts_text else "hide",
            "data": {"window": event.title, "timestamp": event.timestamp},
        }
        for session in self._registry.authenticated():
            socketio.emit("keyboard_event", message, to=session.session_id)

    def _on_device_revoked(self, event: DeviceRevoked) -> None:
        socketio = self._socketio
        with self._sids_lock:
            sids = list(self._sids)
        for sid in sids:
            session = self._registry.get(sid)
            if session is None or session.device_id != event.device_id:
                continue
            self._registry.remove(sid)
            if socketio is not None:
                try:
                    socketio.server.disconnect(sid)
                except KeyError:
                    logger.debug("Session %s was already gone", sid)
            logger.info("Disconnected revoked device session %s", sid)


def _auth_failure(code: str, message: str) -> dict[str, Any]:
    return {"success": False, "message": message, "code": code}


def _parse_payload(payload: Any) -> dict[str, Any] | None:
    if isinstance(payload, str):
        try:
            payload = json.loads(payload)
        except ValueError:
            return None
    return payload if isinstance(payload, dict) else None


def _error_response(code: str, message: str, action: str) -> dict[str, Any]:
    return {"ok": False, "code": code, "error": message, "original_action": action}
