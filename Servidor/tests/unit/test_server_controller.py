import json

import pytest

from pcremote.application.auth_service import AuthService
from pcremote.application.server_controller import DEFAULT_PORT, ServerController
from pcremote.application.settings_service import SettingsService
from pcremote.domain.errors import ExecutionError
from pcremote.domain.events import ServerStarted, ServerStopped

from .fakes import (
    FakeDeviceRepository,
    FakeDiscovery,
    FakeMonitor,
    FakeNetwork,
    FakePinStore,
    FakeSettingsStore,
    FakeTransport,
    RecordingPublisher,
)


def build(busy=None):
    bus, transport, monitor = RecordingPublisher(), FakeTransport(), FakeMonitor()
    auth = AuthService(FakePinStore("111222"), FakeDeviceRepository(), bus)
    discovery = FakeDiscovery()
    settings = SettingsService(FakeSettingsStore())
    controller = ServerController(FakeNetwork(busy), transport, monitor, auth, bus, discovery, settings)
    controller.discovery, controller.settings = discovery, settings  # exposed for assertions
    return controller, transport, monitor, bus


def test_start_uses_default_port_and_publishes():
    controller, transport, monitor, bus = build()
    info = controller.start()
    assert (info.port, info.pin, info.ip) == (DEFAULT_PORT, "111222", "192.168.1.50")
    assert transport.port == DEFAULT_PORT and monitor.running and controller.running
    assert bus.events == [ServerStarted("192.168.1.50", DEFAULT_PORT)]


def test_falls_back_when_port_busy():
    controller, *_ = build(busy={DEFAULT_PORT})
    assert controller.start().port == 5000


def test_fails_when_no_port_free():
    controller, *_ = build(busy={DEFAULT_PORT, *range(5000, 5101)})
    with pytest.raises(ExecutionError):
        controller.start()


def test_stop_really_stops_everything():
    controller, transport, monitor, bus = build()
    controller.start()
    controller.stop()
    assert transport.stopped and not monitor.running and not controller.running
    assert isinstance(bus.events[-1], ServerStopped)


def test_qr_payload_format():
    controller, *_ = build()
    payload = json.loads(controller.qr_payload(controller.start()))
    assert payload["id"] == controller.settings.settings.server_id and payload["name"] == "TEST-PC"
    assert {k: payload[k] for k in ("ip", "port", "code", "v")} == {
        "ip": "192.168.1.50",
        "port": DEFAULT_PORT,
        "code": "111222",
        "v": 1,
    }


def test_discovery_started_and_stopped_with_server():
    controller, *_ = build()
    info = controller.start()
    assert controller.discovery.started == (info.server_id, "TEST-PC", info.ip, info.port, 1)
    controller.stop()
    assert controller.discovery.stopped


def test_discovery_failure_does_not_block_server():
    controller, *_ = build()

    def boom(*args):
        raise RuntimeError("no multicast")

    controller.discovery.start = boom
    assert controller.start().port == DEFAULT_PORT
