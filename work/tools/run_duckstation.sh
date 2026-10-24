#!/usr/bin/env bash
# Abre DuckStation (portable, audio muteado) con la imagen indicada (default: ISO JP original).
source "$(dirname "$0")/env.sh"
[ -n "${DISPLAY:-}" ] || { echo "sin pantalla: usar tools/drive.sh (capturas) en esta máquina" >&2; exit 1; }
exec "$SRW_WORK/emu/duckstation/DuckStation-x64.AppImage" -batch "${1:-$SRW_JP_CUE}"
