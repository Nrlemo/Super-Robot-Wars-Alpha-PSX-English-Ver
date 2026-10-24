#!/usr/bin/env bash
# Rutas de regresión en el emulador (server1, sin pantalla): corre cada ruta con drive.sh sobre una imagen y deja por
# ruta las capturas (PNG), la hoja de contactos (sheet.png) y el control automático (shots_check.py).
# Uso: regresion.sh <imagen.cue> <dir_salida> [ruta ...]           (sin rutas: boot prologo cp04 cp12)
#      REF=<dir_salida de otra corrida> regresion.sh …             además compara cuadro a cuadro (<ruta>/diff.png)
# Rutas (checklist: notes/checklist_regresion.md, niveles N1 y N2):
#   boot     card virgen: logos → título → LOAD → "sin archivo de sistema" (EXE, fuente, FS)           ~1 min
#   prologo  nueva partida → ENTR → diálogo del prólogo → 1ª batalla (battle_prologue.sh fresh)         ~4 min
#            ⚠ desfasada (2026-09-28): en el menú de la Excelion el CIRCLE elige 移動 y no 攻撃 (#52)
#   cp04     card CP03 + grabación CP04: Amuro ataca con Fin Funnel (armas, nombres, frases de batalla)  ~2 min
#   cp12     card CP12: LOAD → menú de intermisión → 次のマップへ → escena del escenario 62 (IMIS, SCRIPT)  ~3 min
# Sale con 1 si alguna ruta falla el control (faltan capturas, todo de un color, emulador congelado).
# Los cuadros de cp04 y cp12 salen de las grabaciones y de notes/script_bin.md; si el texto nuevo cambia los tiempos,
# ajustarlos acá (la grabación depende del cuadro exacto: ver saves/LEEME.md).
set -euo pipefail
source "$(dirname "$0")/env.sh"
[ $# -ge 2 ] || { sed -n '2,15p' "$0"; exit 2; }
CUE="$(realpath "$1")"; OUT="$(realpath -m "$2")"; shift 2
RUTAS=("$@"); [ ${#RUTAS[@]} -gt 0 ] || RUTAS=(boot prologo cp04 cp12)
CARDS="$SRW_ROOT/saves/cards"
FALLAS=()
for r in "${RUTAS[@]}"; do
  D="$OUT/$r"
  echo "== $r → $D"
  case "$r" in
    boot)     # card virgen: sin ella, la memcard1.mcd que dejó la corrida anterior cambia lo que se ve.
              # START salta el video (sus cortes negros caen en cualquier cuadro): logos, título, LOAD, "sin archivo
              # de sistema" (medido 2026-09-28, igual en la japonesa y en la inglesa)
      SF="600,1500,2400,3000,4000"
      "$SRW_TOOLS/drive.sh" "$CUE" "$D" FRESH_CARD=1 INPUTS="2000:START;2800:START;3400:LEFT;3600:START" \
        SHOT_FRAMES="$SF" LAST=4000 ;;
    prologo)  # los cuadros que captura battle_prologue.sh en modo fresh (7900+4460 … 9800+4460, cada 60)
      SF="$(seq -s, 12360 60 14260)"
      "$SRW_TOOLS/battle_prologue.sh" "$CUE" "$D" fresh ;;
    cp04)     # la grabación termina ~f5400; desde f3300 se ven el mapa, la lista de armas y la vista previa
      SF="$(seq -s, 3300 60 5700)"
      "$SRW_TOOLS/drive.sh" "$CUE" "$D" CARD="$CARDS/CP03-MAP-E64-T1-amuro-ataque.mcd" \
        INPUTS_FILE="$CARDS/CP04-MAP-E64-T1-amuro-ataque2.rec.txt" SHOT_FRAMES="$SF" LAST=5700 ;;
    cp12)     # título LEFT→LOAD, menú de intermisión ~f4850, 5×DOWN hasta 次のマップへ, CIRCLE cada 150 en la escena
      I="2000:START;2900:LEFT;3500:CIRCLE;4300:CIRCLE;4800:CIRCLE;"
      for f in $(seq 5600 150 6200); do I="$I$f:DOWN;"; done
      I="${I}6450:CIRCLE;"
      for f in $(seq 6600 150 11100); do I="$I$f:CIRCLE;"; done
      SF="4900,6300,$(seq -s, 6600 300 11100)"
      "$SRW_TOOLS/drive.sh" "$CUE" "$D" CARD="$CARDS/CP12-INT-E62-mixta-1714.mcd" INPUTS="$I" \
        SHOT_FRAMES="$SF" LAST=11200 ;;
    *) echo "ruta desconocida: $r (boot, prologo, cp04, cp12)" >&2; exit 2 ;;
  esac
  N="$(tr ',' '\n' <<<"$SF" | grep -c .)"
  "$SRW_PY" "$SRW_TOOLS/src/sheet.py" "$D" >/dev/null || true
  if ! "$SRW_PY" "$SRW_TOOLS/src/shots_check.py" "$D" --expect "$N" ${REF:+--ref "$REF/$r"}; then FALLAS+=("$r"); fi
done
if [ ${#FALLAS[@]} -gt 0 ]; then echo "FALLARON: ${FALLAS[*]}"; exit 1; fi
echo "OK: ${RUTAS[*]} → revisar a ojo $OUT/<ruta>/sheet.png${REF:+ y diff.png}"
