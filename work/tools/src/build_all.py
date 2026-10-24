"""Pipeline de build completo: fuentes en inglés (volcados, traducciones, fuente) → archivos del juego → ISO verificada.

Uso (en server1: tools/build.sh …, que usa el venv; ver notes/pipeline_build.md):
  build_all.py --list                     etapas en orden y su estado (lista / pendiente / opcional)
  build_all.py [--name N]                 build con todas las etapas listas (las pendientes dejan su archivo en japonés); con --name sale como N_vNN (autoincremental; --no-version lo evita)
  build_all.py --dry-run                  plan + validación de textos + specs de menús, sin tocar archivos del juego
  build_all.py --selftest                 además: autopruebas de las herramientas e integridad de los volcados
  build_all.py --null                     sin reemplazos: la ISO tiene que salir idéntica a la original (toolchain)
  build_all.py --only snmsg,validate      solo esas etapas (+ preflight); --skip para excluir
  build_all.py --smoke [--routes …]       al final, rutas de regresión en el emulador (tools/regresion.sh)
  build_all.py --release                  al final, parche xdelta3 contra la ISO original + prueba de aplicación

Salida: work/build/<N>/ (en .gitignore)
  files/<RUTA_ISO>   archivos reconstruidos; a la ISO entran solo los que difieren del japonés
  specs/             entradas intermedias (specs de ovl_patch.py por overlay, filas de menú retenidas)
  logs/<etapa>.log   salida completa de cada herramienta
  check_text.csv     violaciones del validador
  <N>.bin/.cue/.xml  imagen (build_iso.py + mkpsxiso)
  verify.json        re-extracción de la imagen y comparación archivo por archivo
  manifest.json      qué entró: hashes de fuentes y salidas, filas traducidas, git, opciones, estado de cada etapa
No escribe sobre la ISO original ni sobre archivos versionados (la vista previa de la fuente va a build/<N>/). Fuera
de build/<N>/ solo escribe salidas generadas y en .gitignore: patches/vwf_table.bin y build/exe/ (por eso hay un lock).
Estados: ok (entra a la ISO) · sin cambios (idéntico al japonés: no entra) · pendiente (falta herramienta: el archivo
queda en japonés) · aviso (terminó con problemas permitidos) · plan (--dry-run) · error (corta el pipeline).
"""
from __future__ import annotations

import argparse
import contextlib
import csv
import datetime
import filecmp
import hashlib
import importlib.util
import io
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import time
import traceback
import xml.etree.ElementTree as ET
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Optional

SRC = Path(__file__).resolve().parent            # work/tools/src
TOOLS = SRC.parent                                # work/tools
WORK = TOOLS.parent                               # work
ROOT = WORK.parent                                # raíz del proyecto (acá vive la ISO original)
ISO_JP = WORK / 'iso_jp'
BUILD = Path(os.environ.get('SRW_BUILD_DIR') or WORK / 'build')
JP_CUE = Path(os.environ.get('SRW_JP_CUE') or ROOT / 'Super Robot Taisen Alpha (Japan) (v1.0).cue')
JP_BIN = JP_CUE.with_suffix('.bin')
FONT_TXT = WORK / 'font' / 'en_8px.txt'
VWF_TABLE = WORK / 'patches' / 'vwf_table.bin'   # la incluye vwf.asm y la leen los validadores: ruta fija
sys.path.insert(0, str(SRC))

SECTOR = 2352
CD_74 = 74 * 60 * 75            # 333.000 sectores: CD-R de 74 min
CD_80 = 80 * 60 * 75            # 360.000: CD-R de 80 min (algunas lectoras de PSX fallan cerca del borde)

# ───────────────────────────── Configuración (editar acá) ─────────────────────────────
EXE = 'SLPS_026.36'
EXE_OUT = WORK / 'build' / 'exe' / EXE           # salida fija de patches/vwf.asm
EXE_BASE = 0x80010000 - 0x800                    # dirección de RAM del byte 0 del archivo (cabecera de 0x800)
# Rangos que los parches del EXE pueden cambiar ([inicio, fin) en RAM). Un byte distinto fuera de estos = error
# (armips escribió donde no debía). Al sumar parches al EXE (strings, título de guardado) agregar sus rangos acá.
EXE_WINDOWS = {
    'VWF: código (vwf.asm)': (0x80018F30, 0x80018F78),
    'VWF: tabla de anchos': (0x80059480, 0x80059580),
    'objetos de texto (#57)': (0x80014AC8, 0x80014ACC),
    'título de guardado: sistema (#12)': (0x800100F0, 0x8001011F),
    'título de guardado: escenario (#12)': (0x80010120, 0x8001014F),
}
# Títulos de la partida guardada (los muestra la BIOS con su fuente SJIS, sin VWF): SJIS de ancho completo, in situ
# (47 B de lugar c/u). Ver notes/exe_strings.md. El nombre del archivo de la card (SRWAx/SRSYS) no se toca.
EXE_STRINGS = [
    (0x800100F0, 'スーパーロボット大戦アルファ　システムデータ', 'ＳＲＷ　Ａｌｐｈａ　Ｓｙｓｔｅｍ', 47),
    (0x80010120, 'スーパーロボット大戦アルファ　シナリオデータ%s', 'ＳＲＷ　Ａｌｐｈａ　Ｓｃｅｎａｒｉｏ%s', 47),
]
VWF_TABLE_ADDR = 0x80059480

# formato: (herramienta y argumentos previos a entrada/salida, fuente con "en", ruta en la ISO, nota técnica)
TEXT_BUILDS = {
    'snmsg':    (['snmsg.py', 'build'], 'dump/snmsg.jsonl', 'SNMAP/SNMSG.BIN', 'notes/poc_snmsg.md'),
    'script':   (['script_bin.py', 'build'], 'dump/script.jsonl', 'BUSTUP/SCRIPT.BIN', 'notes/script_bin.md'),
    'bxclist':  (['bxclist.py', 'build'], 'dump/bxclist.jsonl', 'BATTLE/BXCLIST.BIN', 'notes/bxclist.md'),
    'deadmess': (['deadmess_em.py', 'build', 'deadmess'], 'dump/deadmess.jsonl', 'SNMAP/DEADMESS.BIN',
                 'notes/deadmess_em.md'),
    'em':       (['deadmess_em.py', 'build', 'em'], 'dump/em.jsonl', 'SNMAP/EM.BIN', 'notes/deadmess_em.md'),
    'pilot':    (['pilot_bin.py', 'build'], 'dump/pilot.jsonl', 'UNITPRAM/PILOT.BIN', 'notes/pilot_bin.md'),
    # nombres de terreno y lugares (#221): un volcado, dos archivos (la clave "file" del volcado elige las filas)
    'mdata':    (['mdata_bin.py', 'build', 'SNMAP'], 'dump/mdata.jsonl', 'SNMAP/MDATA.BIN', 'notes/mdata.md'),
    'mdata_test': (['mdata_bin.py', 'build', 'TEST'], 'dump/mdata.jsonl', 'TEST/MDATA.BIN', 'notes/mdata.md'),
}
# traducciones que viven fuera de dump/ (check_text.py las valida con --input)
CHECK_INPUTS = {'dc': 'translation/dc_en.jsonl', 'dr': 'translation/dr_en.jsonl'}
MENUS_SRC = 'translation/menus_en.jsonl'
MENUS_MAP = 'translation/menus_map.txt'
SOURCES = {**{fmt: v[1] for fmt, v in TEXT_BUILDS.items()}, **CHECK_INPUTS, 'menus': MENUS_SRC}
# otras entradas cuyo hash va al manifiesto
EXTRA_INPUTS = ('font/en_8px.txt', 'patches/vwf.asm', MENUS_MAP, 'glossary/glossary.csv', 'glossary/units_en.csv',
                'translation/entry_en.csv', 'gfx/render/lugares_mapa.csv')

MENU_OVLS = ('IMIS', 'PRM', 'SNMP', 'BTL', 'SNDU', 'TITL', 'COMM', 'ENTR', 'SNDM')
ENTRY_OVLS = ('ENTR', 'SNMP', 'IMIS', 'PRM', 'TITL', 'SNDM', 'SNDU')   # entry_patch.py (se encadena sobre la salida de "menus")

# (formato, volcado de la herramienta, claves de fila, campos japoneses): el "jp" del volcado de trabajo tiene que
# seguir siendo el texto original en esa clave (protege contra filas corridas al pegar traducciones)
DUMP_INTEGRITY = (
    ('script', ['script_bin.py', 'dump'], ('script', 'inst'), ('jp',)),
    ('bxclist', ['bxclist.py', 'dump'], ('pilot', 'idx'), ('jp',)),
    ('mdata', ['mdata_bin.py', 'dump'], ('file', 'off'), ('jp',)),
    ('pilot', ['pilot_bin.py', 'dump'], ('id',), ('full', 'short')),
)
GRAPHICS = ('TEST/TXT30.TIM', 'TEST/TXT31.TIM', 'TEST/TXT32.TIM', 'TEST/TXT33.TIM', 'TEST/PRO_FONT.TIM',
            'FONTWIN/WINTEX.BIN', 'FONTWIN/WINDOW.TIM', 'TITLE/TITLEDAT.BIN', 'BATTLE/COMMON.BIN', 'BUSTUP/MAP.BIN',
            'SNMAP/KIEFETIM.BIN', 'OVL/PRO_GRP.BIN')   # gfx_entrega.py import (G14–G36 + largo del prólogo; G01–G13 = etapa titles)
GFX_PNG = WORK / 'gfx' / 'render' / 'out'          # salida de gfx_render.py render (validada con gfx_entrega check)


# ───────────────────────────── Utilidades ─────────────────────────────
class StageError(Exception):
    """Falla de una etapa: corta el pipeline (el manifiesto se escribe igual)."""


@dataclass
class Result:
    status: str                                    # ok · aviso · sin cambios · pendiente · omitida · plan · error
    summary: str = ''
    outputs: dict = field(default_factory=dict)    # ruta ISO → {sha1, bytes, bytes_jp, entra}
    data: dict = field(default_factory=dict)       # conteos y detalles para el manifiesto
    seconds: float = 0.0


@dataclass
class Ctx:
    name: str
    dir: Path
    args: argparse.Namespace
    ids: set = field(default_factory=set)               # etapas elegidas en esta corrida
    replacements: dict = field(default_factory=dict)   # ruta ISO → archivo local que entra a la ISO

    @property
    def dry_run(self) -> bool:
        return self.args.dry_run

    @property
    def files(self) -> Path:
        return self.dir / 'files'

    @property
    def logs(self) -> Path:
        return self.dir / 'logs'

    @property
    def bin(self) -> Path:
        return self.dir / f'{self.name}.bin'


def rel(p) -> str:
    """Ruta para mostrar: relativa a la raíz del proyecto si está adentro."""
    try:
        return str(Path(p).resolve().relative_to(ROOT))
    except ValueError:
        return str(p)


def sha1(path, chunk=1 << 20) -> str:
    h = hashlib.sha1()
    with open(path, 'rb') as f:
        for b in iter(lambda: f.read(chunk), b''):
            h.update(b)
    return h.hexdigest()


def iter_jsonl(path):
    with open(path, encoding='utf-8') as f:
        for line in f:
            if line.strip():
                yield json.loads(line)


def git_info() -> dict:
    def g(*a):
        try:
            return subprocess.run(['git', *a], cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip()
        except (OSError, subprocess.CalledProcessError):
            return ''
    return {'commit': g('rev-parse', 'HEAD'), 'rama': g('rev-parse', '--abbrev-ref', 'HEAD'),
            'sucio': bool(g('status', '--porcelain'))}


def py(tool: str, *args) -> list:
    """Comando para una herramienta de tools/src con el mismo intérprete (el venv en server1)."""
    return [sys.executable, SRC / tool, *args]


def armips_cmd() -> Optional[list]:
    """Igual que la función armips de env.sh: binario nativo si existe; si no, la build de Windows con wine."""
    native = TOOLS / 'bin' / 'armips'
    if native.is_file() and os.access(native, os.X_OK):
        return [str(native)]
    exe = TOOLS / 'bin' / 'armips' / 'armips.exe'
    if exe.is_file() and shutil.which('wine'):
        return ['wine', str(exe)]
    return None


def shown_cmd(cmd: list, cwd: Path) -> str:
    """Comando para mostrar o copiar: rutas relativas a cwd y el intérprete del venv como "$SRW_PY"."""
    venv, out = os.environ.get('SRW_PY'), []
    for c in cmd:
        if c == sys.executable:
            out.append('"$SRW_PY"' if venv and os.path.realpath(venv) == os.path.realpath(c) else 'python3')
            continue
        with contextlib.suppress(ValueError):
            c = str(Path(c).relative_to(cwd)) if Path(c).is_absolute() else c
        out.append(shlex.quote(c))
    return f'(cd {rel(cwd)} && {" ".join(out)})'


def run(ctx: Ctx, stage: str, cmd: list, cwd: Path = WORK, env: dict | None = None, ok=(0,),
        always: bool = False) -> tuple[int, str]:
    """Corre un comando y agrega su salida a logs/<etapa>.log. En --dry-run solo lo muestra, salvo always=True
    (pasos que no tocan archivos del juego, como la validación). Un código fuera de `ok` corta la etapa."""
    cmd = [str(c) for c in cmd]
    shown = shown_cmd(cmd, cwd)
    if ctx.dry_run and not always:
        print(f'        $ {shown}')
        return 0, ''
    ctx.logs.mkdir(parents=True, exist_ok=True)
    p = subprocess.run(cmd, cwd=cwd, env={**os.environ, **(env or {})}, stdout=subprocess.PIPE,
                       stderr=subprocess.STDOUT, text=True, errors='replace')
    log = ctx.logs / f'{stage}.log'
    with open(log, 'a', encoding='utf-8') as fh:
        fh.write(f'$ {shown}\n{p.stdout}\n[código de salida {p.returncode}]\n\n')
    if p.returncode not in ok:
        label = next((Path(c).name for c in cmd if c.endswith('.py')), Path(cmd[0]).name)
        tail = '\n'.join(p.stdout.strip().splitlines()[-8:])
        raise StageError(f'{label} → código {p.returncode} (log: {rel(log)})\n{tail}')
    return p.returncode, p.stdout


def register(ctx: Ctx, iso_path: str, local: Path) -> dict:
    """Anota un archivo reconstruido. Entra a la ISO solo si difiere del japonés: la imagen queda lo más cerca posible
    del original y verify compara todo lo demás contra iso_jp."""
    orig = ISO_JP / iso_path
    same = orig.exists() and filecmp.cmp(orig, local, shallow=False)
    if same:
        ctx.replacements.pop(iso_path, None)
    else:
        ctx.replacements[iso_path] = local
    return {'sha1': sha1(local), 'bytes': local.stat().st_size,
            'bytes_jp': orig.stat().st_size if orig.exists() else None, 'entra': not same}


def count_rows(fmt: str, path: Path) -> tuple[int, int]:
    """(filas, filas con inglés) de una fuente. PILOT: full_en/short_en; DC/DR: lista "en" paralela a los campos."""
    total = done = 0
    for r in iter_jsonl(path):
        total += 1
        if fmt == 'pilot':
            done += bool(r.get('full_en') or r.get('short_en'))
        elif fmt in ('dc', 'dr'):
            done += bool(r.get('en') and any(r['en']))
        else:
            done += bool(r.get('en'))
    return total, done


def capacity(sectors: int) -> str:
    """'ok' hasta un CD-R de 74 min, 'aviso' hasta 80 min, 'error' más allá."""
    return 'ok' if sectors <= CD_74 else 'aviso' if sectors <= CD_80 else 'error'


def minutes(sectors: int) -> str:
    return f'{sectors / 75 / 60:.1f} min'


# ───────────────────────────── Controles puros (probados en test_build_all.py) ─────────────────────────────
def diff_ranges(a: bytes, b: bytes) -> list[tuple[int, int]]:
    """Rangos [inicio, fin) de bytes distintos entre a y b (del mismo largo)."""
    out, start = [], None
    for i, (x, y) in enumerate(zip(a, b)):
        if x != y:
            if start is None:
                start = i
        elif start is not None:
            out.append((start, i))
            start = None
    if start is not None:
        out.append((start, min(len(a), len(b))))
    return out


def exe_problems(orig: bytes, new: bytes, table: bytes | None = None, windows: dict = EXE_WINDOWS) -> list[str]:
    """Problemas del EXE parcheado: tamaño distinto, bytes cambiados fuera de las ventanas permitidas, tabla VWF."""
    if len(orig) != len(new):
        return [f'el tamaño cambió: {len(orig)} → {len(new)} bytes']
    allowed = [(a - EXE_BASE, b - EXE_BASE) for a, b in windows.values()]
    out = [f'bytes cambiados fuera de las ventanas permitidas: archivo 0x{s:X}-0x{e:X} (RAM 0x{s + EXE_BASE:08X})'
           for s, e in diff_ranges(orig, new) if not any(a <= s and e <= b for a, b in allowed)]
    if table is not None:
        o = VWF_TABLE_ADDR - EXE_BASE
        if new[o:o + len(table)] != table:
            out.append('la tabla VWF dentro del EXE no coincide con patches/vwf_table.bin')
    return out


def menus_stale(rows, map_path: Path) -> list:
    """Filas de menus_en.jsonl que no coinciden con menus_map.txt (se editó el mapa y no se corrió menus_draft.py)."""
    import menus_draft
    try:
        m = menus_draft.load_map(map_path)
    except SystemExit as e:                         # load_map corta con SystemExit ante errores de formato
        return [({'file': '-', 'addr': '-', 'jp': '-'}, f'menus_map.txt: {e}')]
    out = []
    for r in rows:
        e = m.get(menus_draft.map_key(m, r) or '')
        if e is None:
            out.append((r, 'no está en menus_map.txt'))
        elif e[0] != r['en'] or (r.get('en_short') and e[1] != r['en_short']):
            out.append((r, 'texto distinto del de menus_map.txt'))
    return out


def cue_problems(cue_text: str, bin_name: str, ref_text: str | None = None) -> tuple[list, list]:
    """(errores, avisos) del .cue generado: un FILE con la imagen, pista 1 MODE2/2352, mismas pistas que el original."""
    errors, warns = [], []
    files = re.findall(r'^\s*FILE\s+"([^"]+)"', cue_text, re.M)
    if len(files) != 1 or Path(files[0]).name != bin_name:
        errors.append(f'el .cue referencia {files}, se esperaba "{bin_name}"')
    elif files[0] != bin_name:
        warns.append(f'el .cue usa una ruta ({files[0]}): no es portable, copiar .bin y .cue juntos')
    tracks = [t.upper() for t in re.findall(r'^\s*TRACK\s+\d+\s+(\S+)', cue_text, re.M)]
    if not tracks or tracks[0] != 'MODE2/2352':
        errors.append(f'la pista 1 no es MODE2/2352: {tracks[:1]}')
    if ref_text is not None:
        ref = [t.upper() for t in re.findall(r'^\s*TRACK\s+\d+\s+(\S+)', ref_text, re.M)]
        if tracks != ref:
            errors.append(f'pistas {tracks} distintas de las del .cue original {ref}')
    return errors, warns


def layout_paths(layout: Path | None = None) -> list[str]:
    """Rutas de archivo del layout de mkpsxiso (iso_jp/layout.xml), con el formato de isofs.py ("DIR/ARCH.EXT")."""
    tree = ET.parse(layout or ISO_JP / 'layout.xml')
    out = []

    def walk(node, prefix):
        for ch in node:
            if ch.tag == 'dir':
                walk(ch, prefix + ch.get('name') + '/')
            elif ch.tag == 'file':
                out.append(prefix + ch.get('name'))
    walk(tree.getroot().find('track').find('directory_tree'), '')
    return out


def verify_image(bin_path: Path, replacements: dict, mode: str = 'completa', null: bool = False,
                 jp_bin: Path | None = None, iso_jp: Path | None = None) -> dict:
    """Relee la imagen construida con isofs.py y la compara, archivo por archivo, con lo que se quiso meter:
    los reemplazos y, para el resto, iso_jp. mode 'reemplazos' compara contenido solo de los reemplazados (tamaño
    de todos). XA/STR (Form 2) se comparan por tamaño contra la ISO original."""
    import isofs
    jp_bin = JP_BIN if jp_bin is None else jp_bin
    iso_jp = ISO_JP if iso_jp is None else iso_jp
    errors, warns = [], []
    size = bin_path.stat().st_size
    sectors = size // SECTOR
    if size % SECTOR:
        errors.append(f'tamaño {size} no es múltiplo de {SECTOR}')
    cap = capacity(sectors)
    if cap != 'ok':
        (errors if cap == 'error' else warns).append(
            f'{sectors} sectores = {minutes(sectors)}: {"no entra en" if cap == "error" else "pasa de"} un CD-R de '
            f'{80 if cap == "error" else 74} min')
    img = isofs.Image(bin_path)
    got = {e.path: e for e in img.entries()}
    want = set(layout_paths(iso_jp / 'layout.xml'))
    errors += [f'falta en la imagen: {p}' for p in sorted(want - set(got))]
    errors += [f'sobra en la imagen: {p}' for p in sorted(set(got) - want)]
    jp = {}
    if jp_bin.exists():
        ref = isofs.Image(jp_bin)
        jp = {e.path: e for e in ref.entries()}
        ref.f.close()
    if not jp:
        warns.append('sin la ISO original: no se comparan XA/STR, área de sistema ni pistas del .cue')
    compared = form2 = 0
    for p, e in sorted(got.items()):
        if p not in want:
            continue
        if p.upper().endswith(isofs.FORM2_EXT):
            form2 += 1
            if p in jp and jp[p].size != e.size:
                errors.append(f'{p}: {e.size} bytes, en el original {jp[p].size}')
            continue
        src = Path(replacements.get(p, iso_jp / p))
        if not src.exists():
            errors.append(f'{p}: no existe {rel(src)} para comparar')
            continue
        if e.size != src.stat().st_size:
            errors.append(f'{p}: {e.size} bytes en la imagen, {src.stat().st_size} en {rel(src)}')
            continue
        if mode == 'completa' or p in replacements:
            compared += 1
            if img.read_file(e) != src.read_bytes():
                errors.append(f'{p}: el contenido no coincide con {rel(src)}')
    img.f.close()
    if jp:
        with open(bin_path, 'rb') as a, open(jp_bin, 'rb') as b:
            if a.read(16 * SECTOR) != b.read(16 * SECTOR):
                errors.append('sectores 0-15 (licencia / área de sistema) distintos de la ISO original')
    cue = bin_path.with_suffix('.cue')
    if cue.exists():
        ref_cue = jp_bin.with_suffix('.cue')
        e, w = cue_problems(cue.read_text(errors='replace'), bin_path.name,
                            ref_cue.read_text(errors='replace') if ref_cue.exists() else None)
        errors += e
        warns += w
    else:
        errors.append(f'no existe {cue.name}')
    if null:
        if not jp_bin.exists():
            errors.append('--null necesita la ISO original para comparar')
        elif sha1(bin_path) != sha1(jp_bin):
            errors.append('--null: la imagen no es idéntica a la original (¿cambió mkpsxiso o iso_jp?)')
    return {'bin': rel(bin_path), 'bytes': size, 'sectores': sectors, 'minutos': round(sectors / 4500, 2),
            'archivos': len(got), 'comparados': compared, 'xa_str': form2, 'reemplazos': sorted(replacements),
            'errores': errors, 'avisos': warns}


# ───────────────────────────── Etapas ─────────────────────────────
def subtitle_font() -> bool:
    try:
        import subtitle
        return bool(subtitle.find_font(subtitle.FONT))
    except (ImportError, SystemExit):
        return False


def dedication_font() -> bool:
    try:
        import dedicatoria
        return all(dedicatoria.font_path(f) for f, _ in (dedicatoria.DED_FONT, *dedicatoria.LABEL_FONTS))
    except (ImportError, SystemExit):
        return False


def requirements(ids: set) -> list[tuple[str, bool]]:
    """(qué, está) según las etapas elegidas: permite, p. ej., --only validate en una máquina sin la ISO."""
    req = []

    def need(label, ok):
        req.append((label, bool(ok)))
    if 'font' in ids:
        for p in ('FONTWIN/8FONT_R.TIM', 'FONTWIN/WINTEX.BIN'):
            need(f'iso_jp/{p}', (ISO_JP / p).exists())
        for mod in ('numpy', 'PIL'):
            need(f'módulo {mod} (usar el venv: $SRW_PY)', importlib.util.find_spec(mod))
    if 'dedicatoria' in ids:
        need('módulo segno (usar el venv: $SRW_PY)', importlib.util.find_spec('segno'))
        need('armips nativo (tools/bin/armips: dedicatoria.py no usa wine)', (WORK / 'tools' / 'bin' / 'armips').is_file())
        need('fuente DejaVuSansCondensed-Bold (fonts-dejavu-extra)', dedication_font())
    if 'exe' in ids:
        need(f'iso_jp/{EXE}', (ISO_JP / EXE).exists())
        need('armips (tools/bin/armips, o wine + tools/bin/armips/armips.exe)', armips_cmd())
    for fmt, (_, _, iso_path, _) in TEXT_BUILDS.items():
        if fmt in ids or 'selftest' in ids:
            need(f'iso_jp/{iso_path}', (ISO_JP / iso_path).exists())
    if 'selftest' in ids:
        need('iso_jp/UNITPRAM/ROBOT.RAF', (ISO_JP / 'UNITPRAM/ROBOT.RAF').exists())
    if 'menus' in ids:
        for o in MENU_OVLS:
            need(f'iso_jp/OVL/{o}_GRP.BIN', (ISO_JP / 'OVL' / f'{o}_GRP.BIN').exists())
    if 'titles' in ids:
        for p in ('TITLE/SUBTITLE.BIN', 'OVL/SNMP_GRP.BIN'):
            need(f'iso_jp/{p}', (ISO_JP / p).exists())
        need('fuente LiberationSerif-Bold (fonts-liberation)', subtitle_font())
    if 'layout' in ids:
        for p in ('OVL/SNMP_GRP.BIN', 'OVL/PRM_GRP.BIN'):
            need(f'iso_jp/{p}', (ISO_JP / p).exists())
    if 'iso' in ids or 'verify' in ids:
        need('iso_jp/layout.xml', (ISO_JP / 'layout.xml').exists())
    if 'iso' in ids:
        need('iso_jp/license_data.dat', (ISO_JP / 'license_data.dat').exists())
        need('tools/bin/mkpsxiso', (TOOLS / 'bin' / 'mkpsxiso').exists())
    if 'release' in ids:
        need('xdelta3 en el PATH', shutil.which('xdelta3'))
        need(f'ISO original ({JP_BIN.name})', JP_BIN.exists())
    if 'smoke' in ids:
        need('BIOS (Bios/scph100.bin)', (ROOT / 'Bios' / 'scph100.bin').exists())
        need('PCSX-Redux (tools/bin/PCSX-Redux-HEAD-x86_64.AppImage)',
             (TOOLS / 'bin' / 'PCSX-Redux-HEAD-x86_64.AppImage').exists())
    seen, out = set(), []
    for label, ok in req:
        if label not in seen:
            seen.add(label)
            out.append((label, ok))
    return out


def stage_preflight(ctx: Ctx) -> Result:
    missing = [label for label, ok in requirements(ctx.ids) if not ok]
    warns = []
    if not JP_BIN.exists():
        warns.append(f'sin la ISO original ({JP_BIN.name}): verify no compara XA/STR ni licencia')
    git = git_info()
    if git['sucio']:
        if ctx.args.strict:
            missing.append('árbol de git limpio (--strict)')
        else:
            warns.append('git con cambios sin commitear (queda en el manifiesto)')
    with contextlib.suppress(OSError):
        free = shutil.disk_usage(BUILD).free
        if free < 2 * 700 * 2**20:
            warns.append(f'poco disco: {free / 2**30:.1f} GiB libres (una build ocupa ~0,65 GiB)')
    data = {'faltan': missing, 'avisos': warns, 'git': git}
    if missing:
        if ctx.dry_run:
            return Result('plan', 'faltan (normal fuera de server1): ' + '; '.join(missing), data=data)
        raise StageError('faltan: ' + '; '.join(missing))
    return Result('ok', '; '.join(warns) or 'entorno completo', data=data)


def stage_selftest(ctx: Ctx) -> Result:
    if ctx.dry_run:
        return Result('plan', 'reconstrucción sin cambios == original en cada herramienta + pruebas unitarias + '
                              'integridad del "jp" de los volcados')
    import bxclist
    import deadmess_em
    import option_dict
    import pilot_bin
    import robot_raf
    import script_bin
    import snmsg
    import subtitle
    checks, buf = {}, io.StringIO()
    with contextlib.redirect_stdout(buf):
        checks['snmsg: volcado ↔ original'] = snmsg.check(ISO_JP / 'SNMAP/SNMSG.BIN', WORK / 'dump/snmsg.jsonl')
        data = (ISO_JP / 'BUSTUP/SCRIPT.BIN').read_bytes()
        scripts, _, first = script_bin.parse(data)
        checks['script_bin: reconstrucción'] = script_bin.build(scripts, first, data) == data
        data = (ISO_JP / 'BATTLE/BXCLIST.BIN').read_bytes()
        raws, blocks = bxclist.parse(data)
        checks['bxclist: reconstrucción'] = bxclist.build(raws, blocks, {}) == data
        checks['deadmess_em: selftest'] = deadmess_em.selftest()
        checks['pilot_bin: selftest'] = pilot_bin.selftest()
        data = (ISO_JP / 'UNITPRAM/ROBOT.RAF').read_bytes()
        recs = [rec for _, _, rec in robot_raf.entries(data)]
        checks['robot_raf: LZSS ida y vuelta'] = [r for _, _, r in robot_raf.entries(robot_raf.build_raf(recs))] == recs
        checks['option_dict: selftest (DC/DR)'] = option_dict.selftest()
        checks['subtitle: tabla de títulos ↔ original'] = subtitle.selftest()
    ctx.logs.mkdir(parents=True, exist_ok=True)
    (ctx.logs / 'selftest.log').write_text(buf.getvalue(), encoding='utf-8')
    run(ctx, 'selftest', [sys.executable, '-m', 'unittest', '-q', 'test_check_text', 'test_build_all'], cwd=SRC)
    tmp = ctx.dir / 'selftest'
    tmp.mkdir(parents=True, exist_ok=True)
    for fmt, tool, keys, cols in DUMP_INTEGRITY:
        fresh_path = tmp / f'{fmt}.jsonl'
        run(ctx, 'selftest', py(*tool, fresh_path))
        fresh = {tuple(r[k] for k in keys): tuple(r[c] for c in cols) for r in iter_jsonl(fresh_path)}
        bad = [tuple(r[k] for k in keys) for r in iter_jsonl(WORK / TEXT_BUILDS[fmt][1])
               if fresh.get(tuple(r[k] for k in keys)) != tuple(r.get(c) for c in cols)]
        checks[f'{fmt}: "jp" del volcado de trabajo == original ({len(bad)} filas distintas)'] = not bad
    failed = [k for k, v in checks.items() if not v]
    if failed:
        raise StageError('fallaron: ' + '; '.join(failed))
    return Result('ok', f'{len(checks)} controles OK', data={'controles': checks})


def stage_font(ctx: Ctx) -> Result:
    tim, wintex = ctx.files / 'FONTWIN' / '8FONT_R.TIM', ctx.files / 'FONTWIN' / 'WINTEX.BIN'
    run(ctx, 'font', py('font_build.py', '--tim-in', ISO_JP / 'FONTWIN/8FONT_R.TIM', '--glyphs', FONT_TXT,
                        '--tim-out', tim, '--table', VWF_TABLE, '--wintex-in', ISO_JP / 'FONTWIN/WINTEX.BIN',
                        '--wintex-out', wintex, '--preview', ctx.dir / 'font_preview.png'),
        env={'PYTHONPATH': str(SRC)})
    if ctx.dry_run:
        return Result('plan', f'{rel(FONT_TXT)} → 8FONT_R.TIM, WINTEX.BIN (entrada 0), {rel(VWF_TABLE)}')
    import check_text   # sin vwf_table.bin (nube) los validadores derivan la tabla de en_8px.txt: tiene que ser la misma
    if check_text.table_from_font(FONT_TXT) != VWF_TABLE.read_bytes():
        raise StageError('patches/vwf_table.bin no coincide con la tabla que check_text.py deriva de font/en_8px.txt')
    outs = {p: register(ctx, p, f) for p, f in (('FONTWIN/8FONT_R.TIM', tim), ('FONTWIN/WINTEX.BIN', wintex))}
    return Result('ok', f'tabla VWF {sha1(VWF_TABLE)[:10]} · vista previa {rel(ctx.dir / "font_preview.png")}',
                  outputs=outs)


def stage_validate(ctx: Ctx) -> Result:
    csv_path = ctx.dir / 'check_text.csv'
    cmd = py('check_text.py', '--csv', csv_path)
    for fmt, src in CHECK_INPUTS.items():
        cmd += ['--input', f'{fmt}={WORK / src}']
    code, _ = run(ctx, 'validate', cmd, ok=(0, 1), always=True)
    sev = Counter()
    if csv_path.exists():
        with open(csv_path, encoding='utf-8') as fh:
            sev = Counter(r['severity'] for r in csv.DictReader(fh))
    counts = {fmt: count_rows(fmt, WORK / src) for fmt, src in SOURCES.items() if (WORK / src).exists()}
    problems = []
    if code:
        problems.append(f"{sev['error']} errores de texto (detalle: {rel(csv_path)})")
    import check_text   # con --only validate (sin "font") la tabla puede ser de una fuente anterior
    if VWF_TABLE.exists() and VWF_TABLE.read_bytes() != check_text.table_from_font(FONT_TXT):
        problems.append('patches/vwf_table.bin no corresponde a font/en_8px.txt: correr también la etapa font')
    stale = menus_stale(list(iter_jsonl(WORK / MENUS_SRC)), WORK / MENUS_MAP)
    if stale:
        problems.append(f'{len(stale)} filas de menus_en.jsonl no coinciden con menus_map.txt: correr '
                        f'tools/src/menus_draft.py (p. ej. {stale[0][0]["jp"]!r}: {stale[0][1]})')
    data = {'errores': sev['error'], 'avisos': sev['warn'], 'menus_desactualizados': len(stale),
            'traducido': {fmt: {'filas': t, 'en_ingles': d} for fmt, (t, d) in counts.items()}}
    summary = (f"{sev['error']} errores · {sev['warn']} avisos · con inglés: "
               + ', '.join(f'{fmt} {d}/{t}' for fmt, (t, d) in counts.items()))
    if problems and not ctx.args.allow_text_errors:
        raise StageError('; '.join(problems))
    return Result('aviso' if problems else 'ok', summary + ''.join(f' · PERMITIDO: {p}' for p in problems), data=data)


def stage_exe(ctx: Ctx) -> Result:
    cmd = armips_cmd() or ['armips']
    if not ctx.dry_run:
        EXE_OUT.parent.mkdir(parents=True, exist_ok=True)
        EXE_OUT.unlink(missing_ok=True)   # salida fija de vwf.asm: sin esto, si armips falla se copiaría una vieja
    run(ctx, 'exe', cmd + ['patches/vwf.asm'], cwd=WORK, env={'WINEDEBUG': '-all'})
    if ctx.dry_run:
        return Result('plan', f'patches/vwf.asm → {rel(EXE_OUT)} → files/{EXE} + control de ventanas')
    if not EXE_OUT.exists():
        raise StageError(f'armips no generó {rel(EXE_OUT)}')
    dst = ctx.files / EXE
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(EXE_OUT, dst)
    problems = exe_problems((ISO_JP / EXE).read_bytes(), dst.read_bytes(), VWF_TABLE.read_bytes())
    if problems:
        raise StageError('; '.join(problems))
    changed = sum(e - s for s, e in diff_ranges((ISO_JP / EXE).read_bytes(), dst.read_bytes()))
    return Result('ok', f'{changed} bytes cambiados, todos dentro de: {", ".join(EXE_WINDOWS)}',
                  outputs={EXE: register(ctx, EXE, dst)})


def stage_exe_strings(ctx: Ctx) -> Result:
    if ctx.dry_run:
        return Result('plan', f'{len(EXE_STRINGS)} títulos de guardado in situ sobre files/{EXE}')
    dst = ctx.files / EXE
    if not dst.exists():                 # sin la etapa exe: partir del original
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ISO_JP / EXE, dst)
    data = bytearray(dst.read_bytes())
    for addr, jp, en, room in EXE_STRINGS:
        off = addr - EXE_BASE
        old, new = jp.encode('cp932') + b'\0', en.encode('cp932') + b'\0'
        if bytes(data[off:off + len(old)]) != old:
            raise StageError(f'{addr:#x}: el EXE no tiene el japonés esperado')
        if len(new) > room:
            raise StageError(f'{addr:#x}: {len(new)} B > {room} B de lugar')
        data[off:off + room] = new.ljust(room, b'\0')
    dst.write_bytes(bytes(data))
    problems = exe_problems((ISO_JP / EXE).read_bytes(), bytes(data), VWF_TABLE.read_bytes())
    if problems:
        raise StageError('; '.join(problems))
    return Result('ok', f'{len(EXE_STRINGS)} títulos de guardado en inglés (SJIS ancho completo)',
                  outputs={EXE: register(ctx, EXE, dst)})


def make_text_stage(fmt: str) -> Callable[[Ctx], Result]:
    tool, src, iso_path, _ = TEXT_BUILDS[fmt]

    def stage(ctx: Ctx) -> Result:
        total, done = count_rows(fmt, WORK / src)
        dst = ctx.files / iso_path
        if not ctx.dry_run:
            dst.parent.mkdir(parents=True, exist_ok=True)
        _, out = run(ctx, fmt, py(*tool, WORK / src, dst))
        summary = f'{done}/{total} filas con inglés'
        if ctx.dry_run:
            return Result('plan', summary)
        # snmsg.py informa los errores y sigue (usa el japonés en ese casillero): no dejarlo pasar en silencio
        errors = [ln for ln in out.splitlines() if ln.startswith('ERROR')]
        notes = [ln for ln in out.splitlines() if ln.startswith('AVISO')]
        if errors and not ctx.args.allow_text_errors:
            raise StageError(f'{len(errors)} errores (log: {rel(ctx.logs / (fmt + ".log"))}): ' + errors[0])
        info = register(ctx, iso_path, dst)
        status = 'aviso' if errors or notes else 'ok' if info['entra'] else 'sin cambios'
        summary += ''.join(f' · {x}' for x in notes) + (f' · {len(errors)} errores PERMITIDOS' if errors else '')
        return Result(status, summary, outputs={iso_path: info}, data={'filas': total, 'en_ingles': done})
    return stage


def stage_robot(ctx: Ctx) -> Result:
    """robot_raf.py build: nombres de unidades (≤21 B) y armas (≤19 B) desde glossary.csv → LZSS; sale con error si
    algo queda sin traducción o no entra, y controla que solo cambien los campos de nombre."""
    iso_path = 'UNITPRAM/ROBOT.RAF'
    dst = ctx.files / iso_path
    if not ctx.dry_run:
        dst.parent.mkdir(parents=True, exist_ok=True)
    _, out = run(ctx, 'robot', py('robot_raf.py', 'build', dst, '--report', ctx.logs / 'robot_names.csv'))
    if ctx.dry_run:
        return Result('plan', 'glossary.csv → robot_raf.py build')
    return Result('ok', out.strip().splitlines()[-1], outputs={iso_path: register(ctx, iso_path, dst)})


def make_dict_stage(fmt: str) -> Callable[[Ctx], Result]:
    """option_dict.py build: fichas de translation/{fmt}_en.jsonl en los campos fijos (relleno 0xCD) + LZSS; sale con
    error si un campo no entra (esa ficha quedaría en japonés)."""
    iso_path = f'OPTION/{fmt.upper()}.BIN'

    def stage(ctx: Ctx) -> Result:
        dst = ctx.files / iso_path
        if not ctx.dry_run:
            dst.parent.mkdir(parents=True, exist_ok=True)
        _, out = run(ctx, fmt, py('option_dict.py', 'build', fmt, WORK / f'translation/{fmt}_en.jsonl', dst))
        if ctx.dry_run:
            return Result('plan', f'translation/{fmt}_en.jsonl → option_dict.py build')
        return Result('ok', out.strip().splitlines()[-1], outputs={iso_path: register(ctx, iso_path, dst)})
    return stage


def stage_menus(ctx: Ctx) -> Result:
    """ovl_patch.py sobre menus_en.jsonl: en in situ → en reubicado (pool: slots liberados, sobrantes, cola de zona) →
    en_short → japonés; relee cada overlay y sale con 1 si un texto o una referencia no quedó donde debe."""
    out = ctx.dir / 'menus'
    run(ctx, 'menus', py('ovl_patch.py', '--jsonl', WORK / MENUS_SRC, '--out', out))
    if ctx.dry_run:
        return Result('plan', f'ovl_patch.py → {len(MENU_OVLS)} overlays')
    stats = json.loads((out / 'stats.json').read_text(encoding='utf-8'))
    outputs = {}
    for ovl in stats:
        iso_path = f'OVL/{ovl}_GRP.BIN'
        outputs[iso_path] = register(ctx, iso_path, out / f'{ovl}_GRP.BIN')
    tot = Counter()
    for st in stats.values():
        tot.update({k: st[k] for k in ('in situ', 'reubicado', 'corta', 'sin cambio')})
    summary = (f'{len(stats)} overlays · {tot["in situ"]} in situ, {tot["reubicado"]} reubicados '
               f'({tot["corta"]} con la forma corta) · {tot["sin cambio"]} quedan en japonés (menus/report.csv)')
    return Result('aviso' if tot['sin cambio'] else 'ok', summary, outputs=outputs,
                  data={o: {k: st[k] for k in ('in situ', 'reubicado', 'corta', 'sin cambio', 'pool_left')}
                        for o, st in stats.items()})

def stage_entry(ctx: Ctx) -> Result:
    """entry_patch.py sobre la salida de "menus" (o iso_jp si no corrió): editor de nombres con topes 8/8/8, tabla
    por defecto (translation/entry_en.csv) y "%s %s" / $f en inglés; compara cada cambio con el original."""
    src = ctx.dir / 'menus' if 'menus' in ctx.ids else '-'
    out = ctx.dir / 'entry'
    _, log = run(ctx, 'entry', py('entry_patch.py', 'build', src, out))
    if ctx.dry_run:
        return Result('plan', f'entry_patch.py → {", ".join(ENTRY_OVLS)}')
    outputs = {f'OVL/{o}_GRP.BIN': register(ctx, f'OVL/{o}_GRP.BIN', out / f'{o}_GRP.BIN') for o in ENTRY_OVLS}
    notes = [ln for ln in log.splitlines() if ln.startswith('AVISO')]
    changes = sum(1 for ln in log.splitlines() if ln.startswith(ENTRY_OVLS))
    return Result('ok', f'{changes} cambios en {len(ENTRY_OVLS)} overlays' + ''.join(f' · {n}' for n in notes),
                  outputs=outputs)


def stage_titles(ctx: Ctx) -> Result:
    """subtitle.py build: títulos de escenario en inglés (misiones.csv) → hojas de TITLE/SUBTITLE.BIN reempaquetadas +
    tabla de recortes y encabezado "Stage N" en SNMP, encadenado sobre el SNMP de "entry" (o "menus", o iso_jp)."""
    src = next((ctx.dir / s / 'SNMP_GRP.BIN' for s in ('entry', 'menus') if s in ctx.ids), '-')
    out = ctx.dir / 'titles'
    _, log = run(ctx, 'titles', py('subtitle.py', 'build', src, out))
    if ctx.dry_run:
        return Result('plan', f'subtitle.py build {rel(src) if src != "-" else "iso_jp"} → SUBTITLE.BIN + SNMP_GRP.BIN')
    outputs = {p: register(ctx, p, out / Path(p).name) for p in ('TITLE/SUBTITLE.BIN', 'OVL/SNMP_GRP.BIN')}
    notes = [ln for ln in log.splitlines() if ln.startswith('AVISO')]
    return Result('aviso' if notes else 'ok', log.strip().splitlines()[-1] + ''.join(f' · {n}' for n in notes) +
                  f' · vista previa: {rel(out / "preview")}', outputs=outputs)

def stage_layout(ctx: Ctx) -> Result:
    """layout_patch.py build (#66): x de menús y títulos de SNMP según el ancho real del inglés (tabla VWF) y recuadro
    del menú de comandos de PRM ensanchado para "Transform"; encadenado sobre el SNMP de "titles"/"entry"/"menus" y el
    PRM de "entry"/"menus" (o iso_jp)."""
    snmp = next((ctx.dir / s / 'SNMP_GRP.BIN' for s in ('titles', 'entry', 'menus') if s in ctx.ids), '-')
    prm = next((ctx.dir / s / 'PRM_GRP.BIN' for s in ('entry', 'menus') if s in ctx.ids), '-')
    out = ctx.dir / 'layout'
    _, log = run(ctx, 'layout', py('layout_patch.py', 'build', snmp, prm, out))
    if ctx.dry_run:
        return Result('plan', 'layout_patch.py build → SNMP_GRP.BIN + PRM_GRP.BIN')
    outputs = {p: register(ctx, p, out / Path(p).name) for p in ('OVL/SNMP_GRP.BIN', 'OVL/PRM_GRP.BIN')}
    notes = [ln for ln in log.splitlines() if ln.startswith('AVISO')]
    return Result('aviso' if notes else 'ok', log.strip().splitlines()[-1] + ''.join(f' · {n}' for n in notes),
                  outputs=outputs)


def stage_copyright(ctx: Ctx) -> Result:
    """copyright_patch.py (#74): ancho (y posición del par 光プロ…/アトランティス) de cada línea de la pantalla de copyright
    en TITL según el inglés ya renderizado (gfx/render/out/G20.png); encadenado sobre el TITL de "entry"/"menus"."""
    titl = next((ctx.dir / s / 'TITL_GRP.BIN' for s in ('entry', 'menus') if s in ctx.ids), '-')
    out = ctx.dir / 'copyright'
    _, log = run(ctx, 'copyright', py('copyright_patch.py', 'build', titl, GFX_PNG / 'G20.png', out))
    if ctx.dry_run:
        return Result('plan', 'copyright_patch.py build → TITL_GRP.BIN')
    outputs = {'OVL/TITL_GRP.BIN': register(ctx, 'OVL/TITL_GRP.BIN', out / 'TITL_GRP.BIN')}
    return Result('ok', log.strip().splitlines()[-1], outputs=outputs)


def stage_dedicatoria(ctx: Ctx) -> Result:
    """dedicatoria.py build (#279): pantalla de dedicatoria + 2 QR después del copyright. Reempaqueta la hoja G20 de
    TITLEDAT (de "graphics") con su paleta, reubica los recortes del copyright en TITL (de "copyright") y arma el código
    (patches/dedicatoria.asm) en la cola del último sector de MOVE_GRP (sin correr ningún LBA)."""
    tdat = ctx.dir / 'graphics' / 'TITLE' / 'TITLEDAT.BIN'
    titl = ctx.dir / 'copyright' / 'TITL_GRP.BIN'
    if not ctx.dry_run and not (tdat.exists() and titl.exists()):
        return Result('pendiente', 'necesita las salidas de "graphics" (TITLEDAT) y "copyright" (TITL)')
    out = ctx.dir / 'dedicatoria'
    _, log = run(ctx, 'dedicatoria', py('dedicatoria.py', 'build', tdat, titl, out))
    if ctx.dry_run:
        return Result('plan', 'dedicatoria.py build → TITLEDAT.BIN + TITL_GRP.BIN + MOVE_GRP.BIN')
    outputs = {p: register(ctx, p, out / p) for p in ('TITLE/TITLEDAT.BIN', 'OVL/TITL_GRP.BIN', 'OVL/MOVE_GRP.BIN')}
    return Result('ok', log.strip().splitlines()[-1], outputs=outputs)


def stage_graphics(ctx: Ctx) -> Result:
    """gfx_entrega.py import de los PNG de gfx_render.py (work/gfx/render/out/): check + reinserción de índices; los
    contenedores LZSS se recomprimen. WINTEX.BIN/WINDOW.TIM parten de la salida de "font" si corrió. G01–G13
    (SUBTITLE.BIN) no: los genera la etapa "titles" (gfx_entrega ignora esos PNG)."""
    pngs = sorted(p.stem for p in GFX_PNG.glob('G[0-9][0-9].png') if int(p.stem[1:]) > 13) \
        if GFX_PNG.is_dir() else []
    if not pngs:
        return Result('pendiente', f'sin PNG en {rel(GFX_PNG)}: correr gfx_render.py render')
    out = ctx.dir / 'graphics'
    base = [ctx.files] if 'font' in ctx.ids else []
    _, log = run(ctx, 'graphics', py('gfx_entrega.py', 'import', GFX_PNG, out, *base), env={'PYTHONPATH': str(SRC)})
    if ctx.dry_run:
        return Result('plan', f'gfx_entrega.py import: {len(pngs)} piezas ({", ".join(pngs)})')
    outputs = {}
    for f in sorted(out.rglob('*')):
        if f.is_file():
            iso_path = f.relative_to(out).as_posix()
            outputs[iso_path] = register(ctx, iso_path, f)
    notes = [ln for ln in log.splitlines() if ln.startswith('AVISO')]
    return Result('aviso' if notes else 'ok', f'{len(pngs)} piezas → {len(outputs)} archivos'
                  + ''.join(f' · {n}' for n in notes), outputs=outputs)


def stage_iso(ctx: Ctx) -> Result:
    pairs = [] if ctx.args.null else [f'{p}={f}' for p, f in sorted(ctx.replacements.items())]
    run(ctx, 'iso', py('build_iso.py', ctx.bin, *pairs))
    if ctx.dry_run:
        return Result('plan', 'entran solo los archivos que resulten distintos del japonés')
    sectors = ctx.bin.stat().st_size // SECTOR
    return Result('ok', f'{len(pairs)} archivos reemplazados · {sectors} sectores ({minutes(sectors)})',
                  data={'bin': rel(ctx.bin), 'bytes': ctx.bin.stat().st_size, 'sectores': sectors,
                        'sha1': sha1(ctx.bin), 'reemplazos': len(pairs)})


def stage_verify(ctx: Ctx) -> Result:
    if ctx.args.verify == 'no':
        return Result('omitida', '--verify no')
    if ctx.dry_run:
        return Result('plan', f'releer {ctx.bin.name} y comparar {ctx.args.verify}; sectores ≤ 74 min; .cue; licencia')
    rep = verify_image(ctx.bin, {} if ctx.args.null else ctx.replacements, ctx.args.verify, ctx.args.null)
    (ctx.dir / 'verify.json').write_text(json.dumps(rep, ensure_ascii=False, indent=1), encoding='utf-8')
    if rep['errores']:
        raise StageError(f"{len(rep['errores'])} errores (verify.json): " + '; '.join(rep['errores'][:5]))
    return Result('aviso' if rep['avisos'] else 'ok',
                  f"{rep['archivos']} archivos, {rep['comparados']} comparados byte a byte, {rep['xa_str']} XA/STR por "
                  f"tamaño · {minutes(rep['sectores'])}" + ''.join(f' · {w}' for w in rep['avisos']), data=rep)


def stage_smoke(ctx: Ctx) -> Result:
    out = WORK / 'emu' / 'shots' / ctx.name
    env = {'REF': str(Path(ctx.args.ref).resolve())} if ctx.args.ref else {}
    run(ctx, 'smoke', ['bash', TOOLS / 'regresion.sh', ctx.bin.with_suffix('.cue'), out,
                       *ctx.args.routes.split(',')], env=env)
    return Result('plan' if ctx.dry_run else 'ok',
                  f'rutas {ctx.args.routes} → {rel(out)}/<ruta>/sheet.png (revisar a ojo; checklist N1)')


def stage_release(ctx: Ctx) -> Result:
    x = shutil.which('xdelta3') or 'xdelta3'
    patch = ctx.dir / f'{ctx.name}.xdelta'
    check = ctx.dir / 'release_check.bin'
    run(ctx, 'release', [x, '-e', '-9', '-f', '-s', JP_BIN, ctx.bin, patch])
    run(ctx, 'release', [x, '-d', '-f', '-s', JP_BIN, patch, check])   # aplicar sobre la original: tiene que dar igual
    if ctx.dry_run:
        return Result('plan', f'{patch.name} + SHA1SUMS')
    ok = sha1(check) == sha1(ctx.bin)
    check.unlink()                                  # copia temporal de ~0,65 GB creada recién por esta etapa
    if not ok:
        raise StageError('el parche aplicado sobre la ISO original no reproduce la build')
    sums = {JP_BIN.name + ' (original esperada)': sha1(JP_BIN), ctx.bin.name: sha1(ctx.bin), patch.name: sha1(patch)}
    (ctx.dir / 'SHA1SUMS').write_text(''.join(f'{h}  {n}\n' for n, h in sums.items()), encoding='utf-8')
    return Result('ok', f'{patch.name} ({patch.stat().st_size / 2**20:.1f} MiB), probado sobre la original',
                  data={'parche': rel(patch), 'sha1': sums})


@dataclass
class Stage:
    id: str
    title: str
    run: Optional[Callable[[Ctx], Result]] = None   # None = pendiente: el archivo queda en japonés
    outputs: tuple = ()                             # rutas de la ISO que produce (o producirá)
    needs: str = ''                                 # qué falta, si está pendiente
    ref: str = ''                                   # nota técnica
    optional: str = ''                              # flag que la activa (no corre por defecto)


STAGES = [
    Stage('preflight', 'Entorno según las etapas elegidas: iso_jp, herramientas, módulos, git, disco',
          stage_preflight),
    Stage('selftest', 'Autopruebas de las herramientas + integridad del "jp" de los volcados', stage_selftest,
          optional='--selftest'),
    Stage('font', 'Fuente inglesa + tabla VWF (font_build.py)', stage_font,
          ('FONTWIN/8FONT_R.TIM', 'FONTWIN/WINTEX.BIN'), ref='notes/fuente_en.md'),
    Stage('validate', 'Textos (check_text.py) y menus_en.jsonl al día con menus_map.txt', stage_validate,
          ref='notes/check_text.md'),
    Stage('exe', 'EXE con VWF (armips patches/vwf.asm) + control de ventanas', stage_exe, (EXE,),
          ref='notes/vwf_investigacion.md'),
    *[Stage(fmt, f'{v[2]} ← {v[1]}', make_text_stage(fmt), (v[2],), ref=v[3]) for fmt, v in TEXT_BUILDS.items()],
    Stage('robot', 'Nombres de unidades y armas → UNITPRAM/ROBOT.RAF (glossary.csv)', stage_robot,
          ('UNITPRAM/ROBOT.RAF',), ref='notes/units_en.md · notes/weapons_review.md · notes/compresion.md'),
    Stage('dc', 'Diccionario de personajes → OPTION/DC.BIN (option_dict.py)', make_dict_stage('dc'),
          ('OPTION/DC.BIN',), ref='notes/diccionarios_traduccion.md'),
    Stage('dr', 'Diccionario de robots → OPTION/DR.BIN (option_dict.py)', make_dict_stage('dr'),
          ('OPTION/DR.BIN',), ref='notes/diccionarios_traduccion.md'),
    Stage('menus', 'Menús de overlays (menus_en.jsonl → ovl_patch.py)', stage_menus,
          tuple(f'OVL/{o}_GRP.BIN' for o in MENU_OVLS), ref='notes/menus.md'),
    Stage('exe_strings', 'Strings del EXE: títulos de la partida guardada (memory card)', stage_exe_strings, (EXE,),
          ref='notes/exe_strings.md'),
    Stage('entry', 'Protagonista: topes del editor 8/8/8, nombres por defecto y nombre completo en inglés',
          stage_entry, tuple(f'OVL/{o}_GRP.BIN' for o in ENTRY_OVLS), ref='notes/nombres_protagonistas.md'),
    Stage('titles', 'Títulos de escenario: hojas de SUBTITLE.BIN + tabla de recortes y "Stage N" en SNMP '
          '(subtitle.py, encadenado sobre "entry")', stage_titles, ('TITLE/SUBTITLE.BIN', 'OVL/SNMP_GRP.BIN'),
          ref='notes/graficos.md'),
    Stage('layout', 'Posiciones de menús y títulos según el ancho del inglés + menú de comandos más ancho '
          '(layout_patch.py, encadenado sobre "titles")', stage_layout, ('OVL/SNMP_GRP.BIN', 'OVL/PRM_GRP.BIN'),
          ref='notes/menus.md'),
    Stage('copyright', 'Pantalla de copyright: ancho de cada línea en TITL según el inglés (copyright_patch.py, '
          'encadenado sobre "entry")', stage_copyright, ('OVL/TITL_GRP.BIN',), ref='notes/graficos.md'),
    Stage('graphics', 'Gráficos con texto (prólogo, interfaz, efectos, barreras, mapa) ← gfx/render/out',
          stage_graphics, GRAPHICS, ref='gfx/MANUAL_render.md · notes/graficos.md'),
    Stage('dedicatoria', 'Pantalla de dedicatoria + 2 QR después del copyright (dedicatoria.py, encadenado sobre '
          '"copyright" y "graphics"; código en la cola de MOVE_GRP)', stage_dedicatoria,
          ('TITLE/TITLEDAT.BIN', 'OVL/TITL_GRP.BIN', 'OVL/MOVE_GRP.BIN'), ref='notes/graficos.md'),
    Stage('iso', 'Imagen .bin/.cue (build_iso.py + mkpsxiso)', stage_iso),
    Stage('verify', 'Re-extracción: hashes de todos los archivos, sectores, .cue, licencia', stage_verify),
    Stage('smoke', 'Rutas de regresión en el emulador (tools/regresion.sh)', stage_smoke, optional='--smoke',
          ref='notes/checklist_regresion.md'),
    Stage('release', 'Parche xdelta3 contra la ISO original + prueba de aplicación', stage_release,
          optional='--release'),
]
NULL_STAGES = {'preflight', 'selftest', 'iso', 'verify', 'smoke', 'release'}   # --null: sin etapas de contenido


def select(args) -> list[Stage]:
    ids = [s.id for s in STAGES]
    only = set(args.only.split(',')) if args.only else None
    skip = set(args.skip.split(',')) if args.skip else set()
    bad = sorted(((only or set()) | skip) - set(ids))
    if bad:
        raise SystemExit(f'etapas desconocidas: {bad}. Válidas: {", ".join(ids)}')
    flags = {'selftest': args.selftest, 'smoke': args.smoke, 'release': args.release}
    out = []
    for s in STAGES:
        if s.id == 'preflight':
            take = True
        elif args.null and s.id not in NULL_STAGES:
            take = False
        elif only is not None:
            take = s.id in only
        else:
            take = flags.get(s.id, True)
        if take and s.id not in skip:
            out.append(s)
    chosen = {s.id for s in out}
    if 'verify' in chosen and 'iso' not in chosen:
        raise SystemExit('verify necesita iso en la misma corrida (usa los reemplazos de esta build)')
    return out


def list_stages():
    print(f'{"#":>2}  {"etapa":11} {"estado":10} descripción')
    for i, s in enumerate(STAGES, 1):
        st = 'opcional' if s.optional else 'pendiente' if s.run is None else 'lista'
        print(f'{i:2}  {s.id:11} {st:10} {s.title}' + (f' [{s.optional}]' if s.optional else ''))
        if s.run is None:
            print(f'{"":25}falta: {s.needs}')
        if s.ref:
            print(f'{"":25}ver: {s.ref}')


def default_name(null: bool) -> str:
    g = git_info()
    stamp = datetime.datetime.now().strftime('%Y%m%d-%H%M')
    tag = (g['commit'][:7] or 'sin-git') + ('-sucio' if g['sucio'] else '')
    return f"srwa_{'null' if null else 'en'}_{stamp}_{tag}"


def next_version_name(base: str) -> str:
    """<base>_vNN con NN = siguiente al mayor que ya existe en work/build/ (builds de prueba: saber cuál es la última)."""
    import re
    pat = re.compile(re.escape(base) + r'_v(\d+)$')
    used = [int(m.group(1)) for d in BUILD.glob(base + '_v*') if (m := pat.match(d.name))] if BUILD.exists() else []
    return f'{base}_v{max(used, default=0) + 1:02d}'


def acquire_lock():
    import fcntl
    BUILD.mkdir(parents=True, exist_ok=True)
    fh = open(BUILD / '.build.lock', 'w')
    try:
        fcntl.flock(fh, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        raise SystemExit('hay otra build corriendo (work/build/.build.lock): patches/vwf_table.bin y build/exe/ '
                         'son compartidos')
    return fh


def write_manifest(ctx: Ctx, results: list, t0: float):
    hashes = {}
    for src in list(SOURCES.values()) + list(EXTRA_INPUTS):
        p = WORK / src
        if p.exists():
            hashes[src] = sha1(p)
    m = {'nombre': ctx.name, 'fecha': datetime.datetime.now().isoformat(timespec='seconds'), 'git': git_info(),
         'python': sys.version.split()[0], 'argv': sys.argv[1:], 'dry_run': ctx.dry_run,
         'segundos': round(time.time() - t0, 1), 'fuentes': hashes,
         'reemplazos': {p: rel(f) for p, f in sorted(ctx.replacements.items())},
         'etapas': [{'id': s.id, 'estado': r.status, 'resumen': r.summary, 'segundos': round(r.seconds, 1),
                     'salidas': r.outputs, **({'datos': r.data} if r.data else {})} for s, r in results]}
    (ctx.dir / 'manifest.json').write_text(json.dumps(m, ensure_ascii=False, indent=1), encoding='utf-8')


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--list', action='store_true', help='mostrar las etapas y salir')
    ap.add_argument('--name', help='nombre base; la build sale como <N>_vNN (default: srwa_en_<fecha>_<commit>)')
    ap.add_argument('--no-version', action='store_true', help='usar --name tal cual, sin el sufijo _vNN automático')
    ap.add_argument('--dry-run', action='store_true', help='plan + validación, sin tocar archivos del juego')
    ap.add_argument('--only', metavar='E1,E2', help='solo estas etapas (+ preflight)')
    ap.add_argument('--skip', metavar='E1,E2', help='excluir estas etapas')
    ap.add_argument('--selftest', action='store_true', help='autopruebas de herramientas e integridad de volcados')
    ap.add_argument('--null', action='store_true', help='ISO sin reemplazos: tiene que ser idéntica a la original')
    ap.add_argument('--allow-text-errors', action='store_true', help='seguir con errores de texto (build de prueba)')
    ap.add_argument('--verify', choices=('completa', 'reemplazos', 'no'), default='completa',
                    help='comparar todos los archivos (default), solo los reemplazados, o nada')
    ap.add_argument('--strict', action='store_true', help='exigir git limpio (builds para publicar)')
    ap.add_argument('--overwrite', action='store_true',
                    help='reusar work/build/<N>/ si ya existe (borra sus files/, specs/, logs/ y selftest/)')
    ap.add_argument('--smoke', action='store_true', help='al final, rutas de regresión en el emulador')
    ap.add_argument('--routes', default='boot,prologo', help='rutas para --smoke (default: boot,prologo)')
    ap.add_argument('--ref', help='--smoke: carpeta de capturas de otra build para comparar cuadro a cuadro')
    ap.add_argument('--release', action='store_true', help='al final, parche xdelta3 contra la ISO original')
    args = ap.parse_args(argv)
    if args.list:
        list_stages()
        return 0
    stages = select(args)
    name = args.name or default_name(args.null)
    if args.name and not args.overwrite and not args.no_version:
        name = next_version_name(args.name)
    bdir = BUILD / name
    if bdir.exists() and any(bdir.iterdir()) and not args.overwrite:
        raise SystemExit(f'{rel(bdir)} ya existe: otro --name, o --overwrite para reusarla')
    if args.overwrite:
        for sub in ('files', 'specs', 'logs', 'selftest'):
            shutil.rmtree(bdir / sub, ignore_errors=True)
    bdir.mkdir(parents=True, exist_ok=True)
    ctx = Ctx(name, bdir, args, ids={s.id for s in stages})
    lock = None if args.dry_run else acquire_lock()
    t0 = time.time()
    print(f'Build {name} → {rel(bdir)}/' + ('   [dry-run: sin tocar archivos del juego]' if args.dry_run else ''))
    results, rc = [], 0
    for i, s in enumerate(stages, 1):
        t = time.time()
        try:
            r = s.run(ctx) if s.run else Result('pendiente', f'falta: {s.needs}')
        except StageError as e:
            r = Result('error', str(e))
        except Exception:                           # error de programación en una etapa: al log y a la pantalla
            ctx.logs.mkdir(parents=True, exist_ok=True)
            with open(ctx.logs / f'{s.id}.log', 'a', encoding='utf-8') as fh:
                fh.write(traceback.format_exc())
            r = Result('error', traceback.format_exc(limit=2).strip().splitlines()[-1] + f' (log: {s.id}.log)')
        r.seconds = time.time() - t
        results.append((s, r))
        head, *rest = (r.summary or '-').splitlines()
        print(f'[{i:2}/{len(stages)}] {s.id:11} {r.status:11} {r.seconds:6.1f} s  {head}')
        for ln in rest:
            print(f'{"":34}{ln}')
        if r.status == 'error':
            rc = 1
            break
    write_manifest(ctx, results, t0)
    pend = [s.id for s, r in results if r.status == 'pendiente']
    print(f'\nManifiesto: {rel(bdir / "manifest.json")}')
    if ctx.replacements:
        print(f'Reemplazos ({len(ctx.replacements)}): ' + ', '.join(sorted(ctx.replacements)))
    if pend:
        print(f'Pendientes ({len(pend)}): {", ".join(pend)} → sus archivos quedan en japonés (ver --list)')
    if rc == 0 and not args.dry_run and 'iso' in ctx.ids:
        cue = rel(ctx.bin.with_suffix('.cue'))
        print(f'Imagen: {cue}\nSiguiente (desde la raíz): work/tools/regresion.sh {cue} work/emu/shots/{name}   '
              '(checklist: work/notes/checklist_regresion.md)')
    if lock:
        lock.close()
    return rc


if __name__ == '__main__':
    sys.exit(main())
