"""QR code rendering for the connection panel."""

from __future__ import annotations

import logging
from pathlib import Path

import customtkinter as ctk
import qrcode
from PIL import Image

from .theme import Theme

logger = logging.getLogger(__name__)

QR_DISPLAY_SIZE = (220, 220)


def render_qr(data: str, logo_path: Path | None, theme: Theme) -> Image.Image:
    """Render `data` as a themed QR image with an optional centered logo."""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)

    img = qr.make_image(fill_color=theme.primary, back_color=theme.card_bg).convert("RGB")

    if logo_path is not None and logo_path.exists():
        try:
            _paste_logo(img, logo_path, theme)
        except (OSError, ValueError):
            logger.warning("Could not add logo to QR code", exc_info=True)
    return img


def _paste_logo(img: Image.Image, logo_path: Path, theme: Theme) -> None:
    logo = Image.open(logo_path)
    logo_size = int(img.size[0] * 0.15)
    logo = logo.resize((logo_size, logo_size), Image.Resampling.LANCZOS)
    pos = ((img.size[0] - logo_size) // 2, (img.size[1] - logo_size) // 2)
    backdrop = Image.new("RGB", (logo_size + 4, logo_size + 4), theme.card_bg)
    img.paste(backdrop, (pos[0] - 2, pos[1] - 2))
    img.paste(logo, pos, mask=logo if logo.mode == "RGBA" else None)


def to_ctk_image(img: Image.Image) -> ctk.CTkImage:
    return ctk.CTkImage(light_image=img, dark_image=img, size=QR_DISPLAY_SIZE)
