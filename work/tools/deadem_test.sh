#!/usr/bin/env bash
# Prueba en el juego de DEADMESS y EM (notes/deadmess_em.md). Uso: deadem_test.sh [dm|em] [dir_salida]
#   Arma build/deadem_test (EXE VWF + fuente + DEADMESS/EM de prueba + PILOT.BIN con el piloto 331 "RG Short");
#   con BUILD=build/<nombre> [SLOT=n] usa el texto real de ese build (+ la frase del slot n en el piloto 331, #28)
#   y repite la grabación CP04 con las armas del ν Gundam HWS a potencia 30000 en RAM (POKE) → derribo del guardia.
#   dm: capturas hasta la frase de derribo en el mapa · em: sigue hasta セーブ → 「ｹﾞｰﾑを続けますか?」 いいえ (↑ + ○) → EM.
# Necesita build/exe/SLPS_026.36 y build/font/ (ver notes/fuente_en.md) y la card saves/cards/CP03-….
set -euo pipefail
source "$(dirname "$0")/env.sh"
mode=${1:-dm}; OUT=${2:-$SRW_WORK/emu/shots/deadem_$mode}
cd "$SRW_WORK"
mkdir -p build/deadem
if [ -n "${BUILD:-}" ]; then
  # BUILD=build/<nombre>: texto real del build (todos sus reemplazos) + una frase real en el piloto 331 (#28)
  "$SRW_PY" tools/src/mk_deadem_real.py "$BUILD" build/deadem_test.bin ${SLOT:-} | tail -2
else
"$SRW_PY" tools/src/mk_deadem_test.py iso_jp/SNMAP build/deadem > build/deadem/mk.log
printf '%s\n' '{"id": 331, "full_en": "Royal Guard Full", "short_en": "RG Short"}' > build/deadem/pilot.jsonl
"$SRW_PY" tools/src/pilot_bin.py build build/deadem/pilot.jsonl build/deadem/PILOT.BIN > /dev/null
"$SRW_PY" tools/src/build_iso.py build/deadem_test.bin SLPS_026.36=build/exe/SLPS_026.36 \
  FONTWIN/8FONT_R.TIM=build/font/8FONT_R.TIM FONTWIN/WINTEX.BIN=build/font/WINTEX.BIN \
  SNMAP/DEADMESS.BIN=build/deadem/DEADMESS.BIN SNMAP/EM.BIN=build/deadem/EM.BIN \
  UNITPRAM/PILOT.BIN=build/deadem/PILOT.BIN | tail -1
fi

# potencia 30000 en las 9 armas del ν Gundam HWS (la dirección depende de la tabla de objetos de texto: env.sh)
POKE=$(hws_poke)
if [ "$mode" = em ]; then
  INPUTS="7860:CIRCLE;7960:START;8120:CROSS;8200:RIGHT;8230:RIGHT;8260:RIGHT;8340:CIRCLE"
  f=8460; for k in 1 2 3 4 5 6; do INPUTS+=";$f:DOWN"; f=$((f+30)); done
  INPUTS+=";8680:CIRCLE;8780:UP;8840:CIRCLE;9500:UP;9560:CIRCLE"
  FR=9800,10020; LAST=10100
else
  INPUTS=""; FR=6480; LAST=6500
fi
rm -rf "$OUT"
tools/drive.sh build/deadem_test.cue "$OUT" CARD="$SRW_ROOT/saves/cards/CP03-MAP-E64-T1-amuro-ataque.mcd" \
  INPUTS_FILE="$SRW_ROOT/saves/cards/CP04-MAP-E64-T1-amuro-ataque2.rec.txt" INPUTS="$INPUTS" POKE="$POKE" \
  SHOT_FRAMES="$FR" LAST=$LAST
ls "$OUT"/*.png
