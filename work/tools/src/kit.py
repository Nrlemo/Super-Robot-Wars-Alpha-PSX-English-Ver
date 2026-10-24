"""Kit de traducción público (#288): las herramientas y las fuentes de la traducción SIN datos del juego.

El kit vive en el repo público (Nrlemo/Super-Robot-Wars-Alpha-PSX-English-Ver) para que cualquiera haga un fork y
traduzca a su idioma (docs/TRANSLATION_GUIDE.md). Los 6 volcados de diálogo van sin "jp" ni "chs": cada fila guarda
sus claves y solo los campos que difieren de un volcado fresco del disco original. En el fork, `restore` vuelve a
sacar el japonés del disco propio del traductor y lo junta por clave; el filtro de git `srwjp` (clean/smudge) hace
que git guarde siempre la fila sin japonés y el disco la tenga completa, así todas las herramientas siguen igual.

Uso (desde la raíz del repo; los mensajes del lado del fork van en inglés: los lee gente de afuera):
  kit.py export <dir> [--dry-run]   (repo de desarrollo) copia a <dir> (checkout del repo público) lo que permite
                                    work/tools/kit/manifest.txt; nunca toca README.md, screenshots/ ni FUNDING.yml
  kit.py restore                    (fork) japonés desde work/iso_jp → work/dump/*.jsonl, volcados que son solo datos
                                    del juego, archivos generados y el filtro de git
  kit.py clean <ruta> | smudge <ruta>   filtro de git (stdin → stdout); lo configura `restore`
  kit.py pivot [--only snmsg,script]  (fork que traduce desde el inglés) en → en_ref y en vacío; el juego usa
                                    en → en_ref → jp, así sigue jugable en inglés hasta traducir cada fila
  kit.py refresh-ref <ref>          (fork) trae las correcciones del inglés de upstream (p. ej. upstream/main) a en_ref
                                    y lista las filas ya traducidas cuyo inglés cambió (para revisarlas)
  kit.py check-stripped             falla si algún .jsonl versionado (índice de git) tiene "jp" o "chs" (CI del kit)
  kit.py dedication                 la pantalla de dedicatoria no cambió (requisito 2 del kit; CI del kit)
"""
import argparse
import fnmatch
import hashlib
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

SRC = Path(__file__).resolve().parent             # work/tools/src
WORK = SRC.parent.parent                          # work
ROOT = WORK.parent
ISO_JP = WORK / 'iso_jp'
DUMP = WORK / 'dump'
KIT = WORK / 'tools' / 'kit'                      # configuración del export (solo en el repo de desarrollo)
ORIG = WORK / '.kit' / 'orig'                     # (fork) volcados frescos del disco original, no versionados
LOGS = WORK / 'logs' / 'kit'

# volcados de diálogo que se versionan sin japonés: formato → claves de fila (las de check_text.py)
DIALOG = {'snmsg': ('id',), 'script': ('script', 'inst'), 'bxclist': ('pilot', 'idx'), 'deadmess': ('slot',),
          'em': ('rec',), 'mdata': ('file', 'off')}
DROP = {'jp', 'chs'}                              # nunca van al kit (texto del juego / del parche chino)
GONE = '_sin'                                     # campos del volcado fresco que la fila no tiene
# (fork) volcados que son solo datos del juego y archivos generados, en orden de dependencia
REGEN = (['pilot_bin.py', 'dump'], ['pilot_bin.py', 'fill'], ['robot_raf.py', '--json', str(DUMP / 'robot.jsonl')],
         ['option_dict.py', 'dump'], ['ovl_strings.py'], ['sndata.py', 'map'], ['dict_build.py', 'dc', 'dr'],
         ['menus_draft.py'], ['traduccion_ref.py'], ['end_credits.py'])
DEDICATION = ('work/tools/src/dedicatoria.py', 'work/patches/dedicatoria.asm')
DEDICATION_SUM = 'work/tools/kit/dedication.sha256'
PROTECTED = ('README.md', 'screenshots/', '.github/FUNDING.yml')   # del repo público: el export no los toca
EXPORTED = 'work/tools/kit/EXPORTED.txt'          # lista de lo exportado (para borrar lo que deja de exportarse)
# lo mismo que el paso guard de ci_check.sh
FORBIDDEN = re.compile(r'\.(bin|cue|img|iso|chd|pbp|ecm|mdf|ccd|sub|sstate|ppf|xdelta)$|(^|/)(bios/|scph[^/]*$)|'
                       r'(^|/)SLPS_[0-9]|^work/iso_(jp|chs)/', re.I)
JAPANESE = re.compile(r'[぀-ヿ㐀-鿿ｦ-ﾟ]')


# ───────────────────────────── Filas ─────────────────────────────
def read_rows(text: str) -> list[dict]:
    return [json.loads(line) for line in text.splitlines() if line.strip()]


def write_rows(rows: list[dict]) -> str:
    return ''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in rows)


def _aligned(fmt, rows, fresh):
    keys = DIALOG[fmt]
    if len(rows) != len(fresh):
        sys.exit(f'{fmt}: {len(rows)} rows but a fresh dump of the disc has {len(fresh)}: tools of another version? '
                 'Run kit.py restore')
    for r, f in zip(rows, fresh):
        if any(r.get(k) != f[k] for k in keys):
            sys.exit(f'{fmt}: row {[r.get(k) for k in keys]} does not match the fresh dump '
                     f'{[f[k] for k in keys]}: tools of another version? Run kit.py restore')
    return zip(rows, fresh)


def strip(fmt: str, rows: list[dict], fresh: list[dict]) -> list[dict]:
    """Fila completa → fila del kit: claves + campos que difieren del volcado fresco (sin jp/chs)."""
    keys, out = DIALOG[fmt], []
    for r, f in _aligned(fmt, rows, fresh):
        o = {k: r[k] for k in keys}
        o.update({c: v for c, v in r.items() if c not in keys and c not in DROP and (c not in f or f[c] != v)})
        gone = [c for c in f if c not in r and c not in DROP]
        if gone:
            o[GONE] = gone
        out.append(o)
    return out


def overlay(fmt: str, rows: list[dict], fresh: list[dict]) -> list[dict]:
    """Fila del kit (o completa) + volcado fresco → fila completa, con el japonés del disco."""
    out = []
    for o, f in _aligned(fmt, rows, fresh):
        r = dict(f)
        for c in o.get(GONE, ()):
            r.pop(c, None)
        r.update({c: v for c, v in o.items() if c != GONE and (c not in DROP or c not in f)})
        out.append(r)
    return out


def fresh_dumps(out: Path) -> dict[str, list[dict]]:
    """Volcados de diálogo sacados de work/iso_jp (sin el parche chino: "chs" vacío)."""
    if not (ISO_JP / 'SNMAP' / 'SNMSG.BIN').exists():
        sys.exit(f'missing {ISO_JP}: extract your original disc first (work/tools/kit_setup.sh)')
    out.mkdir(parents=True, exist_ok=True)
    py = sys.executable
    for cmd in ([py, SRC / 'snmsg.py', 'dump', ISO_JP / 'SNMAP' / 'SNMSG.BIN', '-', out / 'snmsg.jsonl'],
                [py, SRC / 'script_bin.py', 'dump', out / 'script.jsonl'],
                [py, SRC / 'bxclist.py', 'dump', out / 'bxclist.jsonl'],
                [py, SRC / 'deadmess_em.py', 'dump', out],
                [py, SRC / 'mdata_bin.py', 'dump', out / 'mdata.jsonl']):
        run(cmd, 'dump_' + Path(cmd[1]).stem)
    return {fmt: read_rows((out / f'{fmt}.jsonl').read_text(encoding='utf-8')) for fmt in DIALOG}


def run(cmd, name):
    LOGS.mkdir(parents=True, exist_ok=True)
    log = LOGS / f'{name}.log'
    with open(log, 'w', encoding='utf-8') as f:
        rc = subprocess.run([str(c) for c in cmd], cwd=ROOT, stdout=f, stderr=subprocess.STDOUT).returncode
    if rc:
        sys.exit(f'{name} failed (log: {log.relative_to(ROOT)}):\n' + ''.join(log.read_text().splitlines(True)[-15:]))


def git(*args, check=True) -> str:
    return subprocess.run(['git', *args], cwd=ROOT, capture_output=True, text=True, check=check).stdout


# ───────────────────────────── Export (repo de desarrollo) ─────────────────────────────
def manifest_rules() -> list[tuple[bool, str]]:
    rules = []
    for line in (KIT / 'manifest.txt').read_text(encoding='utf-8').splitlines():
        line = line.split('#', 1)[0].strip()
        if line:
            sign, pat = line[0], line[1:].strip()
            assert sign in '+-', f'manifest.txt: cada regla empieza con + o -: {line!r}'
            rules.append((sign == '+', pat))
    return rules


def selected() -> list[str]:
    rules = manifest_rules()
    out = []
    for path in git('ls-files', '-z').split('\0'):
        keep = False
        for inc, pat in rules:          # gana la última regla que coincide (como .gitignore)
            if fnmatch.fnmatchcase(path, pat):
                keep = inc
        if path and keep and (ROOT / path).is_file():
            out.append(path)
    return out


def kit_files() -> dict[str, bytes]:
    """Archivos propios del kit: work/tools/kit/files/** tal cual + .gitignore (el del repo + gitignore.extra)."""
    out = {str(p.relative_to(KIT / 'files')): p.read_bytes() for p in sorted((KIT / 'files').rglob('*')) if p.is_file()}
    out['.gitignore'] = (ROOT / '.gitignore').read_bytes() + b'\n' + (KIT / 'gitignore.extra').read_bytes()
    out[DEDICATION_SUM] = dedication_sums().encode()
    return out


def leak_report(stripped: dict[str, list[dict]]) -> list[str]:
    """Campos conservados (fuera de en/en_ref) que todavía tienen japonés: para revisar a mano."""
    lines = []
    for fmt, rows in stripped.items():
        hits = {}
        for r in rows:
            for c, v in r.items():
                if c not in ('en', 'en_ref') and isinstance(v, str) and JAPANESE.search(v):
                    hits.setdefault(c, []).append(v)
        for c, vs in hits.items():
            lines.append(f'  {fmt}.{c}: {len(vs)} filas con japonés, p. ej. {vs[:3]}')
    return lines


def export(dest: Path, dry_run: bool):
    files = selected()
    prot = [f for f in files if f.startswith(PROTECTED)]
    bad = [f for f in files if FORBIDDEN.search(f)]
    if prot or bad:
        sys.exit(f'manifest.txt deja pasar archivos prohibidos o del repo público: {prot + bad}')
    dirty = git('status', '--porcelain', '--', *files)
    if dirty:
        print(f'AVISO: {len(dirty.splitlines())} archivos exportados con cambios sin commitear')
    dumps = {f'work/dump/{fmt}.jsonl': fmt for fmt in DIALOG}
    missing = [p for p in dumps if p not in files]
    if missing:
        sys.exit(f'manifest.txt no incluye los volcados de diálogo {missing}')
    with tempfile.TemporaryDirectory() as tmp:
        fresh = fresh_dumps(Path(tmp))
    stripped = {fmt: strip(fmt, read_rows((ROOT / p).read_text(encoding='utf-8')), fresh[fmt])
                for p, fmt in dumps.items()}
    content = {f: (write_rows(stripped[dumps[f]]).encode() if f in dumps else None) for f in files}
    extra = kit_files()
    if any(r.keys() & DROP for rows in stripped.values() for r in rows):
        sys.exit('ERROR: quedó "jp" o "chs" en un volcado del kit')
    def size(f):
        if f in extra:
            return len(extra[f])
        return len(content[f]) if content[f] is not None else (ROOT / f).stat().st_size
    by_dir = {}
    for f in [*files, *extra]:
        top = f.split('/')[0] if f.count('/') < 2 else '/'.join(f.split('/')[:2])
        n, b = by_dir.get(top, (0, 0))
        by_dir[top] = (n + 1, b + size(f))
    print(f'kit: {len(files)} archivos del repo + {len(extra)} propios del kit')
    for top, (n, b) in sorted(by_dir.items()):
        print(f'  {top:32} {n:5} archivos  {b / 2**20:7.2f} MiB')
    report = leak_report(stripped)
    print('Campos conservados con japonés (revisar):' if report else 'Ningún campo conservado tiene japonés.')
    print('\n'.join(report))
    if dry_run:
        return
    if not (dest / '.git').exists():
        sys.exit(f'{dest} no es un checkout de git (clonar el repo público ahí)')
    prev = (dest / EXPORTED).read_text().split('\n') if (dest / EXPORTED).exists() else []
    now = sorted({*files, *extra, EXPORTED})
    for f in set(prev) - set(now):
        if f and not f.startswith(PROTECTED) and (dest / f).is_file():
            (dest / f).unlink()
            print('borrado (ya no se exporta):', f)
    for f in files:
        (dest / f).parent.mkdir(parents=True, exist_ok=True)
        if content[f] is not None:
            (dest / f).write_bytes(content[f])
        else:
            shutil.copy2(ROOT / f, dest / f)
    for f, data in extra.items():
        (dest / f).parent.mkdir(parents=True, exist_ok=True)
        (dest / f).write_bytes(data)
    (dest / EXPORTED).write_text('\n'.join(now) + '\n')
    print(f'→ {dest} (revisar con git -C {dest} status antes de commitear)')


# ───────────────────────────── Fork ─────────────────────────────
def restore():
    fresh = fresh_dumps(ORIG)
    attrs = ROOT / '.gitattributes'
    use_git = attrs.exists() and 'filter=srwjp' in attrs.read_text() and (ROOT / '.git').exists()
    if use_git:
        me = 'python3 work/tools/src/kit.py'
        git('config', 'filter.srwjp.clean', f'{me} clean %f')
        git('config', 'filter.srwjp.smudge', f'{me} smudge %f')
        git('config', 'filter.srwjp.required', 'true')
        print('git filter srwjp configured (git stores the dumps without the Japanese text)')
    for fmt in DIALOG:
        p = DUMP / f'{fmt}.jsonl'
        rows = read_rows(p.read_text(encoding='utf-8'))
        if any('jp' in r for r in rows):              # ya completo (p. ej. segunda corrida): se normaliza igual
            rows = strip(fmt, rows, fresh[fmt])
        p.write_text(write_rows(overlay(fmt, rows, fresh[fmt])), encoding='utf-8')
        print(f'{p.relative_to(ROOT)}: {len(rows)} rows, Japanese restored from your disc')
        # git da por modificado un archivo cuyo tamaño cambió sin pasarlo por el filtro: si la versión sin japonés es
        # la del índice (no hay cambios del traductor), se refresca la entrada; si los hay, quedan sin tocar
        rel = str(p.relative_to(ROOT))
        if use_git and git('show', f':{rel}', check=False) == write_rows(rows):
            git('add', '--', rel)
    for cmd in REGEN:
        run([sys.executable, SRC / cmd[0], *cmd[1:]], Path(cmd[0]).stem + ('_' + cmd[1] if len(cmd) > 1 else ''))
        print('ok:', ' '.join(cmd[:2]))
    if use_git:
        st = git('status', '--porcelain', '--', *(f'work/dump/{f}.jsonl' for f in DIALOG), check=False)
        print('git status of the dumps:', 'clean' if not st else '\n' + st)


def git_filter(mode: str, path: str):
    fmt = Path(path).stem
    data = sys.stdin.buffer.read()
    orig = ORIG / f'{fmt}.jsonl'
    if fmt not in DIALOG:
        sys.stdout.buffer.write(data)
        return
    rows = read_rows(data.decode('utf-8'))
    full = any('jp' in r for r in rows)
    if not orig.exists():
        if mode == 'clean' and full:
            sys.exit(f'kit.py clean {path}: has Japanese text and {orig.relative_to(ROOT)} is missing: run kit.py restore')
        sys.stdout.buffer.write(data)             # smudge sin restore: queda la fila del kit (restore la completa)
        return
    fresh = read_rows(orig.read_text(encoding='utf-8'))
    if mode == 'clean':
        out = strip(fmt, rows, fresh) if full else rows
    else:
        out = overlay(fmt, strip(fmt, rows, fresh) if full else rows, fresh)
    sys.stdout.buffer.write(write_rows(out).encode('utf-8'))


def pivot(only: list[str]):
    for fmt in only or DIALOG:
        p = DUMP / f'{fmt}.jsonl'
        rows = read_rows(p.read_text(encoding='utf-8'))
        if any('en_ref' in r for r in rows):
            print(f'{p.relative_to(ROOT)}: already has en_ref (pivot done before), left as is')
            continue
        n = 0
        for r in rows:
            if r.get('en'):
                r['en_ref'], r['en'] = r['en'], ''
                n += 1
        p.write_text(write_rows(rows), encoding='utf-8')
        print(f'{p.relative_to(ROOT)}: {n} rows: English moved to en_ref, en emptied')


def refresh_ref(ref: str):
    LOGS.mkdir(parents=True, exist_ok=True)
    for fmt, keys in DIALOG.items():
        rel = f'work/dump/{fmt}.jsonl'
        up = {tuple(r[k] for k in keys): r.get('en', '') for r in read_rows(git('show', f'{ref}:{rel}'))}
        p = DUMP / f'{fmt}.jsonl'
        rows = read_rows(p.read_text(encoding='utf-8'))
        changed = []
        for r in rows:
            new = up.get(tuple(r[k] for k in keys))
            if 'en_ref' in r and new and new != r['en_ref']:
                changed.append((r, r['en_ref'], new))
                r['en_ref'] = new
        if not changed:
            print(f'{rel}: English unchanged in {ref}')
            continue
        p.write_text(write_rows(rows), encoding='utf-8')
        review = LOGS / f'refresh_ref_{fmt}.tsv'
        with open(review, 'w', encoding='utf-8') as f:
            f.write('key\told_en_ref\tnew_en_ref\tyour_translation\n')
            for r, old, new in changed:
                if r.get('en'):
                    cells = ['/'.join(str(r[k]) for k in keys), old, new, r['en']]
                    f.write('\t'.join(c.replace('\n', '\\n') for c in cells) + '\n')
        n_rev = sum(1 for r, _, _ in changed if r.get('en'))
        print(f'{rel}: {len(changed)} rows got a new en_ref; {n_rev} of them are already translated → review '
              f'{review.relative_to(ROOT)}')


def check_stripped():
    bad = []
    for path in git('ls-files', '*.jsonl').split():
        blob = git('cat-file', 'blob', f':{path}')
        for n, line in enumerate(blob.splitlines(), 1):
            try:
                r = json.loads(line) if line.strip() else {}
            except ValueError:
                continue
            if isinstance(r, dict) and r.keys() & DROP:
                bad.append(f'{path}:{n}')
                break
    if bad:
        sys.exit('Game text committed ("jp"/"chs"): ' + ', '.join(bad) +
                 '\nThe kit never distributes game data: run kit.py restore (it sets up the git filter) and git add again')
    print('ok: no committed .jsonl has "jp" or "chs"')


def dedication_sums() -> str:
    return ''.join(f'{hashlib.sha256((ROOT / p).read_bytes()).hexdigest()}  {p}\n' for p in DEDICATION)


def check_dedication():
    want = (ROOT / DEDICATION_SUM).read_text()
    if dedication_sums() != want:
        sys.exit('The dedication screen changed (' + ', '.join(DEDICATION) + '). Requirement 2 (TRANSLATING.md): '
                 'it must not be modified. Restore it with: git checkout upstream/main -- ' + ' '.join(DEDICATION))
    print('ok: dedication screen unchanged')


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    sub = ap.add_subparsers(dest='cmd', required=True)
    e = sub.add_parser('export')
    e.add_argument('dest', type=Path)
    e.add_argument('--dry-run', action='store_true')
    sub.add_parser('restore')
    for m in ('clean', 'smudge'):
        sub.add_parser(m).add_argument('path')
    p = sub.add_parser('pivot')
    p.add_argument('--only', default='', help='comma-separated formats (default: all 6)')
    sub.add_parser('refresh-ref').add_argument('ref', help='git ref of upstream, e.g. upstream/main')
    sub.add_parser('check-stripped')
    sub.add_parser('dedication')
    a = ap.parse_args()
    if a.cmd == 'export':
        export(a.dest.resolve(), a.dry_run)
    elif a.cmd == 'restore':
        restore()
    elif a.cmd in ('clean', 'smudge'):
        git_filter(a.cmd, a.path)
    elif a.cmd == 'pivot':
        only = [f for f in a.only.split(',') if f]
        unknown = [f for f in only if f not in DIALOG]
        if unknown:
            sys.exit(f'unknown formats: {unknown} (valid: {", ".join(DIALOG)})')
        pivot(only)
    elif a.cmd == 'refresh-ref':
        refresh_ref(a.ref)
    elif a.cmd == 'check-stripped':
        check_stripped()
    else:
        check_dedication()


if __name__ == '__main__':
    main()
