#!/usr/bin/env bash
# Pipeline de build completo (todas las fuentes en inglés → ISO verificada). Ver notes/pipeline_build.md.
# Uso: build.sh [opciones de build_all.py]     ej.: build.sh --list · build.sh --selftest · build.sh --null
set -euo pipefail
source "$(dirname "$0")/env.sh" 2>/dev/null
PY="${SRW_PY:-}"; [ -x "$PY" ] || PY=python3   # sin el venv (nube): alcanza para --list, --dry-run y --only validate
exec "$PY" "$SRW_TOOLS/src/build_all.py" "$@"
