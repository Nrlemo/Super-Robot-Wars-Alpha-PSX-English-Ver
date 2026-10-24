#!/usr/bin/env bash
# Corre PCSX-Redux headless con tools/src/redux_drive.lua y convierte las capturas a PNG.
# Uso: drive.sh <imagen.cue> <dir_salida> [VAR=valor ...]   (INPUTS, INPUTS_FILE, SHOT_EVERY, SHOT_FRAMES, LAST, LOAD_STATE, SAVE_STATE,
#      DUMP_RAM, POKE="cuadro:0xADDR:ancho:valor;…", BP_READ, BP_WRITE, BP_EXEC, BP_FROM, LOG_FILE, COVER_FILE, FRESH_CARD=1, CARD=emu/states/x.mcd, EMU_FLAGS="-interpreter -debugger")
# ej:  drive.sh build/poc.cue emu/shots/t1 SHOT_EVERY=300 LAST=4800 INPUTS="2000:START;2600:CROSS"
set -euo pipefail
source "$(dirname "$0")/env.sh"
CUE="$(realpath "$1")"; OUT="$(realpath -m "$2")"; shift 2
# rutas relativas en INPUTS_FILE / LOAD_STATE → absolutas (más abajo se cambia de directorio)
args=(); for a in "$@"; do case "$a" in INPUTS_FILE=*|LOAD_STATE=*) a="${a%%=*}=$(realpath "${a#*=}")";; esac; args+=("$a"); done
set -- "${args[@]}"
mkdir -p "$OUT"
cd "$SRW_WORK/emu/pcsx-redux"
# FRESH_CARD=1 → memory card 1 virgen (plantilla emu/states/blank.mcd) para que la partida arranque igual siempre
if [[ " $* " == *" FRESH_CARD=1 "* ]]; then cp "$SRW_WORK/emu/states/blank.mcd" memcard1.mcd; fi
# CARD=<archivo.mcd> → usar esa memory card (copia; el original no se toca)
for a in "$@"; do [[ "$a" == CARD=* ]] && cp "$(realpath "$SRW_WORK/${a#CARD=}" 2>/dev/null || realpath "${a#CARD=}")" memcard1.mcd; done
# shellcheck disable=SC2086
emu_exec "$SRW_WORK/emu/pcsx-redux" "${TIMEOUT:-900}" SHOT_DIR="$OUT" "$@" -- \
  "$SRW_TOOLS/bin/PCSX-Redux-HEAD-x86_64.AppImage" -portable ${EMU_FLAGS:-} -iso "$CUE" -run -stdout -lua_stdout \
  -dofile "$SRW_TOOLS/src/redux_drive.lua" 2>&1 | grep -E "^\[f[0-9]+\] BP |error|Error" | grep -v "OpenGL" || true
# -interpreter/-debugger quedan persistidos en pcsx.json: volver al modo normal (dynarec, sin debug, audio mudo)
"$SRW_PY" - <<'PY'
import json
d = json.load(open('pcsx.json'))
d['emulator']['Dynarec'] = True
d['emulator']['Debug']['Debug'] = False
d['SPU']['Mute'], d['SPU']['Volume'] = True, 0
json.dump(d, open('pcsx.json', 'w'), indent=2)
PY
"$SRW_PY" "$SRW_TOOLS/src/raw2png.py" "$OUT" | tail -1
