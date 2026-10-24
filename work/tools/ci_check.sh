#!/usr/bin/env bash
# Controles que no necesitan la ISO: los corre GitHub Actions (.github/workflows/check.yml) en cada push a main y en
# cada PR, y se pueden correr igual en server1, la desktop o una sesión de la nube antes de subir.
# Uso: ci_check.sh [paso ...]        (sin pasos: todos, en este orden)
#   guard      ninguna imagen de disco, BIOS, EXE del juego ni save state versionado (CLAUDE.md §5.4)
#   syntax     sintaxis de todos los .py de tools/src y de todos los .sh versionados
#   csv        csv_lint.py: columnas corridas, (category, jp) repetido, en_final vacío, cp932
#   tests      test_check_text + test_build_all (con numpy/Pillow/pycdlib no se saltea ninguno)
#   validate   build_all.py --dry-run: check_text.py sobre todos los volcados + DC/DR, menus_en al día con menus_map
#   lotes      lote.py validar sobre cada lote de traduccion/lotes/ (#24)
#   generated  regenera glosario, nombres de piloto, DC/DR, menús y referencias: si algo cambia, falta commitearlo
#              (va al final: los anteriores validan lo commiteado, no lo regenerado)
#   nogamedata (kit de traducción, #288) ningún .jsonl versionado tiene "jp"/"chs" (kit.py check-stripped)
#   dedication (kit) la pantalla de dedicatoria no cambió (kit.py dedication; requisito 2 de TRANSLATING.md)
# En el kit no hay info/ (el glosario no se regenera: glossary.csv es la fuente) ni lotes versionados.
# Intérprete: $PY, o el venv de server1 (work/.venv) si existe, o python3. Sale con 1 si falla algún paso.
set -uo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT" || exit 2
PY=${PY:-$([ -x work/.venv/bin/python ] && echo "$ROOT/work/.venv/bin/python" || echo python3)}
LOGS=work/logs/ci; mkdir -p "$LOGS"
# salidas de los generadores (paso generated)
GEN_PATHS=(work/glossary work/dump/pilot.jsonl work/translation traduccion/referencia)

summary() { [ -n "${GITHUB_STEP_SUMMARY:-}" ] && printf '%s\n' "$@" >> "$GITHUB_STEP_SUMMARY"; return 0; }

step_guard() {
  local bad
  bad=$(git ls-files | grep -iE '\.(bin|cue|img|iso|chd|pbp|ecm|mdf|ccd|sub|sstate|ppf|xdelta)$|(^|/)(bios/|scph[^/]*$)|(^|/)SLPS_[0-9]|^work/iso_(jp|chs)/' || true)
  if [ -n "$bad" ]; then
    echo "Archivos que no se versionan (ISO, BIOS, EXE del juego, save states, parches de imagen):"; echo "$bad"; return 1
  fi
  echo "ok: $(git ls-files | wc -l) archivos versionados, ninguno prohibido"
}

step_syntax() {
  local rc=0 f
  "$PY" -m compileall -q work/tools/src > "$LOGS/compileall.log" || { cat "$LOGS/compileall.log"; rc=1; }
  while IFS= read -r f; do bash -n "$f" || rc=1; done < <(git ls-files '*.sh')
  [ $rc = 0 ] && echo "ok: $(git ls-files 'work/tools/src/*.py' | wc -l) .py y $(git ls-files '*.sh' | wc -l) .sh"
  return $rc
}

step_csv() { "$PY" work/tools/src/csv_lint.py; }

step_tests() { (cd work/tools/src && "$PY" -m unittest test_check_text test_build_all test_script_bin test_mdata_bin); }

step_generated() {
  local before after g
  before=$(git status --porcelain -uall -- "${GEN_PATHS[@]}"; git diff -- "${GEN_PATHS[@]}" | sha1sum)
  local gens=("pilot_bin.py fill" "dict_build.py dc dr" "menus_draft.py" "traduccion_ref.py")
  [ -d info ] && gens=("glossary_build.py" "${gens[@]}")    # kit: sin info/ el glosario es fuente, no se regenera
  for g in "${gens[@]}"; do
    # shellcheck disable=SC2086
    "$PY" work/tools/src/$g > "$LOGS/gen_${g%%.py*}.log" 2>&1 || { echo "falló $g:"; tail -20 "$LOGS/gen_${g%%.py*}.log"; return 1; }
  done
  after=$(git status --porcelain -uall -- "${GEN_PATHS[@]}"; git diff -- "${GEN_PATHS[@]}" | sha1sum)
  if [ "$before" != "$after" ]; then
    echo "Los generadores cambiaron archivos versionados: correr este paso localmente y commitear el resultado."
    git status --short -- "${GEN_PATHS[@]}"; git --no-pager diff --stat -- "${GEN_PATHS[@]}"; return 1
  fi
  echo "ok: glosario, nombres de piloto, DC/DR, menús y referencias al día con sus fuentes"
}

step_validate() {
  local rc=0
  "$PY" work/tools/src/build_all.py --dry-run --name ci --overwrite > "$LOGS/build_dry_run.log" 2>&1 || rc=1
  grep -E '^\[ *[0-9]+/[0-9]+\] (preflight|validate) ' "$LOGS/build_dry_run.log" | cut -c1-400
  [ $rc = 0 ] || { echo "falló build_all.py --dry-run (log: $LOGS/build_dry_run.log)"; tail -20 "$LOGS/build_dry_run.log"; }
  # shellcheck disable=SC2016  # las comillas invertidas son Markdown, no una expansión
  summary '### Traducción (`lote.py estado`)' '```' "$($PY work/tools/src/lote.py estado)" '```'
  return $rc
}

step_lotes() {
  local rc=0 n=0 f
  [ -d traduccion/lotes ] || { echo "sin lotes en traduccion/lotes/"; return 0; }
  while IFS= read -r f; do n=$((n + 1)); "$PY" work/tools/src/lote.py validar "$f" || rc=1; done \
    < <(find traduccion/lotes -mindepth 2 -type f -name '*.jsonl' | sort)
  [ $n = 0 ] && echo "sin lotes en traduccion/lotes/"
  return $rc
}

step_nogamedata() {
  grep -qs 'filter=srwjp' .gitattributes || { echo "sin filtro srwjp (repo de desarrollo): nada que controlar"; return 0; }
  "$PY" work/tools/src/kit.py check-stripped
}

step_dedication() {
  [ -f work/tools/kit/dedication.sha256 ] || { echo "sin work/tools/kit/dedication.sha256 (repo de desarrollo)"; return 0; }
  "$PY" work/tools/src/kit.py dedication
}

STEPS=("$@"); [ ${#STEPS[@]} -gt 0 ] || STEPS=(guard syntax csv nogamedata dedication tests validate lotes generated)
fail=()
for s in "${STEPS[@]}"; do
  declare -F "step_$s" > /dev/null || { echo "paso desconocido: $s"; exit 2; }
  echo "== $s"
  "step_$s" || fail+=("$s")
done
if [ ${#fail[@]} -gt 0 ]; then echo "FALLARON: ${fail[*]}"; exit 1; fi
echo "todo OK (${STEPS[*]})"
