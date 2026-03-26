#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import platform
import shutil
import subprocess
import sys


MACOS_SOUNDS = {
    "finish": "/System/Library/Sounds/Glass.aiff",
    "interaction": "/System/Library/Sounds/Basso.aiff",
}

LINUX_CANBERRA_EVENTS = {
    "finish": "complete",
    "interaction": "dialog-information",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Play a system-default notification sound for agent events."
    )
    parser.add_argument(
        "mode",
        choices=["finish", "interaction"],
        nargs="?",
        default="finish",
    )
    return parser.parse_args()


def is_wsl() -> bool:
    release = platform.release().lower()
    return bool(os.environ.get("WSL_DISTRO_NAME")) or "microsoft" in release


def play_with_afplay(mode: str) -> bool:
    afplay = shutil.which("afplay")
    if not afplay:
        return False

    subprocess.Popen(
        [afplay, MACOS_SOUNDS[mode]],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return True


def play_windows_native(mode: str) -> bool:
    if os.name != "nt":
        return False

    import winsound

    sound_type = (
        winsound.MB_ICONASTERISK
        if mode == "finish"
        else winsound.MB_ICONQUESTION
    )
    winsound.MessageBeep(sound_type)
    return True


def play_windows_host_from_wsl(mode: str) -> bool:
    if not is_wsl():
        return False

    powershell = shutil.which("powershell.exe")
    if not powershell:
        return False

    sound_name = "Asterisk" if mode == "finish" else "Question"
    command = (
        f"[System.Media.SystemSounds]::{sound_name}.Play(); "
        "Start-Sleep -Milliseconds 200"
    )

    subprocess.Popen(
        [
            powershell,
            "-NoProfile",
            "-NonInteractive",
            "-ExecutionPolicy",
            "Bypass",
            "-Command",
            command,
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return True


def play_with_canberra(mode: str) -> bool:
    player = shutil.which("canberra-gtk-play")
    if not player:
        return False

    subprocess.Popen(
        [
            player,
            "--id",
            LINUX_CANBERRA_EVENTS[mode],
            "--description",
            f"GitHub Copilot agent {mode}",
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return True


def ring_terminal_bell() -> bool:
    try:
        sys.stdout.write("\a")
        sys.stdout.flush()
        return True
    except OSError:
        return False


def main() -> int:
    args = parse_args()

    if sys.platform == "darwin" and play_with_afplay(args.mode):
        return 0

    if play_windows_native(args.mode):
        return 0

    if play_windows_host_from_wsl(args.mode):
        return 0

    if play_with_canberra(args.mode):
        return 0

    return 0 if ring_terminal_bell() else 1


if __name__ == "__main__":
    raise SystemExit(main())
