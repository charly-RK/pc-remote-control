"""Fakes of the domain ports, shared by unit tests."""

from __future__ import annotations


class FakePinStore:
    def __init__(self, pin: str | None = None) -> None:
        self.pin = pin
        self.cleared = False

    def load(self) -> str | None:
        return self.pin

    def save(self, pin: str) -> None:
        self.pin = pin

    def clear(self) -> None:
        self.pin = None
        self.cleared = True


class RecordingPublisher:
    def __init__(self) -> None:
        self.events: list[object] = []

    def publish(self, event: object) -> None:
        self.events.append(event)


class FakeClock:
    def __init__(self) -> None:
        self.now = 0.0

    def __call__(self) -> float:
        return self.now


class FakeMouse:
    def __init__(self) -> None:
        self.calls: list[tuple] = []

    def move_relative(self, dx, dy):
        self.calls.append(("move", dx, dy))

    def click(self, button, click_type):
        self.calls.append(("click", button, click_type))

    def scroll(self, dx, dy):
        self.calls.append(("scroll", dx, dy))


class FakeKeyboard:
    def __init__(self) -> None:
        self.calls: list[tuple] = []

    def press_key(self, key, action):
        self.calls.append(("press", key, action))

    def hotkey(self, keys):
        self.calls.append(("hotkey", tuple(keys)))

    def type_text(self, text):
        self.calls.append(("type", text))


class FakeMedia:
    def __init__(self, state=None) -> None:
        from pcremote.domain.commands import MediaState

        self.calls: list[tuple] = []
        self.state = state if state is not None else MediaState(volume=0.5, muted=False, playing=True)
        self.fail_state = False

    def send(self, command):
        self.calls.append(("send", command))

    def set_volume(self, level):
        self.calls.append(("volume", level))

    def get_state(self):
        if self.fail_state:
            raise RuntimeError("no audio device")
        return self.state


class FakeExecutor:
    """Used for both PowerController and DesktopController."""

    def __init__(self) -> None:
        self.actions: list[object] = []

    def execute(self, action):
        self.actions.append(action)


class FakeNetwork:
    def __init__(self, busy: set[int] | None = None) -> None:
        self.busy = busy or set()

    def local_ip(self) -> str:
        return "192.168.1.50"

    def hostname(self) -> str:
        return "TEST-PC"

    def is_port_free(self, port: int) -> bool:
        return port not in self.busy


class FakeTransport:
    def __init__(self) -> None:
        self.port: int | None = None
        self.stopped = False

    def start(self, port: int) -> None:
        self.port = port

    def stop(self) -> None:
        self.stopped = True


class FakeMonitor:
    def __init__(self) -> None:
        self.running = False

    def start(self) -> None:
        self.running = True

    def stop(self) -> None:
        self.running = False


class FakeDeviceRepository:
    def __init__(self) -> None:
        self.devices: dict[str, object] = {}

    def list(self):
        return list(self.devices.values())

    def find_by_token_hash(self, token_hash):
        return next((d for d in self.devices.values() if d.token_hash == token_hash), None)

    def add(self, device) -> None:
        self.devices[device.device_id] = device

    def remove(self, device_id) -> bool:
        return self.devices.pop(device_id, None) is not None

    def touch(self, device_id, timestamp) -> None:
        from dataclasses import replace

        device = self.devices.get(device_id)
        if device is not None:
            self.devices[device_id] = replace(device, last_seen=timestamp)


class FakeSettingsStore:
    def __init__(self, settings=None) -> None:
        from pcremote.domain.settings import AppSettings

        self.settings = settings or AppSettings()

    def load(self):
        return self.settings

    def save(self, settings) -> None:
        self.settings = settings


class FakeDiscovery:
    def __init__(self) -> None:
        self.started: tuple | None = None
        self.stopped = False

    def start(self, server_id, name, ip, port, protocol_version) -> None:
        self.started = (server_id, name, ip, port, protocol_version)

    def stop(self) -> None:
        self.stopped = True
