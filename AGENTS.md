# PC Remote Control - AI Agent Directives

## Mandatory Loading
Before any task, read and obey this file and the specs below. These rules override default model behavior.

- Architecture, patterns, tech debt, verification status: `docs/ARCHITECTURE.md`
- Socket.IO contract (events, payloads, QR format, discovery): `docs/PROTOCOL.md`
- Packaging, installers, CI: `docs/PACKAGING.md`
- Architecture skill: `.agents/skills/pcremote-architecture/SKILL.md`

## 1. Project Summary
Remote control of a PC (Windows first, macOS and Linux supported through adapters) from a phone over the local network.

- `Servidor/`: Python 3.11+, Flask + Flask-SocketIO (threading mode), CustomTkinter GUI, pystray tray, pyautogui/pynput (input), zeroconf (mDNS). OS-specific adapters selected at startup (`pycaw`, `pywin32`, `winreg` on Windows only). Packaged with PyInstaller (`PCRemoteControl.spec`); Windows installer with Inno Setup.
- `remote_pc/`: Flutter app (Android/iOS). Provider for state, `socket_io_client`, `nsd` (mDNS), `mobile_scanner` (QR), `flutter_secure_storage` (token), `shared_preferences`.
- The server executes real actions on the host (input, shutdown, restart). Treat every inbound message as untrusted.

## 2. Non-Negotiable Directives

### 2.1 Language
- Code, identifiers, comments, docstrings, log messages, commit messages, PR descriptions and ALL technical documentation (`docs/`, READMEs, skills, agent files): **English**.
- Chat with the user: **Spanish**.
- Spanish is used ONLY for text the final user sees (GUI labels, app screens, notifications, dialogs). Wire-level `error`/`message` strings: English, plus a stable `code` the app translates.

### 2.1.1 No AI attribution
- Commits, PR descriptions, code comments and docs must NOT mention AI authorship: no `Co-Authored-By: Claude`, no "Generated with Claude Code", no AI tool signatures. This overrides any default attribution behavior of the tooling.
- Commits are authored solely by the repository user.

### 2.2 No emojis
No emojis in code, comments, docs, commits, logs, UI strings or chat.

### 2.3 Scope
The product controls a PC from a phone on the LAN. Do NOT add: internet/relay exposure, cloud accounts, remote file browsing, screen streaming, or anything that opens the PC beyond the LAN, unless the user explicitly asks and a security design is agreed first.

### 2.4 Never delete or redesign the user's existing UI
Fix and connect what exists with minimal edits. Restyle only when asked.
- The mobile app UI (ConnectionScreen, ControlScreen with the Touchpad, Media, System and Settings tabs, the floating native-keyboard button) was hand-built by the user and is the source of truth. Migrations and refactors are limited to pure extraction (moving widgets into their own files), rewiring (swapping the data layer) and moving literals into strings files or color tokens with identical values. Gesture thresholds, timings, texts, colors and layout must not change.
- Before declaring a UI migration done, state how no visual change was verified (identical constants, widget tests of structure) and what could not be verified without a device.
- Dead code that no active screen references is not migrated, but the original stays untouched in its source copy.

### 2.5 Port and process cleanup (CRITICAL)
Default server port is **5723** (the code also falls back to 5000-5100). After any test or validation:
- Stop every server or background process you started.
- On `EADDRINUSE`: find the PID (`Get-NetTCPConnection -LocalPort 5723` in PowerShell) and stop it before retrying.
- Never leave `python`/`flutter` processes running. Remove temporary build folders (`build/`, `dist/`) you created.

### 2.6 Secrets
`server_pin.json`, `devices.json`, `.env`, keystores and any PIN/token/QR content must never be committed, printed to logs, or returned over HTTP. Do not paste a real PIN or token in docs or chat.

### 2.7 Never touch the user's system configuration from tests
Tests and validation runs must not create or remove real firewall rules, registry autostart entries, LaunchAgents, XDG autostart files or scheduled tasks. Use fakes, monkeypatched `subprocess.run` and `tmp_path`.

## 3. Server Architecture (Layered, Ports and Adapters)
Full detail in `docs/ARCHITECTURE.md`. Summary:

```
presentation -> application -> domain <- infrastructure
```
- `domain/`: pure Python. FORBIDDEN imports: flask, flask_socketio, pyautogui, pynput, pycaw, win32*, winreg, zeroconf, customtkinter, PIL.
- `application/`: auth and pairing, devices, settings, session registry, command dispatcher, handlers, server controller. Depends only on `domain`.
- `infrastructure/`: concrete adapters. Implements `domain/ports.py`. Per-OS adapters live in `infrastructure/platform/`.
- `presentation/`: Socket.IO gateway, minimal HTTP routes (`/health`, `/status`), GUI. Thin: translate and delegate, no business rules.
- `bootstrap.py` is the only composition root. It is the only place that instantiates adapters.

### Mandatory patterns
- **Command + Registry/Dispatcher** for incoming commands. No growing `if/elif` chains.
- **Ports and Adapters** for every OS or library capability.
- **Abstract Factory/Strategy** for per-OS adapters: `create_platform_adapters(app_name, startup_command)` returns a `PlatformAdapters` bundle chosen with `platform.system()`.
- **Dependency injection** through `bootstrap.py`. No mutable module-level state (no new globals like `PIN_CODE`).
- **Observer/event bus** for server-to-GUI notifications instead of passing callbacks.
- **Repository** for persistence (PIN, paired devices, settings).

### Hard rules
1. Handlers validate payloads (types, ranges, enums) before acting. Unknown commands return an error; never forward unknown input to `pyautogui.press`.
2. No `os.system` with built strings. Subprocesses go through `infrastructure/os/_command.run_command` (`shell=False`, timeout, failures wrapped in `ExecutionError`); long-running GUI programs use `spawn_detached`.
3. No bare `except:` and no silent `except Exception: pass`. Catch specific errors; translate domain errors once, in the gateway. The only accepted broad catches are documented isolation boundaries (event subscribers, optional discovery) with a `noqa` comment.
4. No `print`. Use `logging`. Never log the PIN, a token, the QR payload or typed text.
5. One module, one responsibility. Files over about 300 lines or functions over about 40 lines must be split.
6. GUI updates from non-main threads go through `after(0, ...)`.
7. A new command requires: protocol doc entry, domain type, handler, port/adapter if needed, unit test with a fake port. Follow the recipe in `docs/ARCHITECTURE.md` section 8.

### 3.1 Multi-OS rules
1. OS-specific code lives ONLY under `pcremote/infrastructure/platform/` and the adapters it assembles (`os/`, `power/`, `audio/`). Domain, application and presentation never branch on the operating system. The only allowed OS value in presentation is the display string `platform_name` passed in `GuiContext`.
2. Adapters are selected by `create_platform_adapters` (called from `bootstrap.create_platform`) using `platform.system()`. Any other system raises `UnsupportedActionError("Unsupported platform")`.
3. Every new port capability MUST be implemented for Windows, macOS and Linux, or the adapter for that OS must raise `UnsupportedActionError` with a clear message. Silent no-ops are forbidden (the only no-op adapter is `NoopFirewall`, because macOS and Linux need no rule).
4. Windows-only imports (`win32*`, `winreg`, `pycaw`, `comtypes`, `pythoncom`) are never imported at module level outside Windows adapters. Every adapter module must import on every OS (CI verifies it).
5. New adapters need unit tests with monkeypatched `subprocess.run`/`run_command` and `tmp_path` for generated files (LaunchAgent plist, XDG `.desktop`). Never execute real system commands in tests.
6. CI runs lint, tests and a PyInstaller build on `windows-latest`, `macos-latest` and `ubuntu-latest`. A change is not done if it would break any of them.
7. Known limits to respect: Linux input injection works on X11 only (Wayland restricts it); macOS needs the Accessibility and Automation permissions; the macOS `lock` action only sleeps the display.

### 3.2 Firewall and installer rules
1. The firewall rule is **program-based** (the executable, profiles private and domain, any protocol) so it covers the TCP server and UDP mDNS regardless of the port in use. Port-based rules are not used.
2. Creating or removing the rule needs administrator rights. It is done by the installer, or on demand by the headless flags `main.py --configure-firewall` and `main.py --remove-firewall` (exit code 0 on success). The GUI "Configurar" button triggers the same adapter, which relaunches itself elevated when needed.
3. The Windows installer is `Servidor/installer/windows/PCRemoteControl.iss` (Inno Setup 6). It runs elevated, calls `--configure-firewall` on install and `--remove-firewall` on uninstall, and registers autostart with `--background`.
4. On Windows the application must NEVER run as a Windows Service: services live in session 0 and cannot inject input into the user desktop. Use per-user logon autostart.
5. Never modify the user's real firewall, registry or autostart from tests (see 2.7).

## 4. Security Mandates
- Authenticate per connection (`sid`). No command runs before successful `authenticate`.
- Two-stage access: the PIN only pairs a new device; pairing returns a token once, and only its SHA-256 hash is stored (`devices.json`). Reconnections use the token. Revoked devices are disconnected and their token stops working.
- PIN: generated with `secrets`, 6 digits, persisted in the per-user data directory and cleared only when the application exits completely (not on server stop/start); compared with `hmac.compare_digest`. A new PIN is generated after a full exit.
- Rate limit PIN and token attempts per IP (max 5, then a 60 s lock) and disconnect the offender.
- HTTP endpoints never return the PIN or a token. There is no HTTP QR page; the QR is shown only by the local GUI. mDNS announces only server id, name and protocol version.
- CORS must not be `*`. Engine-level debug loggers stay off in production.
- Destructive commands (`shutdown`, `restart`, `sleep`, `logout`) need an explicit confirmation step in the app before being sent.
- Flask `SECRET_KEY` is generated per run. No hardcoded default.

## 5. Mobile App Architecture (Flutter)
The app was migrated from the user's original hand-built app (a single 460-line `WebSocketService` that spoke Engine.IO by hand over `web_socket_channel` and validated the PIN through an HTTP endpoint) into a feature-first structure. The UI is preserved; the data layer was replaced.

Real structure under `remote_pc/lib/`:

```
main.dart                                   # portrait lock, background service init, runApp
app/        app.dart (AppWrapper: ready -> ControlScreen, else ConnectionScreen), providers.dart (composition root),
            theme.dart (reproduces the original look), app_colors.dart (AppColors tokens, values identical to the original)
core/
  protocol/   protocol.dart                 # event names, error codes, Commands and AuthPayloads builders (mirror of docs/PROTOCOL.md)
  network/    command_sender.dart, remote_connection.dart, socket_io_connection.dart, connection_status.dart,
              reconnect_policy.dart, discovery_service.dart, nsd_discovery_service.dart
  storage/    server_store.dart             # saved servers (shared_preferences) + tokens (flutter_secure_storage)
  background/ background_keep_alive.dart (abstraction), flutter_background_keep_alive.dart (Android foreground service)
  haptics/    haptics_service.dart, haptics_preference.dart   # HapticFeedback, controlled by the vibration setting
  ui/         ui_utils.dart
features/
  connection/ data/legacy_connection_source.dart, domain/{qr_payload,manual_input}.dart,
              presentation/{controllers,pages,widgets,connection_strings.dart}
  control/    presentation/{control_screen.dart,control_strings.dart}      # tabs shell
  touchpad/   presentation/{controllers,widgets,touchpad_screen.dart,touchpad_strings.dart}
  keyboard/   presentation/{controllers,widgets,keyboard_strings.dart}     # native-keyboard overlay and floating button
  media/      presentation/{controllers,media_screen.dart,media_strings.dart}
  system/     presentation/{controllers,system_screen.dart,system_strings.dart}
  settings/   data/settings_repository.dart, presentation/{controllers,settings_screen.dart,settings_strings.dart}
```

Replaced pieces: `WebSocketService` became `SocketIoConnection` + `ConnectionController` (pairing token, mDNS rediscovery, backoff reconnection) and the `BackgroundKeepAlive` abstraction. `flutter_vibrate` was removed in favour of `HapticFeedback`. `web_socket_channel` and `http` are gone. Persisted data is compatible: the original settings keys `sensitivity` (default 2.0) and `vibration` are preserved, and the old `last_ip`/`last_pin` values are imported once and then deleted (only the token is kept afterwards).

Rules:
1. State management: **Provider** with `ChangeNotifier` controllers. Do not introduce another state manager.
2. Screens depend on controllers and on the `CommandSender` interface (`isReady`, `fire`, `request`), never on the socket. They never import `socket_io_client`, the concrete connection or the storage layer. Flow: Widget -> Controller -> `CommandSender` -> `SocketIoConnection`.
3. Message names and payload builders live only in `core/protocol/protocol.dart` and mirror `docs/PROTOCOL.md`.
4. The connection is modeled as `ConnectionStatus` (idle, searching, connecting, authenticating, ready, reconnecting, error). No loose booleans.
5. Reconnection (owned by `ConnectionController`): try the saved token against the last known `ip:port`; if that fails, rediscover by server id through mDNS and retry; then fall back to the last `ip:port`. Delays between attempts follow `ReconnectPolicy`: 1, 2, 4, 8, 15 s, then 30 s cap, reset on success. `INVALID_TOKEN` discards the token and asks for the PIN again; `RATE_LIMITED` waits. Reconnect when the app returns to the foreground (iOS cannot keep the socket in background). On Android the foreground service (`BackgroundKeepAlive`) starts when the status becomes ready and stops on disconnect.
6. Tokens are stored in `flutter_secure_storage`, never in `shared_preferences` or logs; the PIN is never stored. Storage failures must not crash the app (in-memory fallback).
7. Destructive system commands (`shutdown`, `restart`, `sleep`, `logout`, see `SystemCommand.isDestructive`) must be confirmed by the user in a Spanish dialog before being sent.
8. `CommandSender.request()` pairs each `command_response` with the oldest pending request (FIFO), because the protocol has no request id. This is correct only while every request gets exactly one response and requests are not reordered. Do not build features that rely on strict correlation until a request id is added in a future protocol version. High-frequency input (mouse, the migrated screens) uses `fire()` and ignores responses.
9. Mouse movement is high-frequency: never rebuild widgets per event; keep the original gesture constants (thresholds, multipliers, timings).
10. User-facing text is Spanish and lives in one strings file per feature (`<feature>_strings.dart`); never scattered in widgets. Colors come from `AppColors`/`Theme`, never hardcoded in widgets; a token must hold exactly the value the original UI used.
11. A file over about 300 lines must be split by pure extraction (widgets into `widgets/`, logic into `controllers/`); no behavior or visual change.
12. `flutter analyze` must report no issues and `flutter test` must be green before reporting done. Use `const` constructors, no `print` (use `debugPrint`), dispose controllers, timers and subscriptions.
13. Tests: feature tests use `FakeCommandSender` (`test/helpers/fake_command_sender.dart`); connection tests use fakes of `RemoteConnection`, `DiscoveryService`, `ServerStore` and `BackgroundKeepAlive`; screens get widget smoke tests with Provider fakes.

### 5.1 Android build toolchain
- Gradle wrapper 8.14.3, Android Gradle Plugin 8.11.1, Kotlin 2.2.20 (the minimums required by Flutter 3.47). Do not downgrade them.
- Never commit a machine-specific `org.gradle.java.home` in `android/gradle.properties` (an absolute path from another PC broke the build once); Gradle uses `JAVA_HOME`.
- `flutter build apk --debug` must succeed before reporting a mobile change as done. Stop the Gradle daemons afterwards with `android/gradlew --stop`.

## 6. UI Rules
Desktop GUI (CustomTkinter) and mobile app:
1. Short titles; no explanatory paragraphs under titles on new screens. Actions sit next to the title.
2. Consistent look across screens: same spacing, card, button and state styles (loading, empty, error). New screens match their siblings.
3. Colors come from one theme object (`theme.py` / `AppColors`), never hardcoded per widget.
4. Text must be readable on every background and state (hover, disabled). Check contrast.
5. Heavy pickers and dialogs open as a modal, not inline.
6. Controls give immediate feedback (pressed state, haptic on mobile when enabled in settings).
7. Mobile layouts must work on small phones and tablets, portrait and landscape; the touchpad area must stay usable. See 6.1 and 6.2 for the mandatory responsive and overlay rules.
8. Desktop tray: pystray needs the main thread on macOS (`run_detached`) and an appindicator on Linux; when the tray is unavailable the window is minimized instead of hidden so it can never be lost.

### 6.1 Responsive layout (Flutter, mandatory)
Every screen must adapt to any screen size, from a 320 px wide small phone to tablets (portrait and landscape), without the red Flutter overflow error (`RenderFlex overflowed`) or clipped content.
1. No fixed pixel sizes that assume one device. Size from the available space: `LayoutBuilder`, `MediaQuery.sizeOf`, `Expanded`/`Flexible`, `FractionallySizedBox`, `AspectRatio`, and `ConstrainedBox` with max widths for large screens.
2. Any column or content that can be taller than the viewport scrolls only when needed: `LayoutBuilder` + `SingleChildScrollView` + `ConstrainedBox(minHeight: viewport height)` keeps the centered look when there is room. Never rely on a screen being tall enough.
3. Text and labels in tight rows use `Flexible`/`Expanded` with `maxLines` and `TextOverflow.ellipsis`, or `FittedBox(fit: BoxFit.scaleDown)` so they only shrink when they do not fit. Respect system font scaling; do not disable it to hide an overflow.
4. Rows of buttons or chips that may not fit use `Wrap` or `Expanded` children instead of fixed widths.
5. Floating, draggable or overlay widgets are clamped to the current screen size on every build (rotation, split screen, tablets).
6. Every new or changed screen is covered by the responsive widget test in `test/responsive/` (sizes 320x568, 360x800, 412x915, tablet portrait 768x1024 and tablet landscape 1024x768, using the real Roboto font via `test/helpers/real_font.dart`, never the default Ahem font which widens text). `expect(tester.takeException(), isNull)` must pass at every size, including states with overlays open (for example the keyboard).
7. Never "fix" an overflow by making the test surface bigger.

### 6.2 Overlays and transient state (Flutter)
1. Transient overlays (native keyboard, sheets, menus) are closed when the user leaves the screen or tab that owns them, and must never reopen by themselves when the user returns.
2. Floating widgets start docked at a screen edge in a spot that does not cover primary controls (the keyboard button starts in the top-left corner, away from the scroll bar on the right and the click buttons at the bottom). The user may drag them, but the default position must not obstruct the UI.

## 7. Validation Before Reporting Done
- Server: `ruff check .` and `pytest -q` (about 1 minute: the contract tests start real servers). For any protocol change, also connect with a real Socket.IO client against a running server and stop it afterwards.
- App: `flutter analyze` (no issues) and `flutter test` (all green); run on a device or emulator for UI changes when possible.
- Say plainly what was NOT verified (for example real-device behavior, mDNS on a real network, camera scanning, macOS and Linux adapters, the packaged `.exe`, the installer, the first CI run).
- Stop everything you started (section 2.5).

## 8. Git Conventions
- Small commits, one concern each, imperative English subject line (for example `Add rate limit to PIN authentication`). No AI attribution lines (see 2.1.1).
- Never commit `server_pin.json`, `devices.json`, `.env`, `dist/`, `build/`, build logs, or the local folder `Nueva carpeta/` (copy of the original app plus a 600 MB zip; it is git-ignored).
- Repository hygiene: the root `.gitignore` started as a generic Python template whose rules (`lib/`, `profile`, `Runner.xcworkspace`, `Icon?`, `*.manifest`) hid Flutter files, so the first GitHub push lacked the whole app (`remote_pc/lib/`). Negation rules now keep them tracked. Before pushing, run `git status --ignored` and `git check-ignore -v <path>` on every new or moved Flutter file (lib, native folders, icons, manifests) and confirm nothing needed is ignored.
- Do not commit or push unless the user asks.
