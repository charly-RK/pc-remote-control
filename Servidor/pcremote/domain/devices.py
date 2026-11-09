"""Paired device entity. Only a hash of the token is ever stored."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PairedDevice:
    device_id: str
    name: str
    token_hash: str
    created_at: float
    last_seen: float
