#!/usr/bin/env bash
# Un trabajo de traducción: saca el lote (si no existe), lo traduce con Gemini y valida. No hace git.
# Uso: gemini_job.sh FORMATO SPEC     SPEC = "1-3" (rango) o "--bloque 7" (snmsg)
# Variables: GEMINI_API_KEY, GEMINI_MODEL (opc.), GEMINI_CHUNK (opc.). Imprime LOTE=<ruta> al final.
set -euo pipefail
cd "$(dirname "$0")/../.."
fmt="$1"; spec="$2"
lote=$(python3 work/tools/src/lote.py sacar "$fmt" $spec --reusar | sed -n 's/^LOTE=//p' | head -1)
[ -n "$lote" ] || { echo "no se pudo sacar el lote" >&2; exit 1; }
mkdir -p work/logs
python3 work/tools/src/gemini_translate.py "$lote" --chunk "${GEMINI_CHUNK:-40}" ${GEMINI_EXTRA:-} 2>&1 | tee "work/logs/gemini_$(basename "$lote" .jsonl).log" | tail -n 20
python3 work/tools/src/lote.py validar "$lote" | tail -n 20 || true
echo "LOTE=$lote"
