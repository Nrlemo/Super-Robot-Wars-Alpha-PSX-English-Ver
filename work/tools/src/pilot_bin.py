"""UNITPRAM/PILOT.BIN: datos de pilotos (nombres, stats, espíritus, habilidades, terreno).

Formato (verificado 2026-09-27; ver notes/pilot_bin.md):
  u16 n (469) · u16 0 · n registros de 0x70 bytes (índice = id de piloto = bloque de BXCLIST)
  El juego copia el registro entero (0x70 bytes, basura incluida) a su tabla de pilotos en RAM
  (en el mapa: slots de 0xB0 desde 0x8015B264), así que los offsets valen igual en RAM.
Registro:
  +0x00 u16 id (0..468)
  +0x02 u8  tipos de unidad que puede pilotar (máscara; 1 = MS UC, 2 = MS de Gundam W, 4 = Mazinger,
            8/0x10 = Aura Battler, 0x20 = Valkyrie, 0x80 = hadas; 0 = capitanes/no transferibles)  [hipótesis]
  +0x03 u8  ? (1 en los pilotos de Gundam W, 2 en Daitarn)                                        [desconocido]
  +0x04     nombre completo: kana de medio ancho / SJIS / ASCII, NUL. Máx. 20 bytes + NUL (+0x04..+0x18).
            Tras el NUL hay basura de la herramienta de Banpresto ("67 00 58 a5 f7 bf 00 00 67 00 40"): no se lee.
  +0x19..+0x27  ceros; +0x21 y +0x25 = 0x08 en los 469 (constantes, no tocar)
  +0x28 u8  0xBE en los 469 (constante; NO es parte del nombre corto)
  +0x29     nombre corto (el que se usa como hablante en batalla, p. ej. "ﾀｼﾛ"), NUL. Máx. 12 bytes + NUL
            (+0x29..+0x35; +0x35 = 0 en los 469). Tras el NUL, basura ("22 8f f8 bf").
  +0x36 u8[6] stats: 格闘 melee, 射撃 ranged, 回避 evasion, 命中 accuracy, 反応 reaction, 技量 skill
  +0x3C u8[6] espíritus (id en el orden de OVL/PRM_GRP.BIN, ver SPIRITS; 0xFF = ninguno)
  +0x42 u8[6] nivel en que se aprende cada espíritu
  +0x48 3 × {u8 habilidad (SKILLS; 0xFF = ninguna), u8[9] nivel de piloto en que llega a L1..L9 (0xFF = nunca)}
  +0x66 u8  SP máximo base
  +0x67 u8  nivel de doble movimiento (99 = nunca)
  +0x68 u8  habilidades sin nivel (máscara): 1 = 底力, 2 = 天才, 4 = ガッツ, 8 = 野性化
  +0x69 u8  clase (máscara): 0x10 = original de Banpresto, 0x20 = genérico/soldado/IA, 0x40 = EVA (シンクロ率),
            0x80 = hada (チャム, ベル, エル)                                                           [hipótesis]
  +0x6A u8  personalidad (性格): 0 = débil, 1 = normal, 2 = fuerte, 3 = muy fuerte
  +0x6B u8  grupo (0 = ninguno; 1..23 crecen con el orden de las series: 1 = 0080, 2 = 0083, 3 = Z…)  [desconocido]
  +0x6C u8[4] terreno aire, tierra, mar, espacio (4 = A, 3 = B, 2 = C, 1 = D, 0 = -)
Glifos especiales: en el texto de 1 byte, un kana seguido de ﾞ (0xDE) o ﾟ (0xDF) se dibuja con OTRO glifo
(celda + 0x30 / + 0x40). Así se escriben "Mk-II" (ﾔﾟﾕﾟﾚﾟ), "ν" (ﾙﾟ), "ヱ" (ﾏﾟ)… Ver notes/pilot_bin.md.

Uso:
  pilot_bin.py dump [salida.jsonl]            → work/dump/pilot.jsonl (un piloto por línea)
  pilot_bin.py build entrada.jsonl salida.BIN → escribe "full_en"/"short_en" (si no están vacíos) con control
                                                de largo; los espacios pasan a 0xA0 como en snmsg.py
  pilot_bin.py selftest                        → build sin cambios == original
  pilot_bin.py fill [entrada.jsonl]            → llena full_en/short_en desde el glosario (completo: manual >
                                                correcciones > glosario; corto: manual > hablantes.csv) e informa
                                                en glossary/pilot_names_en.csv; falla si algo falta o no entra
  pilot_bin.py glyphs                          → notes/img/glifos_especiales.png (tabla de pares ﾞ/ﾟ)
"""
import json, os, struct, sys

from sjis_text import decode, encode

WORK = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
SRC = os.path.join(WORK, 'iso_jp', 'UNITPRAM', 'PILOT.BIN')
OUT = os.path.join(WORK, 'dump', 'pilot.jsonl')
RSIZE = 0x70
FULL, FULL_MAX = 0x04, 20         # nombre completo: 20 bytes + NUL (+0x04..+0x18)
SHORT, SHORT_MAX = 0x29, 12       # nombre corto: 12 bytes + NUL (+0x29..+0x35)
EN_SPACE = b'\xa0'                # espacio angosto del inglés (notes/fuente_en.md)

# OVL/PRM_GRP.BIN 0x528.. (id = posición)
SPIRITS = ['熱血', '魂', 'てかげん', '狙撃', 'ひらめき', '努力', '幸運', '集中', '必中', '鉄壁', '隠れ身', '加速',
           '覚醒', '激闘', '捨て身', 'かく乱', '挑発', '根性', 'ド根性', '気合', '信頼', '友情', '愛', '補給', '再動',
           '復活', '脱力', '戦慄', '自爆', '偵察', '激励', '大激励', '期待', '奇跡', '奇襲']
# OVL/PRM_GRP.BIN 0xE00.. (id = posición; en PILOT.BIN con niveles solo aparecen 0..5)
SKILLS = ['ニュータイプ', '強化人間', '聖戦士', '念動力', 'シールド防御', '切り払い', '底力', '天才', 'ガッツ', '野性化',
          '集中力', 'SP回復', '社長', '勇者', '王子', '王女', 'エースパイロット', '2回行動']
FLAG_SKILLS = {1: '底力', 2: '天才', 4: 'ガッツ', 8: '野性化'}
STATS = ['melee', 'ranged', 'evasion', 'accuracy', 'reaction', 'skill']
TERRAIN = '-DCBA'


def records(data):
    n = struct.unpack_from('<H', data, 0)[0]
    assert len(data) == 4 + n * RSIZE, 'tamaño inesperado'
    return [data[4 + i * RSIZE:4 + (i + 1) * RSIZE] for i in range(n)]


def cstr(b):
    return b.split(b'\0')[0]


def parse(r):
    p = {'id': struct.unpack_from('<H', r, 0)[0],
         'full': decode(cstr(r[FULL:FULL + FULL_MAX + 1])), 'full_len': len(cstr(r[FULL:])),
         'short': decode(cstr(r[SHORT:SHORT + SHORT_MAX + 1])), 'short_len': len(cstr(r[SHORT:])),
         'full_en': '', 'short_en': '',
         'unit_types': r[2], 'b3': r[3],
         'stats': dict(zip(STATS, r[0x36:0x3C])),
         'spirits': [[SPIRITS[s], lv] for s, lv in zip(r[0x3C:0x42], r[0x42:0x48]) if s != 0xFF],
         'skills': [], 'flag_skills': [v for k, v in FLAG_SKILLS.items() if r[0x68] & k],
         'sp': r[0x66], 'double_move': r[0x67], 'flags68': r[0x68], 'class69': r[0x69],
         'nature': r[0x6A], 'group': r[0x6B],
         'terrain': ''.join(TERRAIN[t] for t in r[0x6C:0x70])}
    for b in (0x48, 0x52, 0x5C):
        if r[b] != 0xFF:
            p['skills'].append([SKILLS[r[b]], [x if x != 0xFF else None for x in r[b + 1:b + 10]]])
    return p


def to_game(text):
    """Texto editable → bytes del juego (espacios → 0xA0)."""
    return encode(text).replace(b' ', EN_SPACE)


def put_name(rec, off, maxlen, text, label):
    raw = to_game(text)
    if len(raw) > maxlen:
        raise ValueError(f'{label}: {text!r} ocupa {len(raw)} bytes (máx. {maxlen})')
    rec[off:off + maxlen + 1] = raw + b'\0' * (maxlen + 1 - len(raw))   # limpia también la basura del campo


def build(data, entries):
    recs = [bytearray(r) for r in records(data)]
    errors = []
    for e in entries:
        rec = recs[e['id']]
        for key, off, mx in (('full_en', FULL, FULL_MAX), ('short_en', SHORT, SHORT_MAX)):
            if e.get(key):
                try:
                    put_name(rec, off, mx, e[key], f'piloto {e["id"]} {key}')
                except ValueError as ex:
                    errors.append(str(ex))
    if errors:
        raise SystemExit('\n'.join(errors))
    return data[:4] + b''.join(recs)


def load(path):
    return [json.loads(l) for l in open(path, encoding='utf-8') if l.strip()]


def dump(path=OUT):
    pilots = [parse(r) for r in records(open(SRC, 'rb').read())]
    with open(path, 'w', encoding='utf-8') as f:
        for p in pilots:
            f.write(json.dumps(p, ensure_ascii=False) + '\n')
    print(f'{len(pilots)} pilotos →', path)
    print('máx. nombre completo:', max(p['full_len'] for p in pilots), 'bytes; corto:', max(p['short_len'] for p in pilots))


def selftest():
    data = open(SRC, 'rb').read()
    same = build(data, [dict(p, full_en='', short_en='') for p in map(parse, records(data))]) == data
    # nombres de prueba al límite: deben entrar sin tocar nada fuera de los campos
    t = [{'id': 0, 'full_en': 'X' * FULL_MAX, 'short_en': 'Y' * SHORT_MAX}]
    new = build(data, t)
    r0, n0 = records(data)[0], records(new)[0]
    outside = [o for o in range(RSIZE) if r0[o] != n0[o] and not (FULL <= o <= FULL + FULL_MAX or SHORT <= o <= SHORT + SHORT_MAX)]
    try:
        build(data, [{'id': 0, 'full_en': 'X' * (FULL_MAX + 1)}]); overflow = False
    except SystemExit:
        overflow = True
    print('sin cambios idéntico:', same, '· bytes tocados fuera de los campos:', outside, '· rechaza 21 bytes:', overflow)
    return same and not outside and overflow


# ---------------------------------------------------------------- glifos especiales (8FONT_R.TIM)

def cell_index(byte, mark=None):
    """Índice de celda (fila = i >> 4, columna = 16 + (i & 15)) de FUN_8001885C, con el corrimiento de ﾞ/ﾟ
    que aplica FUN_80018CC4 (sprite +0xD += 0x30 / 0x40 = 3 / 4 filas de 16 px)."""
    i = (byte - 0x40 if byte >= 0xA0 else byte - 0x20) & 0xFF
    return i + {None: 0, 0xDE: 0x30, 0xDF: 0x40}[mark]


def glyph_cells(raw):
    """Secuencia de índices de celda que dibuja el juego para una cadena de 1 byte (sin SJIS)."""
    out, i = [], 0
    while i < len(raw):
        b = raw[i]
        if 0x81 <= b <= 0x9F or 0xE0 <= b <= 0xFC:
            out.append(None); i += 2; continue          # SJIS: glifo de 12 px (12F.DAT), no se dibuja aquí
        mark = raw[i + 1] if i + 1 < len(raw) and raw[i + 1] in (0xDE, 0xDF) else None
        out.append(cell_index(b, mark)); i += 2 if mark else 1
    return out


STANDARD_DE = set(range(0xB6, 0xC5)) | set(range(0xCA, 0xCF)) | {0xB3}   # ｶﾞ..ﾄﾞ, ﾊﾞ..ﾎﾞ, ｳﾞ
STANDARD_DF = set(range(0xCA, 0xCF))                                     # ﾊﾟ..ﾎﾟ


def special_pairs(raw):
    """Pares kana+ﾞ/ﾟ que NO son un kana con (han)dakuten normal."""
    out, i = [], 0
    while i < len(raw):
        b = raw[i]
        if 0x81 <= b <= 0x9F or 0xE0 <= b <= 0xFC:
            i += 2; continue
        if i + 1 < len(raw) and raw[i + 1] in (0xDE, 0xDF):
            m = raw[i + 1]
            if not ((m == 0xDE and b in STANDARD_DE) or (m == 0xDF and b in STANDARD_DF)):
                out.append(raw[i:i + 2])
            i += 2; continue
        i += 1
    return out


def glyphs(png=os.path.join(WORK, 'notes', 'img', 'glifos_especiales.png')):
    import numpy as np
    from PIL import Image, ImageDraw, ImageFont
    import robot_raf
    from tim import read_tim
    _, _, idx = read_tim(open(os.path.join(WORK, 'iso_jp', 'FONTWIN', '8FONT_R.TIM'), 'rb').read())
    pal = np.array([(255, 255, 255), (0, 0, 0), (110, 110, 110), (170, 170, 170)] + [(220, 40, 40)] * 12, np.uint8)
    S = 4

    def cell_img(i):
        r, c = i >> 4, 16 + (i & 15)
        a = pal[idx[r * 16:(r + 1) * 16, c * 8:(c + 1) * 8]]
        return Image.fromarray(a).resize((8 * S, 16 * S), Image.NEAREST)

    def text_img(raw):
        cells = [c for c in glyph_cells(raw) if c is not None]
        im = Image.new('RGB', (max(1, len(cells)) * 8 * S, 16 * S), 'white')
        for k, c in enumerate(cells):
            im.paste(cell_img(c), (k * 8 * S, 0))
        return im

    # pares especiales en ROBOT.RAF (unidades y armas) y PILOT.BIN
    occ = {}
    for i, _, rec in robot_raf.entries(open(robot_raf.SRC, 'rb').read()):
        names = [rec[0:0x20].split(b'\0')[0]]
        for k in range(16):
            w = rec[robot_raf.W0 + k * robot_raf.WSIZE:robot_raf.W0 + (k + 1) * robot_raf.WSIZE]
            if len(w) < robot_raf.WSIZE or w[0] != k or not w[8]:
                break
            names.append(w[8:0x1C].split(b'\0')[0])
        for n in names:
            for p in special_pairs(n):
                occ.setdefault(p, []).append(n)
    for r in records(open(SRC, 'rb').read()):
        for n in (cstr(r[FULL:]), cstr(r[SHORT:])):
            for p in special_pairs(n):
                occ.setdefault(p, []).append(n)

    import unicodedata

    def load_font(paths):
        for f in paths:
            if os.path.exists(f):
                return ImageFont.truetype(f, 18)
        return ImageFont.load_default()
    latin = load_font(['/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'])
    cjk = load_font(['/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',
                     '/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf'])

    class Draw:
        """Texto mixto: ASCII con DejaVu, el resto (kana pasados a ancho completo) con la fuente CJK."""
        def __init__(self, img):
            self.d = ImageDraw.Draw(img)

        def text(self, xy, t, fill='black', font=None):
            x, y = xy
            for ch in unicodedata.normalize('NFKC', t):
                f = latin if ord(ch) < 0x250 else cjk
                self.d.text((x, y), ch, fill=fill, font=f)
                x += f.getlength(ch)
    font = None
    samples = sorted({n for v in occ.values() for n in v}, key=lambda n: n.decode('cp932', 'replace'))
    rows = [(p, cell_index(p[0], p[1])) for p in sorted(occ)]
    H = 16 * S + 12
    W = 1100
    im = Image.new('RGB', (W, 40 + len(rows) * H + 30 + len(samples) * H), 'white')
    d = Draw(im)
    d.text((10, 8), 'Par (bytes)  -> celda 8FONT_R  -> glifo                      usos (ROBOT.RAF / PILOT.BIN)', fill='black', font=font)
    y = 40
    for p, ci in rows:
        d.text((10, y + 20), f'{p.decode("cp932")}  {p.hex()}', fill='black', font=font)
        d.text((190, y + 20), f'fila {ci >> 4} col {16 + (ci & 15)}', fill='blue', font=font)
        im.paste(cell_img(ci), (330, y))
        d.text((380, y + 20), f'{len(occ[p])} usos', fill='black', font=font)
        y += H
    d.text((10, y + 4), 'Cadenas completas tal como las arma FUN_80018CC4 (8 px por glifo; lo SJIS, p. ej. 装着型, va por 12F.DAT y no se dibuja aquí):', fill='black', font=font)
    y += 30
    for n in samples:
        d.text((10, y + 20), n.decode('cp932', 'replace'), fill='black', font=font)
        im.paste(text_img(n), (330, y))
        y += H
    im.save(png)
    print('→', png)
    for p, ci in rows:
        print(p.decode('cp932'), p.hex(), 'celda', hex(ci), len(occ[p]), 'usos:',
              sorted({n.decode('cp932', 'replace') for n in occ[p]}))


GLOSSARY = os.path.join(WORK, 'glossary', 'glossary.csv')
MANUAL = os.path.join(WORK, 'glossary', 'pilot_names_manual.csv')     # decisiones propias de PILOT.BIN (ganan)
REPORT = os.path.join(WORK, 'glossary', 'pilot_names_en.csv')
REF = os.path.join(WORK, '..', 'traduccion', 'referencia')
CORRECTIONS = os.path.join(REF, 'correcciones.csv')
SPEAKERS = os.path.join(REF, 'hablantes.csv')


def norm(s):
    """Misma forma comparable que glossary_build.norm."""
    import re, unicodedata
    s = unicodedata.normalize('NFKC', s)
    s = re.sub(r'(?<=[ァ-ヴー])-', 'ー', s).replace('=', '・').replace('＝', '・')
    return re.sub(r'\s+', '', s)


def english_names():
    """({jp completo: (en, fuente)}, {jp corto: (en, fuente)}) con claves norm(), en orden de prioridad."""
    import csv
    rd = lambda path: list(csv.DictReader(open(path, encoding='utf-8')))
    full, short = {}, {}
    for r in rd(MANUAL):
        (full if r['campo'] == 'full' else short)[norm(r['jp'])] = (r['en'], 'manual')
    for r in rd(CORRECTIONS):
        if r['category'] == 'pilot':
            full.setdefault(norm(r['jp']), (r['en_corregido'], 'correcciones'))
    for r in rd(GLOSSARY):
        if r['category'] == 'pilot':
            for k in (r['jp'], r['jp_game']):
                if k:
                    full.setdefault(norm(k), (r['en_final'], 'glosario'))
    for r in rd(SPEAKERS):
        short.setdefault(norm(r['jp']), (r['en'], 'hablantes'))
    return full, short


def fill(path=OUT):
    """full_en/short_en de cada piloto; se busca con y sin ・ (el juego no siempre separa nombre y apellido)."""
    import csv
    from collections import Counter
    full, short = english_names()
    look = lambda d, jp: d.get(norm(jp)) or d.get(norm(jp).replace('・', ''))
    pilots, rows, problems = load(path), [], []
    for p in pilots:
        f, s = look(full, p['full']), look(short, p['short'])
        for key, hit, jp, mx in (('full_en', f, p['full'], FULL_MAX), ('short_en', s, p['short'], SHORT_MAX)):
            if not hit:
                problems.append(f'piloto {p["id"]} {key}: {jp} sin traducción')
            elif len(to_game(hit[0])) > mx:
                problems.append(f'piloto {p["id"]} {key}: {hit[0]!r} ocupa {len(to_game(hit[0]))} bytes (máx. {mx})')
        p['full_en'] = f[0] if f else ''
        p['short_en'] = s[0] if s else ''
        rows.append([p['id'], p['full'], p['full_en'], f[1] if f else '', p['short'], p['short_en'], s[1] if s else ''])
    with open(REPORT, 'w', encoding='utf-8', newline='') as fh:
        w = csv.writer(fh)
        w.writerow(['id', 'full_jp', 'full_en', 'full_fuente', 'short_jp', 'short_en', 'short_fuente'])
        w.writerows(rows)
    with open(path, 'w', encoding='utf-8') as fh:
        for p in pilots:
            fh.write(json.dumps(p, ensure_ascii=False) + '\n')
    print(f'{len(pilots)} pilotos → {path}; informe → {REPORT}')
    print('completo:', dict(Counter(r[3] for r in rows)), '· corto:', dict(Counter(r[6] for r in rows)))
    if problems:
        raise SystemExit('ERROR ' + '\nERROR '.join(problems))


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else 'dump'
    if cmd == 'dump':
        dump(sys.argv[2] if len(sys.argv) > 2 else OUT)
    elif cmd == 'build':
        data = build(open(SRC, 'rb').read(), load(sys.argv[2]))
        open(sys.argv[3], 'wb').write(data)
        print('→', sys.argv[3])
    elif cmd == 'fill':
        fill(sys.argv[2] if len(sys.argv) > 2 else OUT)
    elif cmd == 'selftest':
        sys.exit(0 if selftest() else 1)
    elif cmd == 'glyphs':
        glyphs(*sys.argv[2:3])
    else:
        print(__doc__)


if __name__ == '__main__':
    main()
