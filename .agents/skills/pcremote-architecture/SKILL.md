---
name: "pcremote-architecture"
description: "Enforces the layered Ports and Adapters architecture, per-OS platform adapters, command dispatcher pattern, pairing security, firewall/installer rules, Flutter app structure and the Socket.IO contract for the PC Remote Control server (Python) and mobile app (Flutter)"
opencode/slash: true
opencode/autoinvoke: true
---

# PC Remote Control Architecture and Operating Directives

Authoritative sources: `AGENTS.md`, `docs/ARCHITECTURE.md`, `docs/PROTOCOL.md`, `docs/PACKAGING.md`. Read them when in doubt.

## 1. Server layers (Python)
```
presentation -> application -> domain <- infrastructure      (bootstrap.py wires everything)
```
- `domain`: pure Python (commands, errors, events, session, devices, settings, ports). No flask, pyautogui, pynput, pycaw, win32, winreg, zeroconf, customtkinter.
- `application`: AuthService (pairing + token), DeviceService, SettingsService, SessionRegistry, EventBus, CommandDispatcher, handlers, ServerController. Depends only on `domain`.
- `infrastructure`: adapters implementing `domain/ports.py`. Per-OS adapters in `infrastructure/platform/{windows,macos,linux}.py`, assembled by `create_platform_adapters`.
- `presentation`: Socket.IO gateway, `/health` and `/status` only, CustomTkinter GUI. Translate and delegate only.

## 2. Patterns to apply
- Command + Registry (dispatcher) instead of `if/elif`.
- Ports and Adapters for every OS capability; fakes in tests.
- Abstract Factory/Strategy for per-OS adapters (`platform.system()`).
- Dependency injection from `bootstrap.py`; no mutable module globals.
- Observer/event bus for server-to-GUI events (`DevicePaired`, `DeviceRevoked`, ...).
- Repository for PIN, paired devices and settings.

## 3. Multi-OS rules
- OS-specific code only under `infrastructure/platform/` and the adapters it assembles.
- Every port capability implemented for Windows, macOS and Linux, or `UnsupportedActionError` with a clear message. No silent no-ops (except `NoopFirewall`).
- Windows-only imports (`win32*`, `winreg`, `pycaw`, `comtypes`) never at module level outside Windows adapters; every module imports on every OS.
- Subprocesses via `infrastructure/os/_command.run_command` (shell=False, timeout, `ExecutionError`).
- Adapter tests: monkeypatched subprocess and `tmp_path`; never run real system commands. CI matrix: windows, macos, ubuntu.

## 4. Adding a command (checklist)
1. Document it in `docs/PROTOCOL.md`.
2. Add type/payload in `domain/commands.py` (and extend a port if a new capability is needed).
3. Implement the adapter for Windows, macOS and Linux (or raise `UnsupportedActionError`).
4. Write the handler in `application/handlers/` and register it in `bootstrap.py`.
5. Unit test with a fake port.
6. App side: builder in `core/protocol/protocol.dart`, controller in the feature, UI. Destructive commands need the controller `confirmed` gate and a dialog.

## 5. Security
- Auth per connection; the PIN pairs once and returns a token; only the SHA-256 hash is stored; revoked devices are disconnected.
- PIN via `secrets`, persisted until the application exits completely, `hmac.compare_digest`; rate limit 5 failures per IP then 60 s lock (PIN and token).
- Never expose or log the PIN, a token, the QR payload or typed text. No HTTP QR page.
- No `os.system`; no wildcard CORS; no hardcoded `SECRET_KEY`; secrets never committed.

## 6. Firewall and installer
- Program-based rule (private + domain, any protocol), created by the Inno Setup installer or `--configure-firewall` (admin); removed with `--remove-firewall`.
- Never run as a Windows Service (session 0 cannot inject input). Per-user logon autostart with `--background`.
- Tests never touch the real firewall, registry or autostart.

## 7. Mobile app (Flutter)
- The app is the user's original hand-built app migrated feature-first. NEVER redesign its UI: migrations are pure extraction (widgets into files), rewiring (data layer) and literals into strings files or `AppColors` tokens with identical values. Keep gesture thresholds, timings, texts and colors.
- Structure: `app/` (app.dart, providers.dart composition root, theme.dart, app_colors.dart), `core/{protocol,network,storage,background,haptics,ui}`, `features/{connection,control,touchpad,keyboard,media,system,settings}` with `presentation/{controllers,widgets,*_strings.dart}`.
- `WebSocketService` (hand-written Engine.IO, PIN over HTTP) was replaced by `SocketIoConnection` + `ConnectionController` and `BackgroundKeepAlive`. Provider + ChangeNotifier. Screens depend on controllers and `CommandSender`, never the socket. Protocol names only in `core/protocol/protocol.dart`.
- `ConnectionStatus` state machine; reconnect: saved token -> mDNS rediscovery by server id -> last ip:port; backoff 1, 2, 4, 8, 15, 30 s. Android foreground service starts when ready, stops on disconnect.
- Tokens in `flutter_secure_storage` (the PIN is never stored). Original keys `sensitivity` (2.0) and `vibration` preserved; `last_ip`/`last_pin` imported once then deleted. Haptics via `HapticFeedback`.
- `request()` matches responses FIFO (no request id in protocol v1); use `fire()` for high-frequency input. Files over ~300 lines are split by pure extraction.
- Build toolchain: Gradle 8.14.3, AGP 8.11.1, Kotlin 2.2.20; never commit a machine-specific `org.gradle.java.home`; stop daemons with `android/gradlew --stop`.
- `flutter analyze` clean, `flutter test` green and `flutter build apk --debug` succeeding before done.
- Repo hygiene: the generic root `.gitignore` once hid Flutter files (`lib/`, `profile`, `Runner.xcworkspace`, `Icon?`, `*.manifest`); check with `git check-ignore -v` before pushing. Never commit `Nueva carpeta/`.

## 7.1 Responsive UI (Flutter)
- Every screen adapts from 320 px phones to tablets (portrait and landscape) with no `RenderFlex overflowed` error.
- Size from available space (`LayoutBuilder`, `Flexible`/`Expanded`, `Wrap`); scroll only when content does not fit (`LayoutBuilder` + `SingleChildScrollView` + `ConstrainedBox(minHeight)`); labels use `FittedBox(scaleDown)` or ellipsis.
- Clamp floating widgets to the current screen; start them docked at an edge, never over primary controls.
- Close transient overlays (native keyboard) when leaving their tab; they must not reopen by themselves.
- Cover screens with `test/responsive/` (320x568, 360x800, 412x915, 768x1024, 1024x768, real Roboto font via `test/helpers/real_font.dart`); never enlarge the test surface to hide an overflow.

## 8. Language, style, cleanup
- Code, commits and all documentation in English; Spanish only for end-user UI text and chat. No emojis.
- No AI attribution in commits or PRs (no Co-Authored-By, no "Generated with" lines).
- Use `logging` (server) and `debugPrint` (app); no `print`.
- Stop every server/process after validation (port 5723, fallback 5000-5100).
- Say plainly what was not verified.
