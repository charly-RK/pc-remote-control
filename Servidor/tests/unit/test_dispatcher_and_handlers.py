import pytest

from pcremote.application.command_dispatcher import CommandDispatcher
from pcremote.application.event_bus import EventBus
from pcremote.application.handlers.keyboard import KeyboardHandlers
from pcremote.application.handlers.media import MediaHandlers
from pcremote.application.handlers.mouse import MouseHandlers
from pcremote.application.handlers.system import SystemHandlers
from pcremote.domain.commands import ClickType, KeyAction, MediaCommand, MouseButton, PowerAction
from pcremote.domain.errors import (
    InvalidPayloadError,
    NotAuthenticatedError,
    UnknownCommandError,
)
from pcremote.domain.session import ClientSession

from .fakes import FakeExecutor, FakeKeyboard, FakeMedia, FakeMouse


@pytest.fixture
def parts():
    mouse, kb, media, power, desktop = FakeMouse(), FakeKeyboard(), FakeMedia(), FakeExecutor(), FakeExecutor()
    dispatcher = CommandDispatcher()
    MouseHandlers(mouse).register(dispatcher)
    KeyboardHandlers(kb).register(dispatcher)
    MediaHandlers(media).register(dispatcher)
    SystemHandlers(power, desktop).register(dispatcher)
    return dispatcher, mouse, kb, media, power, desktop


@pytest.fixture
def auth_session():
    s = ClientSession("sid", "10.0.0.2")
    s.authenticated = True
    return s


def test_requires_authentication(parts):
    dispatcher = parts[0]
    with pytest.raises(NotAuthenticatedError):
        dispatcher.dispatch(ClientSession("sid", "ip"), {"action": "mouse_move", "x": 1, "y": 1})


def test_unknown_action_is_rejected(parts, auth_session):
    with pytest.raises(UnknownCommandError):
        parts[0].dispatch(auth_session, {"action": "format_c"})
    with pytest.raises(UnknownCommandError):
        parts[0].dispatch(auth_session, {})


def test_mouse_commands(parts, auth_session):
    dispatcher, mouse, *_ = parts
    dispatcher.dispatch(auth_session, {"action": "mouse_move", "x": 5, "y": -2})
    dispatcher.dispatch(auth_session, {"action": "mouse_click", "button": "right", "type": "double"})
    assert mouse.calls == [("move", 5, -2), ("click", MouseButton.RIGHT, ClickType.DOUBLE)]


def test_invalid_payload_never_reaches_adapter(parts, auth_session):
    dispatcher, mouse, *_ = parts
    with pytest.raises(InvalidPayloadError):
        dispatcher.dispatch(auth_session, {"action": "mouse_move", "x": "abc"})
    assert mouse.calls == []


def test_keyboard_legacy_aliases_and_hotkey(parts, auth_session):
    dispatcher, _, kb, *_ = parts
    dispatcher.dispatch(auth_session, {"action": "down", "key": "a"})
    dispatcher.dispatch(auth_session, {"action": "key_press", "key": "c", "ctrl": True})
    dispatcher.dispatch(auth_session, {"action": "text_input", "text": "hola"})
    assert kb.calls == [("press", "a", KeyAction.DOWN), ("hotkey", ("ctrl", "c")), ("type", "hola")]


def test_media_alias_and_volume(parts, auth_session):
    dispatcher, _, _, media, *_ = parts
    dispatcher.dispatch(auth_session, {"action": "media", "command": "mute"})
    dispatcher.dispatch(auth_session, {"action": "media_control", "command": "set_volume", "level": 0.3})
    assert media.calls == [("send", MediaCommand.MUTE), ("volume", 0.3)]


def test_unknown_media_command_is_not_forwarded_as_key(parts, auth_session):
    with pytest.raises(InvalidPayloadError):
        parts[0].dispatch(auth_session, {"action": "media_control", "command": "alt+f4"})
    assert parts[3].calls == []


def test_system_power_goes_to_power_port(parts, auth_session):
    dispatcher, *_, power, desktop = parts
    dispatcher.dispatch(auth_session, {"action": "system", "command": "lock"})
    dispatcher.dispatch(auth_session, {"action": "system_control", "command": "explorer"})
    assert power.actions == [PowerAction.LOCK] and len(desktop.actions) == 1


def test_event_bus_isolates_failing_subscriber():
    bus, seen = EventBus(), []

    def boom(_):
        raise RuntimeError("x")

    bus.subscribe(str, boom)
    bus.subscribe(str, seen.append)
    bus.publish("evt")
    assert seen == ["evt"]
