"""PC Remote Control entry point (GUI plus server)."""

from __future__ import annotations

import argparse
import logging
import sys

from pcremote.bootstrap import APP_NAME, configure_logging, create_context, create_platform
from pcremote.infrastructure.os.single_instance import SingleInstance
from pcremote.presentation.gui.app import run_gui


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog=APP_NAME)
    parser.add_argument("--background", action="store_true", help="start hidden in the system tray")
    parser.add_argument(
        "--configure-firewall", action="store_true", help="allow the app through the firewall and exit"
    )
    parser.add_argument("--remove-firewall", action="store_true", help="remove the firewall rule and exit")
    return parser.parse_args(argv)


def run_firewall_task(configure: bool) -> int:
    """Headless task used by installers. Needs administrator rights on Windows."""
    firewall = create_platform().firewall
    done = firewall.configure() if configure else firewall.remove()
    return 0 if done else 1


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    configure_logging()
    logger = logging.getLogger("pcremote.main")

    if args.configure_firewall or args.remove_firewall:
        return run_firewall_task(configure=args.configure_firewall)

    instance = SingleInstance(APP_NAME)
    if not instance.acquire():
        logger.warning("Another instance is already running; exiting")
        return 0
    try:
        context = create_context(lambda: logger.info("Application exit requested"))
        run_gui(context, start_hidden=args.background)
    finally:
        instance.release()
    return 0


if __name__ == "__main__":
    sys.exit(main())
