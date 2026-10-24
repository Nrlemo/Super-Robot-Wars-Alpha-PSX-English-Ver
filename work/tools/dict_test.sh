#!/usr/bin/env bash
# Prueba de los diccionarios (#15 DC.BIN / DR.BIN) sobre una ISO del pipeline (build.sh): título → オプション (overlay
# SNDM) → キャラクター事典 / ロボット大図鑑. La card CP12 solo aporta la configuración (SRSYS).
# Uso: dict_test.sh cue dir_salida [titulo|dc|dr]   (INPUTS=… / FR=… / LAST=… pisan la ruta)
set -euo pipefail
source "$(dirname "$0")/env.sh"
CUE=$(realpath "$1"); OUT=$(realpath -m "$2"); ROUTE=${3:-titulo}
cd "$SRW_WORK"
rm -rf "$OUT"
CARD="$SRW_ROOT/saves/cards/CP12-INT-E62-mixta-1714.mcd"
# Título con card: arranca en LOAD y descarta la 1.ª pulsación; RIGHT ×2 → CONTINUE → OPTION; ○ → menú オプション
# (サウンドセレクト / キャラクター事典 / ロボット大図鑑 / デモセレクト / カラオケモード). La card CP12 tiene 3 fichas
# de personajes (Koji, Sayaka, Ashura) y 6 de robots.
T="2000:START;2900:RIGHT;3500:RIGHT;4100:RIGHT;5000:CIRCLE;5400:DOWN"
case "$ROUTE" in
titulo) I=${INPUTS:-2000:START}; FR=${FR:-2400,2800}; L=${LAST:-2850} ;;
dc)     # lista → Koji Kabuto (scroll ×2) → × → Baron Ashura (seiyuu en 2 líneas)
        I="$T;5800:CIRCLE;6400:CIRCLE;7000:DOWN;7400:DOWN;7800:CROSS;8300:DOWN;8700:CIRCLE;9300:DOWN"
        FR=6200,6700,7200,7600,8600,9100,9600; L=9650 ;;
dr)     # lista → Grungust Type-2 (scroll) → × → G Hawk
        I="$T;5800:DOWN;6200:CIRCLE;6800:CIRCLE;7400:DOWN;7800:CROSS;8300:RIGHT;8700:CIRCLE;9300:DOWN"
        FR=6600,7200,7700,8600,9100,9600; L=9650 ;;
libre)  I=${4//+/;}; FR=$5; L=$6 ;;   # exploración: dict_test.sh cue dir libre 2000:START+2900:LEFT 3100,3400 3450
*) echo "ruta desconocida: $ROUTE" >&2; exit 2 ;;
esac
tools/drive.sh "$CUE" "$OUT" CARD="$CARD" INPUTS="$I" SHOT_FRAMES="$FR" LAST="$L"
"$SRW_PY" tools/src/sheet.py "$OUT" "$OUT/sheet.png" 8 | tail -1
