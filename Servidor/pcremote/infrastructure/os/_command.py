"""Shared helpers to run external commands safely (no shell, with timeout)."""

from __future__ import annotations

import logging
import subprocess

from pcremote.domain.errors import ExecutionError

logger = logging.getLogger(__name__)

COMMAND_TIMEOUT_SECONDS = 10


def run_command(args: list[str]) -> subprocess.CompletedProcess:
    """Run a command with shell=False and a timeout; failures become ExecutionError."""
    try:
        return subprocess.run(args, shell=False, check=True, timeout=COMMAND_TIMEOUT_SECONDS)
    except (OSError, subprocess.SubprocessError) as exc:
        logger.warning("Command failed: %s (%s)", args[0], exc)
        raise ExecutionError(f"Command failed: {args[0]}") from exc


def run_command_output(args: list[str]) -> str:
    """Like run_command but returns stdout as text (empty on undecodable output)."""
    try:
        done = subprocess.run(
            args, shell=False, check=True, timeout=COMMAND_TIMEOUT_SECONDS, capture_output=True
        )
    except (OSError, subprocess.SubprocessError) as exc:
        logger.warning("Command failed: %s (%s)", args[0], exc)
        raise ExecutionError(f"Command failed: {args[0]}") from exc
    out = done.stdout
    return out.decode("utf-8", errors="replace") if isinstance(out, bytes) else str(out or "")


def spawn_detached(args: list[str]) -> None:
    """Start a long-running GUI program without waiting for it."""
    try:
        subprocess.Popen(args, shell=False, start_new_session=True)  # noqa: S603
    except OSError as exc:
        logger.warning("Could not start: %s (%s)", args[0], exc)
        raise ExecutionError(f"Could not start: {args[0]}") from exc
