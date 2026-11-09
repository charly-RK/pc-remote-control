"""Contract tests for the Socket.IO gateway (see docs/PROTOCOL.md).

They run a real server on a free local port and talk to it with a real
Socket.IO client, so the wire format is what is actually verified.
"""

from __future__ import annotations

import json
import queue
import socket
import time

import pytest
import requests
import socketio

from pcremote.application.auth_service import AuthService
from pcremote.application.command_dispatcher import CommandDispatcher
from pcremote.application.event_bus import EventBus
from pcremote.application.session_registry import SessionRegistry
from pcremote.domain.commands import CommandResult
from pcremote.domain.events import ActiveWindowChanged, DeviceRevoked
from pcremote.presentation.transport.socketio_gateway import SocketIOServer
from tests.unit.fakes import FakeDeviceRepository, FakePinStore

WAIT = 3.0


def _free_port() -> int:
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        return probe.getsockname()[1]


class Probe:
    """A Socket.IO client that records every event it receives."""

    def __init__(self, port: int) -> None:
        self.port = port
        self.client = socketio.Client()
        self._inbox: queue.Queue = queue.Queue()
        self.client.on("*", lambda event, *args: self._inbox.put((event, args[0] if args else None)))

    def connect(self) -> "Probe":
        self.client.connect(f"http://127.0.0.1:{self.port}", transports=["websocket"], wait_timeout=WAIT)
        return self

    def emit(self, event: str, payload) -> None:
        self.client.emit(event, payload)

    def wait(self, name: str):
        deadline = time.monotonic() + WAIT
        while time.monotonic() < deadline:
            try:
                event, data = self._inbox.get(timeout=0.1)
            except queue.Empty:
                continue
            if event == name:
                return data
        raise AssertionError(f"event '{name}' was not received")

    def received(self, name: str, settle: float = 0.5) -> list:
        time.sleep(settle)
        items = []
        while not self._inbox.empty():
            event, data = self._inbox.get_nowait()
            if event == name:
                items.append(data)
        return items

    def close(self) -> None:
        if self.client.connected:
            self.client.disconnect()


class Harness:
    def __init__(self) -> None:
        self.events = EventBus()
        self.registry = SessionRegistry()
        self.devices = FakeDeviceRepository()
        self.auth = AuthService(FakePinStore("123456"), self.devices, self.events)
        self.pin = self.auth.ensure_pin()
        self.dispatcher = CommandDispatcher()
        self.calls: list[dict] = []
        self.dispatcher.register(("mouse_move",), self._handle_move)
        self.dispatcher.register(("boom",), self._handle_boom)
        self.dispatcher.register(("with_data",), lambda payload: CommandResult.success("ok", data={"volume": 0.5}))
        self.server = SocketIOServer(
            self.registry, self.auth, self.dispatcher, self.events, secret_key="test-secret"
        )
        self.port = _free_port()
        self.probes: list[Probe] = []
        self.server.start(self.port)

    def _handle_move(self, payload):
        self.calls.append(dict(payload))
        return CommandResult.success("moved")

    @staticmethod
    def _handle_boom(payload):
        raise RuntimeError("secret detail")

    def probe(self) -> Probe:
        probe = Probe(self.port).connect()
        self.probes.append(probe)
        return probe

    def authed_probe(self) -> Probe:
        probe = self.probe()
        probe.emit("authenticate", {"pin": self.pin, "device_name": "Test"})
        assert probe.wait("authentication_result")["success"] is True
        probe.wait("system_info")
        return probe

    def close(self) -> None:
        for probe in self.probes:
            probe.close()
        self.server.stop()


@pytest.fixture
def harness():
    h = Harness()
    yield h
    h.close()


def test_command_before_authentication_is_rejected(harness):
    probe = harness.probe()
    probe.emit("command", {"action": "mouse_move", "x": 1, "y": 1})
    response = probe.wait("command_response")
    assert response["ok"] is False
    assert response["code"] == "NOT_AUTHENTICATED"
    assert response["original_action"] == "mouse_move"
    assert harness.calls == []


def test_wrong_pin_is_rejected(harness):
    probe = harness.probe()
    probe.emit("authenticate", {"pin": "000000"})
    assert probe.wait("authentication_result") == {"success": False, "message": "Invalid PIN", "code": "INVALID_PIN"}


def test_missing_pin_is_rejected(harness):
    probe = harness.probe()
    probe.emit("authenticate", {"device_name": "x"})
    assert probe.wait("authentication_result") == {
        "success": False,
        "message": "No pin provided",
        "code": "INVALID_PAYLOAD",
    }


def test_successful_authentication_sends_system_info(harness):
    probe = harness.probe()
    probe.emit("authenticate", {"pin": harness.pin, "device_name": "Pixel"})
    result = probe.wait("authentication_result")
    assert result["success"] is True
    assert result["message"] == "Authenticated successfully"
    assert result["token"] and result["device_id"]
    info = probe.wait("system_info")
    assert info["protocol_version"] == 1
    assert {"platform", "platform_version", "machine"} <= info.keys()
    assert harness.registry.authenticated_count() == 1


def test_authentication_accepts_json_string_payload(harness):
    probe = harness.probe()
    probe.emit("authenticate", json.dumps({"pin": harness.pin}))
    assert probe.wait("authentication_result")["success"] is True


def test_locked_out_ip_is_refused_after_five_bad_pins(harness):
    probe = harness.probe()
    for _ in range(5):
        probe.emit("authenticate", {"pin": "000000"})
        result = probe.wait("authentication_result")
        assert result["success"] is False
    assert result["message"] == "Too many attempts"
    assert harness.auth.is_locked("127.0.0.1")
    with pytest.raises(socketio.exceptions.ConnectionError):
        Probe(harness.port).connect()


def test_command_round_trip(harness):
    probe = harness.authed_probe()
    probe.emit("command", {"action": "mouse_move", "x": 3, "y": 4})
    assert probe.wait("command_response") == {"ok": True, "message": "moved"}
    assert harness.calls == [{"action": "mouse_move", "x": 3, "y": 4}]


def test_unknown_command_returns_code(harness):
    probe = harness.authed_probe()
    probe.emit("command", {"action": "does_not_exist"})
    response = probe.wait("command_response")
    assert response["ok"] is False
    assert response["code"] == "UNKNOWN_COMMAND"


def test_non_object_command_payload_is_invalid(harness):
    probe = harness.authed_probe()
    probe.emit("command", "not an object")
    response = probe.wait("command_response")
    assert response["code"] == "INVALID_PAYLOAD"


def test_unexpected_handler_error_is_generic(harness):
    probe = harness.authed_probe()
    probe.emit("command", {"action": "boom"})
    response = probe.wait("command_response")
    assert response["ok"] is False
    assert response["code"] == "EXECUTION_FAILED"
    assert "secret detail" not in str(response)


def test_keyboard_event_only_reaches_authenticated_clients(harness):
    authed = harness.authed_probe()
    anonymous = harness.probe()
    harness.events.publish(ActiveWindowChanged(title="Notepad", accepts_text=True, timestamp=1.5))
    assert authed.wait("keyboard_event") == {
        "event": "show",
        "data": {"window": "Notepad", "timestamp": 1.5},
    }
    assert anonymous.received("keyboard_event") == []


def test_disconnect_removes_session(harness):
    probe = harness.authed_probe()
    assert harness.registry.count() == 1
    probe.close()
    deadline = time.monotonic() + WAIT
    while harness.registry.count() and time.monotonic() < deadline:
        time.sleep(0.05)
    assert harness.registry.count() == 0


def test_http_endpoints_do_not_expose_pin(harness):
    base = f"http://127.0.0.1:{harness.port}"
    for path in ("/status", "/"):
        body = requests.get(base + path, timeout=WAIT).json()
        assert "pin" not in json.dumps(body).lower()
        assert body["server_running"] is True
    assert requests.get(base + "/health", timeout=WAIT).json() == {"status": "ok"}
    assert requests.get(base + "/qr", timeout=WAIT).status_code == 404


def test_stop_releases_the_port():
    h = Harness()
    h.close()
    with pytest.raises(OSError):
        socket.create_connection(("127.0.0.1", h.port), timeout=1)


def _pair(harness):
    probe = harness.probe()
    probe.emit("authenticate", {"pin": harness.pin, "device_name": "Pixel"})
    result = probe.wait("authentication_result")
    probe.wait("system_info")
    return probe, result


def test_pairing_returns_token_and_device_id(harness):
    _, result = _pair(harness)
    assert result["success"] is True
    assert isinstance(result["token"], str) and len(result["token"]) >= 32
    assert result["device_id"] in {d.device_id for d in harness.devices.list()}
    assert harness.devices.list()[0].token_hash != result["token"]


def test_reconnect_with_token_needs_no_pin(harness):
    first, paired = _pair(harness)
    first.close()
    second = harness.probe()
    second.emit("authenticate", {"token": paired["token"]})
    result = second.wait("authentication_result")
    assert result == {
        "success": True,
        "message": "Authenticated successfully",
        "device_id": paired["device_id"],
    }
    second.wait("system_info")
    second.emit("command", {"action": "mouse_move", "x": 1, "y": 2})
    assert second.wait("command_response")["ok"] is True


def test_wrong_token_is_rejected(harness):
    probe = harness.probe()
    probe.emit("authenticate", {"token": "not-a-real-token"})
    assert probe.wait("authentication_result") == {
        "success": False,
        "message": "Invalid token",
        "code": "INVALID_TOKEN",
    }


def test_revoked_device_is_disconnected_and_cannot_reconnect(harness):
    probe, paired = _pair(harness)
    harness.devices.remove(paired["device_id"])
    harness.events.publish(DeviceRevoked(paired["device_id"]))
    deadline = time.monotonic() + WAIT
    while probe.client.connected and time.monotonic() < deadline:
        time.sleep(0.05)
    assert not probe.client.connected
    assert harness.registry.authenticated_count() == 0

    again = harness.probe()
    again.emit("authenticate", {"token": paired["token"]})
    assert again.wait("authentication_result")["code"] == "INVALID_TOKEN"


def test_token_failures_count_towards_lockout(harness):
    probe = harness.probe()
    for _ in range(5):
        probe.emit("authenticate", {"token": "bad-token"})
        result = probe.wait("authentication_result")
    assert result["code"] == "RATE_LIMITED"
    assert harness.auth.is_locked("127.0.0.1")


def test_noack_command_executes_without_response(harness):
    probe = harness.authed_probe()
    probe.emit("command", {"action": "mouse_move", "x": 1, "y": 2, "noack": True})
    probe.emit("command", {"action": "mouse_move", "x": 3, "y": 4})
    responses = probe.received("command_response")
    assert responses == [{"ok": True, "message": "moved"}]
    assert [c["x"] for c in harness.calls] == [1, 3]


def test_noack_errors_are_silent_too(harness):
    probe = harness.authed_probe()
    probe.emit("command", {"action": "does_not_exist", "noack": True})
    probe.emit("command", {"action": "mouse_move", "x": 3, "y": 4})
    assert probe.received("command_response") == [{"ok": True, "message": "moved"}]


def test_legacy_command_without_noack_still_replies(harness):
    probe = harness.authed_probe()
    probe.emit("command", {"action": "mouse_move", "x": 3, "y": 4, "noack": False})
    assert probe.wait("command_response")["ok"] is True


def test_response_carries_data_only_when_present(harness):
    probe = harness.authed_probe()
    probe.emit("command", {"action": "with_data"})
    assert probe.wait("command_response") == {"ok": True, "message": "ok", "data": {"volume": 0.5}}
    probe.emit("command", {"action": "mouse_move", "x": 1, "y": 1})
    assert "data" not in probe.wait("command_response")


def test_accepted_sockets_disable_nagle(harness):
    import socket

    from pcremote.presentation.transport.socketio_gateway import _NoDelayRequestHandler

    class _Conn:
        def __init__(self) -> None:
            self.options: list[tuple] = []

        def setsockopt(self, *args) -> None:
            self.options.append(args)

    handler = _NoDelayRequestHandler.__new__(_NoDelayRequestHandler)
    conn = _Conn()
    handler.connection = conn
    # StreamRequestHandler.setup also wires rfile/wfile; only the option matters here.
    import socketserver

    original = socketserver.StreamRequestHandler.setup
    socketserver.StreamRequestHandler.setup = lambda self: None
    try:
        handler.setup()
    finally:
        socketserver.StreamRequestHandler.setup = original
    assert (socket.IPPROTO_TCP, socket.TCP_NODELAY, 1) in conn.options
