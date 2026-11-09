"""Application settings use case (load, update, persist)."""

from __future__ import annotations

import uuid
from dataclasses import replace

from pcremote.domain.ports import SettingsStore
from pcremote.domain.settings import AppSettings


class SettingsService:
    def __init__(self, store: SettingsStore) -> None:
        self._store = store
        self._settings = store.load()
        if not self._settings.server_id:
            self._settings = replace(self._settings, server_id=uuid.uuid4().hex)
            self._store.save(self._settings)

    @property
    def settings(self) -> AppSettings:
        return self._settings

    def update(self, **changes: object) -> AppSettings:
        self._settings = replace(self._settings, **changes)
        self._store.save(self._settings)
        return self._settings
