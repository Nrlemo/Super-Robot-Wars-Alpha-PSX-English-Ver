#!/usr/bin/env bash
# Kit de traducción (#288): deja un fork recién clonado listo para armar la ISO. Ver docs/TRANSLATION_GUIDE.md §4.
# Los mensajes van en inglés: lo corre gente de afuera del proyecto.
# Uso: work/tools/kit_setup.sh [--tools] [--no-null]
#   --tools    compila armips y mkpsxiso/dumpsxiso (versiones fijas) en work/tools/src_ext → work/tools/bin
#   --no-null  no hacer la build de control (--null, ~1 min)
# Disco: "Super Robot Taisen Alpha (Japan) (v1.0).bin/.cue" en la raíz del repo, o SRW_JP_CUE=/ruta/al/archivo.cue
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"
mkdir -p work/logs
TOOLS=0; NULL=1
for a in "$@"; do
  case "$a" in
    --tools) TOOLS=1 ;;
    --no-null) NULL=0 ;;
    *) sed -n '4,7p' "$0"; exit 2 ;;
  esac
done
JP_SHA1=cfce3c7a76f64269387fbb7b77e3bcfe41b723c6     # Redump, single track, 646.374.288 bytes
ARMIPS_REV=62adab4ef30da765f5cf22a451eb08a59c54dc8b   # la que usa el proyecto (v0.11.0)
MKPSXISO_TAG=v2.30
BIN=work/tools/bin; EXT=work/tools/src_ext
step() { printf '\n== %s\n' "$*"; }
die() { printf 'ERROR: %s\n' "$*" >&2; exit 1; }
sha1() { if command -v sha1sum >/dev/null; then sha1sum "$1" | cut -d' ' -f1; else shasum -a 1 "$1" | cut -d' ' -f1; fi; }

step "1/7 Prerequisites"
miss=()
for c in python3 git; do command -v "$c" >/dev/null || miss+=("$c"); done
[ $TOOLS = 1 ] && for c in cmake g++; do command -v "$c" >/dev/null || miss+=("$c"); done
[ ${#miss[@]} = 0 ] || die "missing commands: ${miss[*]} (Debian/Ubuntu: sudo apt install python3 python3-venv git cmake g++ xdelta3 fonts-dejavu-core fonts-dejavu-extra fonts-liberation)"
python3 -c 'import sys; sys.exit(sys.version_info < (3, 12))' || die "Python 3.12 or newer needed (3.14 is the tested version)"
command -v xdelta3 >/dev/null || echo "note: xdelta3 is not installed; you only need it to make a release patch (--release)"
git rev-parse --is-inside-work-tree >/dev/null 2>&1 || die "run this inside your git clone of the kit"

step "2/7 Python environment (work/.venv)"
[ -x work/.venv/bin/python ] || python3 -m venv work/.venv || die "could not create the venv (Debian/Ubuntu: sudo apt install python3-venv)"
work/.venv/bin/python -m pip install -q --upgrade pip
work/.venv/bin/python -m pip install -q -r work/tools/requirements.txt
PY=work/.venv/bin/python
echo "ok: $($PY --version)"

step "3/7 External tools (work/tools/bin: armips, mkpsxiso, dumpsxiso)"
mkdir -p "$BIN" "$EXT"
if [ $TOOLS = 1 ]; then
  if [ ! -x "$BIN/armips" ]; then
    [ -d "$EXT/armips/.git" ] || git clone -q https://github.com/Kingcom/armips "$EXT/armips"
    git -C "$EXT/armips" checkout -q "$ARMIPS_REV" && git -C "$EXT/armips" submodule update -q --init --recursive
    cmake -S "$EXT/armips" -B "$EXT/armips/build" -DCMAKE_BUILD_TYPE=Release > work/logs/kit_armips.log 2>&1 \
      && cmake --build "$EXT/armips/build" -j >> work/logs/kit_armips.log 2>&1 || die "armips build failed (work/logs/kit_armips.log)"
    cp "$EXT/armips/build/armips" "$BIN/armips"
  fi
  if [ ! -x "$BIN/mkpsxiso" ] || [ ! -x "$BIN/dumpsxiso" ]; then
    [ -d "$EXT/mkpsxiso/.git" ] || git clone -q https://github.com/Lameguy64/mkpsxiso "$EXT/mkpsxiso"
    git -C "$EXT/mkpsxiso" checkout -q "$MKPSXISO_TAG" && git -C "$EXT/mkpsxiso" submodule update -q --init --recursive
    cmake -S "$EXT/mkpsxiso" -B "$EXT/mkpsxiso/build" -DCMAKE_BUILD_TYPE=Release > work/logs/kit_mkpsxiso.log 2>&1 \
      && cmake --build "$EXT/mkpsxiso/build" -j >> work/logs/kit_mkpsxiso.log 2>&1 || die "mkpsxiso build failed (work/logs/kit_mkpsxiso.log)"
    cp "$EXT/mkpsxiso/build/mkpsxiso" "$EXT/mkpsxiso/build/dumpsxiso" "$BIN/"
  fi
fi
for t in armips mkpsxiso dumpsxiso; do
  [ -x "$BIN/$t" ] || die "missing $BIN/$t: run again with --tools (needs cmake and g++), or copy your own build there"
done
echo "ok: armips, mkpsxiso, dumpsxiso"

step "4/7 Original disc (your own dump)"
CUE="${SRW_JP_CUE:-$ROOT/Super Robot Taisen Alpha (Japan) (v1.0).cue}"
DISC="${CUE%.cue}.bin"
[ -f "$CUE" ] && [ -f "$DISC" ] || die "put 'Super Robot Taisen Alpha (Japan) (v1.0).bin' and '.cue' in $ROOT, or export SRW_JP_CUE=/path/to/your.cue (the .bin must have the same name)"
got=$(sha1 "$DISC")
[ "$got" = "$JP_SHA1" ] || die "$DISC has SHA-1 $got; the kit needs the Redump image Super Robot Taisen Alpha (Japan) (v1.0), SLPS-02636, SHA-1 $JP_SHA1"
echo "ok: $DISC"

step "5/7 Extract the disc (work/iso_jp)"
if [ ! -f work/iso_jp/layout.xml ]; then
  "$BIN/dumpsxiso" -q -x work/iso_jp -s work/iso_jp/layout.xml "$CUE" > work/logs/kit_dumpsxiso.log 2>&1 \
    || die "dumpsxiso failed (work/logs/kit_dumpsxiso.log)"
fi
n=$(grep -c '<file' work/iso_jp/layout.xml)
[ "$n" = 104 ] && [ -f work/iso_jp/license_data.dat ] || die "work/iso_jp looks wrong ($n files in layout.xml, expected 104): delete it and run again"
echo "ok: 104 files"

step "6/7 Japanese text from your disc + generated files (kit.py restore)"
"$PY" work/tools/src/kit.py restore
"$PY" work/tools/src/gfx_render.py render > work/logs/kit_gfx_render.log 2>&1 || die "gfx_render.py failed (work/logs/kit_gfx_render.log)"
"$PY" work/tools/src/gfx_entrega.py check work/gfx/render/out > work/logs/kit_gfx_check.log 2>&1 \
  || die "gfx_entrega.py check failed (work/logs/kit_gfx_check.log)"
echo "ok: text graphics rendered in work/gfx/render/out"

step "7/7 Toolchain check"
if [ $NULL = 1 ]; then
  SRW_JP_CUE="$CUE" work/tools/build.sh --null --name kit_null > work/logs/kit_null.log 2>&1 \
    || die "build.sh --null failed: the rebuilt disc is not identical to yours (work/logs/kit_null.log)"
  rm -rf work/build/kit_null_v*
  echo "ok: an untouched rebuild is byte-identical to the original"
fi
SRW_JP_CUE="$CUE" work/tools/build.sh --dry-run > work/logs/kit_dry_run.log 2>&1 || die "build.sh --dry-run failed (work/logs/kit_dry_run.log)"
grep -E '^\[ *[0-9]+/[0-9]+\] validate' work/logs/kit_dry_run.log | cut -c1-160

printf '\nReady. Next steps (docs/TRANSLATION_GUIDE.md):\n'
printf '  work/tools/build.sh --selftest --name first     # your first build: the English game\n'
printf '  work/.venv/bin/python work/tools/src/kit.py pivot   # start your language (keeps the English as en_ref)\n'
