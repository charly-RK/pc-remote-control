"""About view (static)."""

from __future__ import annotations

import customtkinter as ctk

from ..theme import Theme, card, font


class AboutView(ctk.CTkScrollableFrame):
    def __init__(
        self,
        parent: ctk.CTkBaseClass,
        theme: Theme,
        version: str,
        logo: ctk.CTkImage | None = None,
    ) -> None:
        super().__init__(parent, fg_color="transparent")
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        main = card(self, theme, radius=20)
        main.grid(row=0, column=0, sticky="nsew", padx=100, pady=50)
        main.grid_columnconfigure(0, weight=1)
        main.grid_rowconfigure(1, weight=1)

        header = ctk.CTkFrame(main, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", pady=(50, 0))
        if logo is not None:
            ctk.CTkLabel(header, text="", image=logo).pack(pady=(0, 20))
        ctk.CTkLabel(header, text="PC Remote Control", font=font(32, bold=True), text_color=theme.text_primary).pack()
        ctk.CTkLabel(header, text=f"v{version}", font=font(14), text_color=theme.primary).pack(pady=(5, 0))

        content = ctk.CTkFrame(main, fg_color="transparent")
        content.grid(row=1, column=0, sticky="nsew", padx=50, pady=30)
        ctk.CTkLabel(
            content,
            text=(
                "Aplicación de control remoto avanzada que te permite "
                "gestionar tu PC desde cualquier dispositivo móvil."
            ),
            font=font(14),
            text_color=theme.text_secondary,
            wraplength=500,
            justify="center",
        ).pack(pady=(0, 30))

        footer = ctk.CTkFrame(main, fg_color="transparent")
        footer.grid(row=2, column=0, sticky="ew", pady=(0, 30))
        ctk.CTkLabel(
            footer,
            text="PC Remote Control - Desarrollador RISK KEEP",
            font=font(11),
            text_color=theme.text_secondary,
        ).pack()
