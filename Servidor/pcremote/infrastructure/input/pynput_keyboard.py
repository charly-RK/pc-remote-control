"""Keyboard adapter built on pynput and pyautogui."""

from __future__ import annotations

import logging

import pyautogui
from pynput import keyboard

from pcremote.domain.commands import KeyAction
from pcremote.domain.errors import ExecutionError

logger = logging.getLogger(__name__)

# Keys that pynput handles poorly on some layouts: send them through pyautogui.
_PYAUTOGUI_KEYS = {"escape": "esc", "f11": "f11", "home": "home", "win": "win"}

_KEY_MAP = {
    "escape": keyboard.Key.esc,
    "f11": keyboard.Key.f11,
    "home": keyboard.Key.home,
    "enter": keyboard.Key.enter,
    "tab": keyboard.Key.tab,
    "delete": keyboard.Key.delete,
    "backspace": keyboard.Key.backspace,
    "ctrl": keyboard.Key.ctrl,
    "alt": keyboard.Key.alt,
    "shift": keyboard.Key.shift,
    "win": keyboard.Key.cmd,
    "cmd": keyboard.Key.cmd,
    "insert": keyboard.Key.insert,
    "menu": keyboard.Key.menu,
    "page_up": keyboard.Key.page_up,
    "page_down": keyboard.Key.page_down,
    "end": keyboard.Key.end,
    "caps_lock": keyboard.Key.caps_lock,
    "print_screen": keyboard.Key.print_screen,
    "scroll_lock": keyboard.Key.scroll_lock,
    "pause": keyboard.Key.pause,
}


def _resolve_key(key: str) -> keyboard.Key | str:
    if key in _KEY_MAP:
        return _KEY_MAP[key]
    if len(key) > 1 and hasattr(keyboard.Key, key):
        return getattr(keyboard.Key, key)
    return key


class PynputKeyboard:
    def __init__(self) -> None:
        self._controller = keyboard.Controller()

    def press_key(self, key: str, action: KeyAction) -> None:
        try:
            if action is KeyAction.PRESS and key in _PYAUTOGUI_KEYS:
                pyautogui.press(_PYAUTOGUI_KEYS[key])
                return
            target = _resolve_key(key)
            if action is KeyAction.PRESS:
                self._controller.press(target)
                self._controller.release(target)
            elif action is KeyAction.DOWN:
                self._controller.press(target)
            elif action is KeyAction.UP:
                self._controller.release(target)
        except (pyautogui.PyAutoGUIException, ValueError, self._controller.InvalidKeyException) as exc:
            logger.warning("Key %s failed: %s", action.value, exc)
            raise ExecutionError(f"Key {action.value} failed: {exc}") from exc

    def hotkey(self, keys: list[str]) -> None:
        try:
            pyautogui.hotkey(*keys)
        except pyautogui.PyAutoGUIException as exc:
            raise ExecutionError(f"Hotkey failed: {exc}") from exc

    def type_text(self, text: str) -> None:
        try:
            self._controller.type(text)
        except (ValueError, self._controller.InvalidCharacterException) as exc:
            raise ExecutionError("Typing text failed") from exc
