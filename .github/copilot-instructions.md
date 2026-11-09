# GitHub Copilot Instructions - PC Remote Control

Full rules: `AGENTS.md`. Specs: `docs/ARCHITECTURE.md`, `docs/PROTOCOL.md`, `docs/PACKAGING.md`.

## Core Mandates
1. Language: code, comments, logs, commits and all documentation in English. Spanish only for end-user UI text and chat. No emojis. No AI attribution in commits or PRs.
2. Server (Python, Flask-SocketIO): layered architecture with Ports and Adapters. `domain` is pure Python (no flask, pyautogui, pynput, win32). Adapters live in `infrastructure`. Only `bootstrap.py` wires dependencies.
3. Commands go through a registry-based dispatcher. Never add `if/elif` branches for new commands.
4. No mutable module-level state, no `print` (use `logging`), no `os.system`; subprocesses use `infrastructure/os/_command.run_command` (shell=False, timeout, `ExecutionError`); no silent `except Exception`.
5. Multi-OS: OS-specific code only under `infrastructure/platform/` and the adapters it assembles, selected by `create_platform_adapters` via `platform.system()`. Every port capability is implemented for Windows, macOS and Linux or raises `UnsupportedActionError`. No module-level `win32`/`winreg`/`pycaw` imports outside Windows adapters. Adapter tests monkeypatch subprocess and use `tmp_path`.
6. Security: authenticate per connection (PIN pairs once, token afterwards, only the token hash is stored), validate every payload, never expose or log the PIN or a token, rate limit attempts, no wildcard CORS, no HTTP QR page, destructive commands need confirmation in the app.
7. Firewall and installer: program-based rule created by the installer or `--configure-firewall`/`--remove-firewall` (admin); never run as a Windows Service; tests must never touch the real firewall, registry or autostart.
8. App (Flutter): migrated from the user's hand-built app; `app/` (app, providers, theme, app_colors), `core/{protocol,network,storage,background,haptics,ui}`, `features/{connection,control,touchpad,keyboard,media,system,settings}`. Never redesign the UI: migrations are pure extraction and rewiring with identical constants, texts and colors. Provider with ChangeNotifier controllers; screens depend on controllers and `CommandSender`, never the socket; tokens in `flutter_secure_storage`; Spanish UI text in per-feature strings files; colors from `AppColors` (values identical to the original); files over ~300 lines are split by extraction; `flutter analyze` clean, `flutter test` green and `flutter build apk --debug` succeeding (Gradle 8.14.3, AGP 8.11.1, Kotlin 2.2.20; no machine-specific `org.gradle.java.home`; run `android/gradlew --stop` afterwards).
8b. Repository hygiene: the generic root `.gitignore` once hid Flutter files; run `git check-ignore -v` on new Flutter files before pushing; never commit `Nueva carpeta/`.
9. Protocol changes must update `docs/PROTOCOL.md`, server and app together.
10. Terminate any server or process started for testing (port 5723, fallback 5000-5100).
11. Responsive UI (Flutter): every screen adapts from 320 px phones to tablets with no overflow errors (LayoutBuilder, Flexible/Expanded, scroll only when needed, FittedBox/ellipsis for labels); covered by `test/responsive/` with the real Roboto font; transient overlays (keyboard) close when leaving their tab; floating widgets start docked at an edge and never cover primary controls.
