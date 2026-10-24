#!/usr/bin/env bash
# PoC del formato de diálogo (issue #23) con mk_formato_test.py + EXE VWF + fuente + menús de la última build:
#   A | A2 | B | N | ancho   SCRIPT.BIN con la escena del escenario 62 → ruta CP12, una captura por línea
#   mapa             SNMSG.BIN con el diálogo del prólogo (slots 2–30) → arranque en frío, una captura por línea
# Uso: formato_test.sh <variante> [dir_salida]      (necesita una build previa: tools/build.sh)
set -euo pipefail
source "$(dirname "$0")/env.sh"
V=$1; OUT=${2:-$SRW_WORK/emu/shots/formato_$V}
cd "$SRW_WORK"
B=${FILES:-$(ls -d build/srwa_en_*/files | tail -1)}   # FILES=build/<N>/files para elegir la build
T=build/formato_$V; mkdir -p "$T"
"$SRW_PY" tools/src/mk_formato_test.py "$V" "$T/texto.jsonl"
if [ "$V" = mapa ]; then
  "$SRW_PY" tools/src/snmsg.py build "$T/texto.jsonl" "$T/SNMSG.BIN" | tail -1; REP=(SNMAP/SNMSG.BIN="$T/SNMSG.BIN")
else
  "$SRW_PY" tools/src/script_bin.py build "$T/texto.jsonl" "$T/SCRIPT.BIN" | tail -1; REP=(BUSTUP/SCRIPT.BIN="$T/SCRIPT.BIN")
fi
ovl=(); for f in "$B"/../menus/*_GRP.BIN; do ovl+=("OVL/$(basename "$f")=$f"); done
"$SRW_PY" tools/src/build_iso.py "$T/formato_$V.bin" SLPS_026.36="$B/SLPS_026.36" \
  FONTWIN/8FONT_R.TIM="$B/FONTWIN/8FONT_R.TIM" FONTWIN/WINTEX.BIN="$B/FONTWIN/WINTEX.BIN" \
  "${REP[@]}" "${ovl[@]}" | tail -1
rm -rf "$OUT"
if [ "$V" = mapa ]; then
  # card virgen → título → archivo de sistema → protagonista y pareja por defecto → diálogo (f8700); CIRCLE cada 60
  I="2000:START;2800:START;3400:LEFT;3600:START;4200:CIRCLE;5000:DOWN;5200:DOWN;5400:CIRCLE;5700:CIRCLE;6100:DOWN;6300:CIRCLE;6600:CIRCLE;7000:START;"
  for f in $(seq 8960 60 10700); do I="$I$f:CIRCLE;"; done
  tools/drive.sh "$T/formato_$V.cue" "$OUT" FRESH_CARD=1 INPUTS="$I" SHOT_FRAMES="$(seq -s, 8930 60 10730)" LAST=10740
else
  # CP12: título LEFT→LOAD → intermisión → 5×DOWN hasta 次のマップへ → escena; CIRCLE cada 150, captura en el medio
  I="2000:START;2900:LEFT;3500:CIRCLE;4300:CIRCLE;4800:CIRCLE;"
  for f in $(seq 5600 150 6200); do I="$I$f:DOWN;"; done
  I="${I}6450:CIRCLE;"
  for f in $(seq 6600 150 11400); do I="$I$f:CIRCLE;"; done
  tools/drive.sh "$T/formato_$V.cue" "$OUT" CARD="$SRW_ROOT/saves/cards/CP12-INT-E62-mixta-1714.mcd" INPUTS="$I" \
    SHOT_FRAMES="$(seq -s, 7125 150 11475)" LAST=11500
fi
"$SRW_PY" tools/src/sheet.py "$OUT" "$OUT/sheet.png" 5 | tail -1
