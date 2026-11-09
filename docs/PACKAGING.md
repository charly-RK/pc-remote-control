# Packaging and distribution

PyInstaller does not cross-compile: build each OS on that OS (locally or with the CI matrix in `.github/workflows/ci.yml`). The build definition is `Servidor/PCRemoteControl.spec`, which adapts to `sys.platform`.

Status: only the Windows build path has been exercised on a developer machine. The macOS and Linux builds, the installer and the CI workflow are untested until CI runs for the first time.

## Build per OS

From `Servidor/`:

```bash
pip install -r requirements-dev.txt
python build.py            # or: pyinstaller PCRemoteControl.spec --noconfirm
```

| OS | Output | Notes |
|---|---|---|
| Windows | `dist/PCRemoteControl.exe` (onefile) | Same as before the spec became platform-aware. |
| macOS | `dist/PCRemoteControl.app` | Menu-bar/background app (`LSUIElement`). `src/Logo.icns` is optional. |
| Linux | `dist/PCRemoteControl` | Needs system packages, see below. |

Linux system packages: `python3-tk`, `xdotool` (active window, X11 only), `playerctl` (media keys), `libappindicator` (tray). macOS dependencies (`pyobjc-framework-Quartz`, `pyobjc-framework-Cocoa`) and Windows ones (`pywin32`, `pycaw`) are selected automatically by environment markers in `requirements.txt`.

## Windows installer

1. Build the exe (above).
2. Run `installer/windows/build_installer.ps1` (requires Inno Setup 6). The installer is written to `dist/installer/`.

The installer runs elevated and:

- installs to `Program Files\PC Remote Control` and adds a Start Menu shortcut;
- offers an optional "Start with Windows" task, which writes the `PCRemoteControl` value under HKCU Run with `--background`;
- runs `PCRemoteControl.exe --configure-firewall` to create the firewall rule;
- on uninstall runs `PCRemoteControl.exe --remove-firewall` and removes the Run value.

## Firewall requirement

The server must accept inbound connections on private networks, otherwise phones cannot connect (this is a common cause of "cannot connect"). Creating the rule needs administrator rights, so the installer does it. Flags handled by `main.py`:

- `--configure-firewall`: creates the inbound allow rule for the application.
- `--remove-firewall`: removes it.

Without an installer, run the exe once from an elevated prompt with `--configure-firewall`. On Linux with a firewall enabled, allow the port manually (for example `ufw allow 5723/tcp`).

## macOS permissions

- Accessibility (System Settings > Privacy & Security > Accessibility): required for mouse and keyboard control.
- Automation: may be requested for media and system actions (`NSAppleEventsUsageDescription` is set in the bundle).
- Start at login is handled by the app (LaunchAgent).

## Linux limits

- X11 is supported. Wayland restricts synthetic input and active-window detection.
- The tray needs AppIndicator support (GNOME requires an extension).
- Start at login uses an XDG autostart `.desktop` entry; an example is in `Servidor/installer/linux/README.md`.

## Code signing

Builds are unsigned. Windows SmartScreen shows an "unknown publisher" warning, and macOS Gatekeeper blocks the app until it is signed and notarized with an Apple Developer ID. Sign releases before distributing them widely.

## Continuous integration

`.github/workflows/ci.yml` runs on Windows, macOS and Ubuntu: install dependencies, `ruff check .`, `pytest -q` (under `xvfb-run` on Linux), PyInstaller build, and upload of `Servidor/dist` as an artifact. Contract tests start local servers; any test that depends on a Windows-only module must skip itself on other OSes.
