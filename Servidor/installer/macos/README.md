# macOS packaging

Build the app bundle on a Mac (PyInstaller does not cross-compile):

```bash
cd Servidor
pip install -r requirements-dev.txt
pyinstaller PCRemoteControl.spec --noconfirm   # produces dist/PCRemoteControl.app
```

Create a disk image:

```bash
hdiutil create -volname "PC Remote Control" -srcfolder dist/PCRemoteControl.app -ov -format UDZO dist/PCRemoteControl.dmg
```

Notes:

- The bundle runs as a menu-bar/background app (`LSUIElement`).
- On first run the user must grant Accessibility permission (System Settings > Privacy & Security > Accessibility) so mouse and keyboard control works. Media and system actions may also ask for Automation permission.
- The app is unsigned. Gatekeeper will warn until it is signed and notarized with an Apple Developer ID.
- Optional: place a `Logo.icns` in `src/` to give the bundle an icon.
- Start at login is handled by the application itself (LaunchAgent).
