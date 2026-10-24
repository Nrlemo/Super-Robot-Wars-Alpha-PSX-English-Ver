#!/usr/bin/env bash
# Medición de ventanas (#31). bx: BXCLIST con todas las frases = texto de medición (mk_ancho_bxclist.py) sobre los
# archivos de una build (FILES=build/<N>/files; por defecto la última) → ruta cp04 de names_test.sh (Amuro ataca).
# La caja de escenas se mide con `formato_test.sh ancho`.
# Uso: ancho_test.sh bx dir_salida [n1,n2,…]    (n = dígitos por renglón, r = espacios 0x20, s = espacios 0xA0)
set -euo pipefail
source "$(dirname "$0")/env.sh"
V=$1; OUT=$(realpath -m "$2"); SPEC=${3:-30,34,r,s}
cd "$SRW_WORK"
B=${FILES:-$(ls -td build/*/files | head -1)}
T=build/ancho_$V; mkdir -p "$T"
"$SRW_PY" tools/src/mk_ancho_bxclist.py "$T/BXCLIST.BIN" "$SPEC" | tail -1
rep=(); while IFS= read -r f; do rep+=("${f#"$B"/}=$f"); done < <(find "$B" -type f ! -name BXCLIST.BIN)
for f in "$B"/../menus/*_GRP.BIN; do rep+=("OVL/$(basename "$f")=$f"); done
"$SRW_PY" tools/src/build_iso.py "$T/ancho_$V.bin" "${rep[@]}" BATTLE/BXCLIST.BIN="$T/BXCLIST.BIN" | tail -1
tools/names_test.sh "$T/ancho_$V.cue" "$OUT" cp04
