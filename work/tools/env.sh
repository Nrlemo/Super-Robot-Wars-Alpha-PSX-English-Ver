# Rutas del entorno de trabajo. Uso: source work/tools/env.sh
export SRW_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")/../.." && pwd)"
export SRW_WORK="$SRW_ROOT/work"
export SRW_TOOLS="$SRW_WORK/tools"
export SRW_JP_CUE="${SRW_JP_CUE:-$SRW_ROOT/Super Robot Taisen Alpha (Japan) (v1.0).cue}"   # o la ruta que ya traiga el entorno
export SRW_BIOS_DIR="$SRW_ROOT/Bios"
export SRW_BIOS="$SRW_BIOS_DIR/scph100.bin"   # SCPH-100 v4.3 NTSC-J
export SRW_PY="$SRW_WORK/.venv/bin/python"
export SRW_JDK="$(ls -d "$SRW_TOOLS"/jdk-21* | head -1)"
export WINEDEBUG=-all
export PATH="$SRW_TOOLS/bin:$PATH"
# armips: binario nativo si existe (compilado en tools/src_ext/armips), si no la build de Windows vía wine
armips() {
  if [ -f "$SRW_TOOLS/bin/armips" ] && [ -x "$SRW_TOOLS/bin/armips" ]; then "$SRW_TOOLS/bin/armips" "$@"
  else wine "$SRW_TOOLS/bin/armips/armips.exe" "$@"; fi
}

# POKE de las pruebas CP04: potencia 30000 en las 9 armas del ν Gundam HWS (0x28 por arma, potencia en +4).
# El registro está en el heap, debajo de la tabla de objetos de texto: con el EXE original en 0x801417D8 y se corre
# 0x1C bytes hacia abajo por cada objeto de más (TEXT_OBJS de patches/vwf.asm, #57; con 0x500 queda en 0x8013DFD8).
hws_poke() {
  local objs base k out=""
  objs=$(sed -n 's/^TEXT_OBJS equ \(0x[0-9A-Fa-f]*\).*/\1/p' "$SRW_WORK/patches/vwf.asm"); objs=${objs:-0x300}
  base=$((0x801417dc - (objs - 0x300) * 0x1c))
  for k in 0 1 2 3 4 5 6 7 8; do out+=$(printf '3600:0x%08x:2:30000;' $((base + k * 0x28))); done
  echo "$out"
}

# Máquina sin monitor (server1): sin DISPLAY se usa Xvfb del sistema (xvfb-run); si no está,
# el contenedor srw-emu (tools/docker/Dockerfile). emu_mode imprime "native", "xvfb" o "docker".
emu_mode() {
  if [ -n "${DISPLAY:-}" ]; then echo native
  elif command -v xvfb-run >/dev/null; then echo xvfb
  elif command -v docker >/dev/null && docker image inspect srw-emu >/dev/null 2>&1; then echo docker
  else echo "sin DISPLAY y sin imagen srw-emu: docker build -t srw-emu work/tools/docker" >&2; return 1; fi
}

# emu_exec DIR_TRABAJO TIMEOUT [VAR=valor ...] -- COMANDO [args...]
# Ejecuta el comando del emulador con pantalla: nativa o Xvfb dentro de srw-emu.
emu_exec() {
  local wd="$1" to="$2"; shift 2
  local vars=()
  while [ "$1" != "--" ]; do vars+=("$1"); shift; done; shift
  local mode; mode="$(emu_mode)" || return 1
  if [ "$mode" = native ]; then
    (cd "$wd" && env "${vars[@]}" timeout "$to" "$@")
  elif [ "$mode" = xvfb ]; then
    (cd "$wd" && env "${vars[@]}" timeout "$to" xvfb-run -a -s "-screen 0 1280x1024x24" "$@")
  else
    local dargs=(-e HOME=/tmp -e XDG_RUNTIME_DIR=/tmp -e LIBGL_ALWAYS_SOFTWARE=1 -v "$SRW_ROOT:$SRW_ROOT" -w "$wd")
    local v val d
    for v in "${vars[@]}"; do
      dargs+=(-e "$v"); val="${v#*=}"
      case "$val" in /*)            # montar rutas absolutas fuera del proyecto (logs, capturas, estados)
        if [ -d "$val" ]; then d="$val"; else d="$(dirname "$val")"; fi
        case "$d" in /|/tmp|"$SRW_ROOT"|"$SRW_ROOT"/*) ;; *) [ -e "$d" ] && dargs+=(-v "$d:$d");; esac;;
      esac
    done
    # AppImage → versión extraída (en el contenedor no hay FUSE)
    [ "$1" = "$SRW_TOOLS/bin/PCSX-Redux-HEAD-x86_64.AppImage" ] && [ -x "$SRW_TOOLS/bin/pcsx-redux/AppRun" ] && set -- "$SRW_TOOLS/bin/pcsx-redux/AppRun" "${@:2}"
    docker run --rm -u "$(id -u):$(id -g)" "${dargs[@]}" srw-emu timeout "$to" sh -c \
      'Xvfb :99 -screen 0 1280x1024x24 -nolisten tcp >/dev/null 2>&1 & sleep 2; DISPLAY=:99 exec "$@"' sh "$@"
  fi
}
