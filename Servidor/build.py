"""Build the executable with PyInstaller using PCRemoteControl.spec."""

import shutil
import sys
from pathlib import Path

import PyInstaller.__main__

ROOT = Path(__file__).resolve().parent


def output_location() -> Path:
    if sys.platform == "win32":
        return ROOT / "dist" / "PCRemoteControl.exe"
    if sys.platform == "darwin":
        return ROOT / "dist" / "PCRemoteControl.app"
    return ROOT / "dist" / "PCRemoteControl"


def build() -> None:
    for folder in ("dist", "build"):
        shutil.rmtree(ROOT / folder, ignore_errors=True)
    PyInstaller.__main__.run([str(ROOT / "PCRemoteControl.spec"), "--clean", "--noconfirm"])
    print(f"Build output: {output_location()}")


if __name__ == "__main__":
    build()
