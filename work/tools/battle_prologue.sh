#!/usr/bin/env bash
# Lleva el juego hasta la primera batalla del prólogo (Excelion dispara 光子魚雷 a un 宇宙怪獣・兵隊) y saca capturas.
# Uso: battle_prologue.sh <imagen.cue> <dir_salida> [state|fresh] [VAR=valor ...]   (VARs de drive.sh: SHOT_FRAMES, LAST, BP_*...)
#   state: carga emu/states/poc_prologue.sstate (rápido; el EXE queda el original del state → no sirve para probar parches al EXE)
#   fresh: bootea desde cero con memory card virgen (necesario para probar el VWF u otros parches al EXE); +4460 cuadros
#          (medido: el diálogo inicial aparece en f8700 fresh vs f4240 state)
# Cuadros de referencia (modo state; en fresh sumar 4460): menú de armas ~6700, vista previa ~7250,
# frase de ataque ~8260, frase del enemigo ~8850, resultado (資金/経験値) ~9570 (aprox.: medido con la secuencia anterior +170).
# ej: EMU_FLAGS="-interpreter -debugger" battle_prologue.sh build/x.cue emu/shots/b fresh BP_FROM=11000 BP_EXEC=0x80018CC4
set -euo pipefail
source "$(dirname "$0")/env.sh"
CUE="$(realpath "$1")"; OUT="$2"; MODE="${3:-state}"; shift 3 || shift $#
if [ "$MODE" = fresh ]; then
  # card virgen: crear archivo de sistema, título LOAD→LEFT→START, protagonista y pareja por defecto
  O=4460; EXTRA=(FRESH_CARD=1)
  I="2000:START;2800:START;3400:LEFT;3600:START;4200:CIRCLE;5000:DOWN;5200:DOWN;5400:CIRCLE;5700:CIRCLE;6100:DOWN;6300:CIRCLE;6600:CIRCLE;7000:START;"
else O=0; I=""; EXTRA=("LOAD_STATE=$SRW_WORK/emu/states/poc_prologue.sstate"); fi
# diálogo inicial (CIRCLE confirma; CROSS no avanza) → fase del jugador con el cursor en Excelion
# DLG_END: último CIRCLE del diálogo. Si sobra uno, abre el menú antes de tiempo y la ruta se corre
# (CROSS no sirve para corregirlo: sobre el mapa abre la ventana de info). Con el SNMSG inglés de la PoC el
# diálogo termina antes → 6240 en fresh.
DLG_END="${DLG_END:-$([ "$MODE" = fresh ] && echo 6240 || echo 6300)}"
for f in $(seq 4500 60 "$DLG_END"); do I="$I$((f + O)):CIRCLE;"; done
# 攻撃 → 4ª arma (光子魚雷, alcance 1-8) → R1 salta al objetivo → confirmar → vista previa → animación ON
# pasos espaciados ≥90 cuadros y pulsaciones de 8: con 60 el menú a veces ignora la confirmación
for p in 6500:CIRCLE 6590:DOWN 6680:CIRCLE 6800:DOWN 6860:DOWN 6920:DOWN 7010:CIRCLE 7130:R1 7250:CIRCLE 7430:CIRCLE 7610:CIRCLE; do
  I="$I$((${p%%:*} + O)):${p#*:}:8;"
done
cd "$SRW_WORK"
exec tools/drive.sh "$CUE" "$OUT" "${EXTRA[@]}" INPUTS="$I" SHOT_FRAMES="$(seq -s, $((7900 + O)) 60 $((9800 + O)))" LAST=$((9800 + O)) "$@"
