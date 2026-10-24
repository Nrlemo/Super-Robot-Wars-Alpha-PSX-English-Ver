#!/usr/bin/env bash
# Prueba de menús en inglés (notes/menus.md): ovl_patch.py sobre translation/menus_en.jsonl → ISO build/menus_test
# (EXE VWF + fuente + 8 overlays) y recorrido CP04: título/carga → mapa → batalla (derribo por POKE) → menú del mapa
# → セーブ → "Save complete. Continue playing?". Uso: menus_test.sh [dir_salida]
set -euo pipefail
source "$(dirname "$0")/env.sh"
OUT=${1:-$SRW_WORK/emu/shots/menus_test}
cd "$SRW_WORK"
"$SRW_PY" tools/src/ovl_patch.py --out build/menus
ovl=(); for f in build/menus/*_GRP.BIN; do ovl+=("OVL/$(basename "$f")=$f"); done
"$SRW_PY" tools/src/build_iso.py build/menus_test.bin SLPS_026.36=build/exe/SLPS_026.36 \
  FONTWIN/8FONT_R.TIM=build/font/8FONT_R.TIM FONTWIN/WINTEX.BIN=build/font/WINTEX.BIN "${ovl[@]}" | tail -1
POKE=$(hws_poke)   # ν Gundam HWS a potencia 30000 (env.sh)
INPUTS="7860:CIRCLE;7960:START;8120:CROSS;8200:RIGHT;8230:RIGHT;8260:RIGHT;8340:CIRCLE"
f=8460; for k in 1 2 3 4 5 6; do INPUTS+=";$f:DOWN"; f=$((f+30)); done
INPUTS+=";8680:CIRCLE;8780:UP;8840:CIRCLE"
FR=${FR:-$(seq -s, 600 150 3300),3450,3520,3580,3620,3700,3800,3900,4400,5200,6480,7900,8100,8400,8600,8700,8800,9000,9400}
rm -rf "$OUT"
tools/drive.sh build/menus_test.cue "$OUT" CARD="$SRW_ROOT/saves/cards/CP03-MAP-E64-T1-amuro-ataque.mcd" \
  INPUTS_FILE="$SRW_ROOT/saves/cards/CP04-MAP-E64-T1-amuro-ataque2.rec.txt" INPUTS="$INPUTS" POKE="$POKE" \
  SHOT_FRAMES="$FR" LAST=${LAST:-9450}
"$SRW_PY" tools/src/sheet.py "$OUT" "$OUT/sheet.png" 8 | tail -1
