#!/usr/bin/env bash
# Abre PCSX-Redux (portable, audio muteado, con debugger) con la imagen indicada.
source "$(dirname "$0")/env.sh"
[ -n "${DISPLAY:-}" ] || { echo "sin pantalla: usar tools/drive.sh (capturas) en esta máquina" >&2; exit 1; }
cd "$SRW_WORK/emu/pcsx-redux"
exec "$SRW_TOOLS/bin/PCSX-Redux-HEAD-x86_64.AppImage" -portable -iso "${1:-$SRW_JP_CUE}" -run
