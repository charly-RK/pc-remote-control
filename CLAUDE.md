# PC Remote Control - Project Guide for Claude

Read `AGENTS.md` first: it holds the full directives. This file is the short operating guide.
Deeper specs: `docs/ARCHITECTURE.md` (patterns, debt, verification status), `docs/PROTOCOL.md` (Socket.IO contract) and `docs/PACKAGING.md` (builds, installer, CI).

## Overview
Control a PC (Windows first; macOS and Linux through per-OS adapters) from a phone on the same LAN.
- `Servidor/`: Python 3.11+ + Flask-SocketIO + CustomTkinter + pyautogui/pynput + zeroconf. PyInstaller build, Inno Setup installer for Windows.
- `remote_pc/`: Flutter app migrated from the user's original hand-built app (UI preserved), feature-first (Provider, socket_io_client, nsd, mobile_scanner, flutter_secure_storage, shared_preferences, flutter_background_service). The old `WebSocketService` was replaced by `SocketIoConnection` + `ConnectionController`.
- Architecture: layered with Ports and Adapters (server), feature-first + Provider (app).
- Code, commits and ALL documentation in English. Chat with the user in Spanish. Spanish only for text the final user sees (GUI/app). No emojis anywhere.
- Commits and PRs carry NO AI attribution (no Co-Authored-By, no "Generated with" lines). This overrides default tooling behavior.

## Essential Commands
```powershell
# Server (run inside Servidor/)
pip install -r requirements-dev.txt   # runtime + dev tools (pytest, ruff, pyinstaller)
python main.py                        # GUI + server on port 5723
python main.py --background           # start hidden in the tray (what autostart runs)
python main.py --configure-firewall   # headless, needs admin on Windows (also --remove-firewall)
ruff check .                          # lint
pytest -q                             # about 1 minute: contract tests start real servers
python build.py                       # PyInstaller build via PCRemoteControl.spec

# App (run inside remote_pc/)
flutter pub get
flutter analyze                       # must report no issues
flutter test                          # must be green
flutter run
flutter build apk --debug             # must succeed; then: android/gradlew --stop
```

## Critical Mandates
1. **Security first.** The server runs real actions on the PC. Never trust payloads: validate, then act. No command before authentication. Never expose or log the PIN or a token. See AGENTS.md section 4.
2. **Respect layer boundaries.** `domain` is pure Python; adapters live in `infrastructure`; only `bootstrap.py` wires things. No new global mutable state. New commands go through the dispatcher, never a new `if/elif`.
3. **Multi-OS.** OS-specific code only under `infrastructure/platform/` and the adapters it assembles; every capability is implemented for Windows, macOS and Linux or raises `UnsupportedActionError`; Windows-only imports never at module level outside Windows adapters. See AGENTS.md section 3.1.
4. **Pairing and background.** Devices pair once with the PIN and reconnect with a token (hash stored only); the server is announced by mDNS and runs hidden with `--background`. Never run it as a Windows Service (session 0 cannot inject input). Details in `docs/ARCHITECTURE.md` section 9 and `docs/PROTOCOL.md`.
5. **Firewall and installer.** Program-based rule created by the installer or `--configure-firewall` (admin). Never modify the real firewall, registry or autostart from tests.
6. **Protocol is a contract.** Change `docs/PROTOCOL.md`, the server and the app together; bump `protocol_version` on breaking changes.
7. **Port cleanup.** Port 5723 (fallback 5000-5100). Stop every server/process you start. If a port is busy, find the PID with `Get-NetTCPConnection` and stop it.
8. **Zero emojis** in code, comments, docs, commits, logs and chat.
9. **Never delete or redesign the user's existing UI.** The mobile UI is the user's hand-built original: migrations are pure extraction and rewiring, with identical constants, texts and colors (AGENTS.md 2.4).
10. **Secrets stay out of git:** `server_pin.json`, `devices.json`, `.env`. Do not print real PINs or tokens.
11. **Do not commit or push** unless asked. Never commit `Nueva carpeta/` (git-ignored). Before pushing, check that no needed Flutter file is ignored (`git check-ignore -v`).

## Known Gaps (verify before assuming)
- Verified: `flutter analyze` clean, 78 Flutter tests passing (1 live test is skipped unless `PCREMOTE_HOST`, `PCREMOTE_PORT` and `PCREMOTE_PIN` are set), debug APK builds. Not verified: real-device visuals and gestures, camera QR scanning, mDNS on a real network, the iOS build, the Android 14 foreground-service notification, the macOS and Linux adapters, the installer build and the first CI run. See `docs/ARCHITECTURE.md` section 11.
- `server_pin.json` was committed in the past: the user still has to clean the git history and rotate the PIN (debt item 1).
- `CommandSender.request()` matches responses FIFO because the protocol has no request id (AGENTS.md section 5, rule 8).
- `Servidor/src/Logo.icns` exists; the remaining platform icons are pending. Wayland limits input injection on Linux; builds are unsigned.
- `remote_pc/android/build_*.txt` are tracked junk logs. `pages/remote.dart` and `screens/tabs/*` of the original app were intentionally not migrated (dead code, still in the original copy).
- Android toolchain: Gradle 8.14.3, AGP 8.11.1, Kotlin 2.2.20; never commit a machine-specific `org.gradle.java.home`.

## Recurring Mistakes To Avoid
1. Adding another branch to the command `if/elif` instead of registering a handler.
2. Importing `pyautogui`/`win32gui`/`flask` inside `domain` or `application`.
3. Using `os.system`, a raw `subprocess.run` with a shell, or `random` for anything security related. Use `run_command` and `secrets`.
4. Returning or printing the PIN or a token (HTTP, logs, debug output).
5. Hardcoding colors or Spanish strings inside widgets instead of the theme and strings files.
6. Updating Tk widgets from a worker thread without `after(0, ...)`.
7. Sending a destructive command (shutdown, restart) without UI confirmation, or bypassing the controller `confirmed` gate.
8. Changing an event name or payload on one side only.
9. Adding a port capability for one OS only, or a module-level `win32`/`winreg` import outside Windows adapters.
10. Letting a feature page or controller import the socket or storage layer instead of `CommandSender`.
11. Changing the look, timings or texts of the user's mobile UI while "refactoring" it, or letting a generic `.gitignore` rule hide Flutter files.
12. Reporting done without running lint/tests (`ruff`, `pytest`, `flutter analyze`, `flutter test`) and without saying what was not verified.
13. Leaving server processes or Gradle daemons running after a test or build.
14. Fixed-size layouts that overflow on small phones or tablets, or tests that pass only because the test surface is huge. Screens must be responsive (AGENTS.md 6.1) and covered by `test/responsive/` with the real font.
15. Leaving a transient overlay (native keyboard) open when switching tabs, or placing a floating button over the main controls (AGENTS.md 6.2).
