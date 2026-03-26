#!/usr/bin/env zsh

set -euo pipefail

script_dir=${0:A:h}

if command -v python3 >/dev/null 2>&1; then
    exec python3 "$script_dir/play_agent_notification.py" "${1:-finish}"
fi

if command -v python >/dev/null 2>&1; then
    exec python "$script_dir/play_agent_notification.py" "${1:-finish}"
fi

repo_root=${script_dir:h}
mode=${1:-finish}

case "$mode" in
    finish)
        sound_path="$repo_root/ai-finished.wav"
        fallback_sound="/System/Library/Sounds/Glass.aiff"
        ;;
    interaction)
        sound_path="$repo_root/ai-input-needed.wav"
        fallback_sound="/System/Library/Sounds/Basso.aiff"
        ;;
    *)
        echo "Unknown sound mode: $mode" >&2
        exit 1
        ;;
esac

if command -v afplay >/dev/null 2>&1; then
    if [[ -f "$sound_path" ]]; then
        afplay "$sound_path" >/dev/null 2>&1 &
        exit 0
    fi

    afplay "$fallback_sound" >/dev/null 2>&1 &
    exit 0
fi

osascript -e 'beep' >/dev/null 2>&1 || true
