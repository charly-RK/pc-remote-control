from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from pcremote.application.command_dispatcher import CommandDispatcher
from pcremote.domain.commands import CommandResult, KeyPress, TextInput
from pcremote.domain.ports import KeyboardController


class KeyboardHandlers:
    # 'press', 'down' and 'up' are legacy action names kept for compatibility.
    KEY_ACTIONS = ("key_press", "press", "down", "up")

    def __init__(self, keyboard: KeyboardController) -> None:
        self._keyboard = keyboard

    def register(self, dispatcher: CommandDispatcher) -> None:
        dispatcher.register(self.KEY_ACTIONS, self.key)
        dispatcher.register("text_input", self.text)

    def key(self, data: Mapping[str, Any]) -> CommandResult:
        cmd = KeyPress.parse(data)
        if cmd.has_modifiers:
            modifiers = (("ctrl", cmd.ctrl), ("alt", cmd.alt), ("shift", cmd.shift), ("win", cmd.win))
            keys = [name for name, enabled in modifiers if enabled]
            keys.append(cmd.key)
            self._keyboard.hotkey(keys)
            return CommandResult.success("Hotkey: " + "+".join(keys))
        self._keyboard.press_key(cmd.key, cmd.action)
        return CommandResult.success(f"Key {cmd.action.value}: {cmd.key}")

    def text(self, data: Mapping[str, Any]) -> CommandResult:
        cmd = TextInput.parse(data)
        self._keyboard.type_text(cmd.text)
        return CommandResult.success(f"Typed {len(cmd.text)} characters")
