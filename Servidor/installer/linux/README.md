# Linux packaging

Build on Linux (PyInstaller does not cross-compile):

```bash
cd Servidor
pip install -r requirements-dev.txt
pyinstaller PCRemoteControl.spec --noconfirm   # produces dist/PCRemoteControl
chmod +x dist/PCRemoteControl
```

System packages (not installed by pip):

- Debian/Ubuntu: `sudo apt install python3-tk xdotool playerctl libappindicator3-1 gir1.2-appindicator3-0.1`
- `xdotool` is used to read the active window (X11 only); `playerctl` is used for media keys.

Desktop entry (`~/.config/autostart/pcremotecontrol.desktop` for start at login, or `~/.local/share/applications/`):

```ini
[Desktop Entry]
Type=Application
Name=PC Remote Control
Exec=/path/to/PCRemoteControl --background
Terminal=false
X-GNOME-Autostart-enabled=true
```

Limits:

- Wayland sessions restrict synthetic mouse and keyboard input; X11 is the supported session.
- The tray icon needs AppIndicator support (GNOME needs an extension).
- Allow the server port through the firewall if one is active (for example `sudo ufw allow 5723/tcp`).
