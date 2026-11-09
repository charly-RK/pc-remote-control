# -*- mode: python ; coding: utf-8 -*-
import os
import sys

IS_WIN = sys.platform == 'win32'
IS_MAC = sys.platform == 'darwin'

hidden_imports = [
    'engineio.async_drivers.threading',
    'simple_websocket',
    'zeroconf',
    'zeroconf._utils.ipaddress',
    'zeroconf._handlers.answers',
    'socketio',
    'engineio',
    'flask',
    'flask_socketio',
    'werkzeug',
    'jinja2',
    'PIL',
    'PIL._tkinter_finder',
    'pyautogui',
    'pynput',
    'pynput.keyboard',
    'pynput.mouse',
    'pystray',
    'customtkinter',
    'qrcode',
]

if IS_WIN:
    hidden_imports += [
        'win32gui',
        'win32con',
        'win32api',
        'win32event',
        'pywintypes',
        'pythoncom',
        'comtypes',
        'winreg',
        'pycaw',
        'pystray._win32',
        'pynput.keyboard._win32',
        'pynput.mouse._win32',
    ]
elif IS_MAC:
    hidden_imports += [
        'pystray._darwin',
        'pynput.keyboard._darwin',
        'pynput.mouse._darwin',
        'Quartz',
        'AppKit',
    ]
else:
    hidden_imports += [
        'pystray._xorg',
        'pystray._appindicator',
        'pystray._gtk',
        'pynput.keyboard._xorg',
        'pynput.mouse._xorg',
    ]

if IS_WIN:
    icon_path = 'src\\Logo.ico'
elif IS_MAC:
    icon_path = 'src/Logo.icns' if os.path.exists('src/Logo.icns') else None
else:
    icon_path = None

a = Analysis(
    ['main.py'],
    pathex=['.'],
    binaries=[],
    datas=[('src', 'src')],
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib',
        'numpy',
        'pandas',
        'scipy',
        'pytest',
        'setuptools',
        'eventlet',
    ],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='PCRemoteControl',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=IS_WIN,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=icon_path,
)

if IS_MAC:
    app = BUNDLE(
        exe,
        name='PCRemoteControl.app',
        icon=icon_path,
        bundle_identifier='com.riskkeep.pcremotecontrol',
        info_plist={
            'LSUIElement': True,
            'NSAppleEventsUsageDescription': (
                'PC Remote Control needs automation access to control media and system actions.'
            ),
            'CFBundleShortVersionString': '1.0.0',
        },
    )
