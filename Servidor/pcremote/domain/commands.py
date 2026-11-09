"""Command vocabulary and validated payloads.

Payload classes parse the raw dictionaries sent by clients. Clients are not
trusted: every field is type-checked and range-checked here before any adapter
is invoked.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from enum import Enum
from typing import Any, TypeVar

from .errors import InvalidPayloadError

MAX_TEXT_LENGTH = 2000
MAX_KEY_LENGTH = 32
MAX_MOUSE_DELTA = 10_000


class MouseButton(str, Enum):
    LEFT = "left"
    RIGHT = "right"
    MIDDLE = "middle"


class ClickType(str, Enum):
    SINGLE = "single"
    DOUBLE = "double"
    DOWN = "down"
    UP = "up"


class KeyAction(str, Enum):
    PRESS = "press"
    DOWN = "down"
    UP = "up"


class MediaCommand(str, Enum):
    PLAY_PAUSE = "play_pause"
    NEXT = "next"
    PREVIOUS = "previous"
    VOLUME_UP = "volume_up"
    VOLUME_DOWN = "volume_down"
    MUTE = "mute"
    SET_VOLUME = "set_volume"
    GAME_BAR = "game_bar"
    RECORD = "record"
    MIC_MUTE = "mic_mute"
    GET_STATE = "get_state"


class PowerAction(str, Enum):
    SHUTDOWN = "shutdown"
    RESTART = "restart"
    SLEEP = "sleep"
    LOGOUT = "logout"
    LOCK = "lock"


class DesktopAction(str, Enum):
    TASK_MANAGER = "task_manager"
    EXPLORER = "explorer"
    CAPTURE = "capture"
    SHOW_DESKTOP = "show_desktop"
    OPEN_BROWSER = "open_browser"


@dataclass(frozen=True)
class MediaState:
    """Snapshot of the PC audio state. Any field is None when it cannot be read.

    `playing` is a heuristic (some app is rendering audio), not a player query.
    """

    volume: float | None = None
    muted: bool | None = None
    playing: bool | None = None

    def to_dict(self) -> dict[str, Any]:
        return {"volume": self.volume, "muted": self.muted, "playing": self.playing}


@dataclass(frozen=True)
class CommandResult:
    """Outcome of a command. Serialized as the `command_response` payload."""

    ok: bool
    message: str = ""
    code: str | None = None
    data: dict[str, Any] | None = None

    @classmethod
    def success(cls, message: str = "", data: dict[str, Any] | None = None) -> "CommandResult":
        return cls(ok=True, message=message, data=data)

    @classmethod
    def failure(cls, code: str, message: str) -> "CommandResult":
        return cls(ok=False, message=message, code=code)


E = TypeVar("E", bound=Enum)


def _int_field(data: Mapping[str, Any], name: str, limit: int) -> int:
    value = data.get(name, 0)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise InvalidPayloadError(f"'{name}' must be a number")
    number = int(value)
    if abs(number) > limit:
        raise InvalidPayloadError(f"'{name}' is out of range")
    return number


def _enum_field(data: Mapping[str, Any], name: str, enum_type: type[E], default: E | None = None) -> E:
    raw = data.get(name, default.value if default is not None else None)
    try:
        return enum_type(raw)
    except ValueError:
        raise InvalidPayloadError(f"'{name}' has an unsupported value") from None


def _bool_field(data: Mapping[str, Any], name: str) -> bool:
    return bool(data.get(name, False))


@dataclass(frozen=True)
class MouseMove:
    dx: int
    dy: int

    @classmethod
    def parse(cls, data: Mapping[str, Any]) -> "MouseMove":
        return cls(_int_field(data, "x", MAX_MOUSE_DELTA), _int_field(data, "y", MAX_MOUSE_DELTA))


@dataclass(frozen=True)
class MouseClick:
    button: MouseButton
    click_type: ClickType

    @classmethod
    def parse(cls, data: Mapping[str, Any]) -> "MouseClick":
        return cls(
            _enum_field(data, "button", MouseButton, MouseButton.LEFT),
            _enum_field(data, "type", ClickType, ClickType.SINGLE),
        )


@dataclass(frozen=True)
class MouseScroll:
    dx: int
    dy: int

    @classmethod
    def parse(cls, data: Mapping[str, Any]) -> "MouseScroll":
        return cls(_int_field(data, "dx", MAX_MOUSE_DELTA), _int_field(data, "dy", MAX_MOUSE_DELTA))


@dataclass(frozen=True)
class KeyPress:
    key: str
    action: KeyAction
    ctrl: bool = False
    alt: bool = False
    shift: bool = False
    win: bool = False

    @property
    def has_modifiers(self) -> bool:
        return self.ctrl or self.alt or self.shift or self.win

    @classmethod
    def parse(cls, data: Mapping[str, Any]) -> "KeyPress":
        key = data.get("key")
        if not isinstance(key, str) or not key or len(key) > MAX_KEY_LENGTH:
            raise InvalidPayloadError("'key' must be a non-empty string")
        # The legacy protocol sends the state as the top-level action
        # ('press', 'down', 'up'); 'key_press' means a plain press.
        raw_action = data.get("action")
        action = KeyAction(raw_action) if raw_action in {a.value for a in KeyAction} else KeyAction.PRESS
        return cls(
            key=key,
            action=action,
            ctrl=_bool_field(data, "ctrl"),
            alt=_bool_field(data, "alt"),
            shift=_bool_field(data, "shift"),
            win=_bool_field(data, "win") or _bool_field(data, "meta"),
        )


@dataclass(frozen=True)
class TextInput:
    text: str

    @classmethod
    def parse(cls, data: Mapping[str, Any]) -> "TextInput":
        text = data.get("text")
        if not isinstance(text, str) or not text:
            raise InvalidPayloadError("'text' must be a non-empty string")
        if len(text) > MAX_TEXT_LENGTH:
            raise InvalidPayloadError("'text' is too long")
        return cls(text)


@dataclass(frozen=True)
class MediaRequest:
    command: MediaCommand
    level: float | None = None

    @classmethod
    def parse(cls, data: Mapping[str, Any]) -> "MediaRequest":
        command = _enum_field(data, "command", MediaCommand)
        level: float | None = None
        if command is MediaCommand.SET_VOLUME:
            raw = data.get("level")
            if isinstance(raw, bool) or not isinstance(raw, (int, float)) or not 0.0 <= float(raw) <= 1.0:
                raise InvalidPayloadError("'level' must be a number between 0 and 1")
            level = float(raw)
        return cls(command, level)


@dataclass(frozen=True)
class SystemRequest:
    """Either a power action or a desktop action."""

    power: PowerAction | None = None
    desktop: DesktopAction | None = None

    @classmethod
    def parse(cls, data: Mapping[str, Any]) -> "SystemRequest":
        raw = data.get("command")
        if raw in {a.value for a in PowerAction}:
            return cls(power=PowerAction(raw))
        if raw in {a.value for a in DesktopAction}:
            return cls(desktop=DesktopAction(raw))
        raise InvalidPayloadError("'command' has an unsupported value")
