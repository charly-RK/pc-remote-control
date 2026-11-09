"""Mouse adapter built on pyautogui and pynput."""

from __future__ import annotations

import logging

import pyautogui
from pynput.mouse import Button
from pynput.mouse import Controller as PynputMouse

from pcremote.domain.commands import ClickType, MouseButton
from pcremote.domain.errors import ExecutionError

logger = logging.getLogger(__name__)

pyautogui.FAILSAFE = False
pyautogui.PAUSE = 0

_BUTTONS = {
    MouseButton.LEFT: Button.left,
    MouseButton.RIGHT: Button.right,
    MouseButton.MIDDLE: Button.middle,
}


class PyAutoGuiMouse:
    def __init__(self) -> None:
        self._mouse = PynputMouse()

    def move_relative(self, dx: int, dy: int) -> None:
        try:
            pyautogui.moveRel(dx, dy)
        except pyautogui.PyAutoGUIException as exc:
            raise ExecutionError(f"Mouse move failed: {exc}") from exc

    def click(self, button: MouseButton, click_type: ClickType) -> None:
        target = _BUTTONS[button]
        try:
            if click_type is ClickType.SINGLE:
                self._mouse.click(target)
            elif click_type is ClickType.DOUBLE:
                self._mouse.click(target, 2)
            elif click_type is ClickType.DOWN:
                self._mouse.press(target)
            elif click_type is ClickType.UP:
                self._mouse.release(target)
        except Exception as exc:  # pynput raises platform specific errors
            logger.warning("Mouse click failed: %s", exc)
            raise ExecutionError(f"Mouse click failed: {exc}") from exc

    def scroll(self, dx: int, dy: int) -> None:
        try:
            if dy:
                pyautogui.scroll(dy)
            if dx:
                pyautogui.hscroll(dx)
        except pyautogui.PyAutoGUIException as exc:
            raise ExecutionError(f"Mouse scroll failed: {exc}") from exc
