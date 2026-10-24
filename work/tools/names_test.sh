#!/usr/bin/env bash
# Prueba de nombres en inglés (#13 ROBOT.RAF, #14 PILOT.BIN) sobre una ISO del pipeline (build.sh):
#   cp04 — mapa del escenario 64 → lista de armas → batalla (derribo por POKE) → menú del mapa (la ruta de menus_test.sh)
#   cp12 — card mixta CP12: LOAD → intermisión (lista de unidades / pilotos, ver notes/script_bin.md)
# Uso: names_test.sh cue dir_salida [cp04|cp12]
set -euo pipefail
source "$(dirname "$0")/env.sh"
CUE=$(realpath "$1"); OUT=$(realpath -m "$2"); ROUTE=${3:-cp04}
cd "$SRW_WORK"
rm -rf "$OUT"
case "$ROUTE" in
cp04)
  POKE=$(hws_poke)   # ν Gundam HWS a potencia 30000 (env.sh)
  INPUTS="7860:CIRCLE;7960:START;8120:CROSS;8200:RIGHT;8230:RIGHT;8260:RIGHT;8340:CIRCLE"
  FR=${FR:-$(seq -s, 600 150 3300),3450,3520,3580,3620,3700,3800,3900,4400,5200,6480,7900,8100,8400}
  tools/drive.sh "$CUE" "$OUT" CARD="$SRW_ROOT/saves/cards/CP03-MAP-E64-T1-amuro-ataque.mcd" \
    INPUTS_FILE="$SRW_ROOT/saves/cards/CP04-MAP-E64-T1-amuro-ataque2.rec.txt" INPUTS="$INPUTS" POKE="$POKE" \
    SHOT_FRAMES="$FR" LAST=${LAST:-8500} ;;
cp12)   # LOAD de CP12 → menú de intermisión (~f4850): 1ª opción, RIGHT pasa de página; × vuelve; 2ª opción igual
  I="2000:START;2900:LEFT;3500:CIRCLE;4300:CIRCLE;4800:CIRCLE;5400:CIRCLE;5900:CIRCLE;6300:RIGHT;6600:CROSS;"
  I+="6900:CROSS;7200:DOWN;7500:CIRCLE;8000:CIRCLE;8400:RIGHT;8700:CROSS;9000:CROSS"
  tools/drive.sh "$CUE" "$OUT" CARD="$SRW_ROOT/saves/cards/CP12-INT-E62-mixta-1714.mcd" INPUTS="$I" \
    SHOT_FRAMES="${FR:-$(seq -s, 4900 150 9300)}" LAST=${LAST:-9300} ;;
esac
"$SRW_PY" tools/src/sheet.py "$OUT" "$OUT/sheet.png" 8 | tail -1
