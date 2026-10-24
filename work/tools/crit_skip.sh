#!/usr/bin/env bash
# #271: nuevo juego → primer ataque del prólogo (Photon Torpedo de Excelion) con "Animation: OFF"; el aviso 「クリティカル」
# del mapa sale ~f12590–12700 (dynarec; en -interpreter la ruta se desfasa). Uso: crit_skip.sh <imagen.cue> <dir_salida> [VAR=valor ...]
# Pasos: menú (○ f10960) → ↓ Attack (11150) → ○ (11300) → arma 4 con 3×↓ (11500–11700) → ○ (11800) → R1 objetivo (11950)
# → ○ vista previa (12100) → ○ abre el cuadro Animation (12300) → ↓ OFF (12450) → ○ (12600). Cada paso necesita la
# ventana anterior ya abierta: pulsaciones ≤ 5 cuadros en ↓ (8 = 2 pasos) y ≥ 100 cuadros de separación.
set -euo pipefail
source "$(dirname "$0")/env.sh"
CUE="$(realpath "$1")"; OUT="$2"; shift 2
I="2000:START;2800:START;3400:LEFT;3600:START;4200:CIRCLE;5000:DOWN;5200:DOWN;5400:CIRCLE;5700:CIRCLE;6100:DOWN;6300:CIRCLE;6600:CIRCLE;7000:START;"
for f in $(seq 8960 60 10700); do I="$I$f:CIRCLE;"; done
I="${I}10960:CIRCLE:8;11150:DOWN:5;11300:CIRCLE:8;11500:DOWN:5;11600:DOWN:5;11700:DOWN:5;11800:CIRCLE:8;11950:R1:8;12100:CIRCLE:8;12300:CIRCLE:8;12450:DOWN:5;12600:CIRCLE:8;"
cd "$SRW_WORK"
exec tools/drive.sh "$CUE" "$OUT" FRESH_CARD=1 INPUTS="$I" "$@"
