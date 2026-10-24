#!/usr/bin/env bash
# Smoke test sin intervención: bootea una imagen, captura frames y genera PNG + contact.png.
# Uso: smoke_boot.sh <imagen.cue> <dir_salida> [frames=600,1500,2400,3600]
set -euo pipefail
FRAMES="${3:-600,1500,2400,3600}"
exec "$(dirname "$0")/drive.sh" "$1" "$2" SHOT_FRAMES="$FRAMES" LAST="${FRAMES##*,}"
