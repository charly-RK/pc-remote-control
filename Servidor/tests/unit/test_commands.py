import pytest

from pcremote.domain.commands import (
    ClickType,
    KeyAction,
    KeyPress,
    MediaCommand,
    MediaRequest,
    MouseButton,
    MouseClick,
    MouseMove,
    PowerAction,
    SystemRequest,
    TextInput,
)
from pcremote.domain.errors import InvalidPayloadError


def test_mouse_move_parses_numbers():
    assert MouseMove.parse({"x": 3, "y": -4.0}) == MouseMove(3, -4)


@pytest.mark.parametrize("payload", [{"x": "1"}, {"x": True}, {"y": 10**9}])
def test_mouse_move_rejects_bad_values(payload):
    with pytest.raises(InvalidPayloadError):
        MouseMove.parse(payload)


def test_mouse_click_defaults_and_validation():
    assert MouseClick.parse({}) == MouseClick(MouseButton.LEFT, ClickType.SINGLE)
    with pytest.raises(InvalidPayloadError):
        MouseClick.parse({"button": "side"})


def test_key_press_legacy_action_names():
    assert KeyPress.parse({"action": "down", "key": "a"}).action is KeyAction.DOWN
    assert KeyPress.parse({"action": "key_press", "key": "a"}).action is KeyAction.PRESS


def test_key_press_requires_key_and_reads_modifiers():
    with pytest.raises(InvalidPayloadError):
        KeyPress.parse({"action": "press"})
    cmd = KeyPress.parse({"key": "c", "ctrl": True, "meta": True})
    assert cmd.has_modifiers and cmd.ctrl and cmd.win


def test_text_input_limits():
    assert TextInput.parse({"text": "hola"}).text == "hola"
    for bad in ({"text": ""}, {"text": 5}, {"text": "x" * 5000}):
        with pytest.raises(InvalidPayloadError):
            TextInput.parse(bad)


def test_media_unknown_command_is_rejected():
    with pytest.raises(InvalidPayloadError):
        MediaRequest.parse({"command": "format_disk"})


def test_media_set_volume_needs_valid_level():
    assert MediaRequest.parse({"command": "set_volume", "level": 0.5}).level == 0.5
    for bad in ({"command": "set_volume"}, {"command": "set_volume", "level": 2}):
        with pytest.raises(InvalidPayloadError):
            MediaRequest.parse(bad)
    assert MediaRequest.parse({"command": "mute"}).command is MediaCommand.MUTE


def test_system_request_routes_power_and_rejects_unknown():
    assert SystemRequest.parse({"command": "shutdown"}).power is PowerAction.SHUTDOWN
    assert SystemRequest.parse({"command": "explorer"}).desktop is not None
    with pytest.raises(InvalidPayloadError):
        SystemRequest.parse({"command": "rm -rf"})
