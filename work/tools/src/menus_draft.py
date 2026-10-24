"""Borrador en inglés de los textos de menú de los overlays: translation/menus_map.txt → translation/menus_en.jsonl.

Cruza cada string de dump/ovl_strings.jsonl (overlays IMIS PRM SNMP BTL SNDU TITL COMM ENTR) con el mapa JP→EN
(una traducción por texto japonés único) y calcula, con el largo real en bytes (cp932), si entra en el lugar.
- fits = el inglés (en) entra in situ: len(en) + 1 (NUL) <= room.
- en_short solo se escribe cuando en no entra; fits_short dice si la forma corta entra en ESE lugar.
- plan (criterio 2026-09-28: primero reubicar, acortar solo si no se puede):
    in situ              en entra en su lugar
    reubicar             en no entra y hay puntero (ptr): se mueve y se corrige la palabra
    reubicar (código)    solo referencias lui/addiu: reubicable cuando ovl_patch.py lo soporte
    corta                sin referencia directa: no se puede mover, va en_short in situ
    sin solución         sin referencia y la forma corta tampoco entra
  En PRM, SNMP y TITL (zonas llenas) "reubicar" significa reempaquetar el bloque de strings.
- Los strings del dump que no están en el mapa se ignoran (ruido de código, glifos especiales, letras de canciones).
Valida que los especificadores de formato (%d, %2d, %s, %c…) sean los mismos en jp, en y en_short.
Uso: menus_draft.py [--report]
"""
import collections, json, os, re, sys

WORK = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
FILES = ('IMIS', 'PRM', 'SNMP', 'BTL', 'SNDU', 'TITL', 'COMM', 'ENTR', 'SNDM')
FMT = re.compile(r'%[-0-9]*[dsc]')
# strings que el volcado corta mal (un byte previo se leyó como primer byte SJIS): (archivo, jp mal leído) → bytes a saltar
MISALIGNED = {('IMIS', 'I￠s絶！台湾大地震ｽﾍﾟｼｬﾙ！'): 2, ('IMIS', '卒ﾝﾀｰﾐｯｼｮﾝ'): 1, ('PRM', '#(潟熱血'): 4, ('ENTR', 'ﾈこA型'): 3,
              ('PRM', 'ｨｂﾍずす'): 2,   # は ず す de la pantalla Parts (#264): 'a8 82' previos son basura
              ('SNDM', 'ﾌＡ愛称'): 3}   # rótulo 愛称 de la ficha del diccionario (#281): 'cc 82 60' previos son basura
# strings que el volcado no extrajo (pegados a una tabla de punteros): se agregan a mano con sus referencias
# (#276: el 男 de la ficha de ENTR; al cambiar de cara dos veces el sexo se redibuja desde este y salía el kanji)
EXTRA = [{'file': 'ENTR', 'off': 0x80114C94 - 0x8011308C, 'addr': '0x80114c94', 'jp': '男', 'bytes': 2, 'room': 3,
          'refs': ['code@0xbb7c', 'ptr@0x10748']}]
# Demo Select (títulos de los videos): tabla de 15 casilleros de 0x30 bytes en SNDM 0x800F1D50, indexada (solo el 1.º tiene
# referencia directa y salía del volcado); se agregan los otros 14 in situ (47 bytes + NUL).
EXTRA += [{'file': 'SNDM', 'off': 0x800F1D50 + 0x30 * i - 0x800D61D8, 'addr': f'{0x800F1D50 + 0x30 * i:#x}', 'jp': JP, 'bytes': len(JP.encode('cp932')),
           'room': 47, 'refs': []} for i, JP in enumerate(['ﾏｼﾞﾝｶﾞｰZ発進', 'ﾁｪﾝｼﾞ! ｹﾞｯﾀｰﾛﾎﾞ', 'ﾚｯﾂ･ｺﾝﾊﾞｲﾝ', '目覚めよ、勇者ﾗｲﾃﾞｨｰﾝ', 'EVA初号機、ﾘﾌﾄ･ｵﾌ', '赤い稲妻', 'ｹﾞｯﾀｰﾛﾎﾞG登場', 'いでよ神の戦士', '偉大な勇者', 'ﾚｯﾂ･ﾎﾞﾙﾄｲﾝ', '真･ｹﾞｯﾀｰ現る', '龍虎合体', 'ｳﾞｧﾘｱﾌﾞﾙ･ﾌｫｰﾒｰｼｮﾝ', '魔神皇帝の目覚め', '炎となりて']) if i > 0]
# referencias que el volcado no le asignó a un string corregido por MISALIGNED (#281: tabla de rótulos de la ficha)
MISALIGNED_REFS = {('SNDM', 'ﾌＡ愛称'): ['ptr@0x1c504']}


def load_map(path):
    m = {}
    for n, line in enumerate(open(path, encoding='utf-8'), 1):
        line = line.rstrip('\n')
        if not line.strip() or line.startswith('#'):
            continue
        parts = line.split('||')
        if len(parts) < 2:
            raise SystemExit(f'{path}:{n}: línea sin "||"')
        # el primer campo conserva los espacios iniciales (huecos de ícono); el resto pierde el espacio del separador
        f = [parts[0].rstrip()] + [p[1:].rstrip() if p.startswith(' ') else p.rstrip() for p in parts[1:]]
        f += [''] * (4 - len(f))
        jp, en, short, notes = f[0], f[1], f[2], '||'.join(f[3:]).strip()
        jp, en, short = (x.replace('\\n', '\n').replace('\\t', '\t').replace('\\s', ' ') for x in (jp, en, short))
        if jp in m:
            raise SystemExit(f'{path}:{n}: {jp!r} repetido')
        m[jp] = (en, short, notes, n)
    return m


OVERRIDE = re.compile(r'^(.*)@([A-Z]+):(0x[0-9a-f]+)$')


def map_key(m, d):
    """Clave del mapa para una fila del volcado: primero la entrada por dirección (`jp@ARCHIVO:0xdir`), luego el texto."""
    k = f"{d['jp']}@{d['file']}:{d['addr']}"
    return k if k in m else d['jp'] if d['jp'] in m else None


def blen(s):
    return len(s.encode('cp932'))


def check(jp, en, short, n):
    errs = []
    for s in (en, short):
        if not s:
            continue
        try:
            s.encode('cp932')
        except UnicodeEncodeError as e:
            errs.append(f'no codificable en cp932: {s!r} ({e})')
        if sorted(FMT.findall(s)) != sorted(FMT.findall(jp)):
            errs.append(f'especificadores distintos: {jp!r} {FMT.findall(jp)} vs {s!r} {FMT.findall(s)}')
    if not en:
        errs.append('en vacío')
    return [f'línea {n}: {e}' for e in errs]


def main():
    m = load_map(os.path.join(WORK, 'translation', 'menus_map.txt'))
    errs = [e for jp, (en, sh, _, n) in m.items() for e in check(OVERRIDE.sub(r'\1', jp), en, sh, n)]
    if errs:
        raise SystemExit('\n'.join(errs))
    used, out = set(), []
    rows = [json.loads(line) for line in open(os.path.join(WORK, 'dump', 'ovl_strings.jsonl'), encoding='utf-8')]
    for d in rows + EXTRA:
        skip = MISALIGNED.get((d['file'], d['jp']))
        if skip:
            raw = d['jp'].encode('cp932')
            d = dict(d, addr=f"{int(d['addr'], 16) + skip:#x}", jp=raw[skip:].decode('cp932'), room=d['room'] - skip,
                     refs=MISALIGNED_REFS.get((d['file'], d['jp']), []), derived=True)
        key = map_key(m, d)
        if d['file'] not in FILES or key is None:
            continue
        en, short, notes, _ = m[key]
        used.add(key)
        room = d['room']
        fits = blen(en) + 1 <= room
        row = {'file': d['file'], 'addr': d['addr'], 'jp': d['jp'], 'en': en, 'en_short': '', 'room': room,
               'fits': fits, 'fits_short': None, 'refs': d['refs'], 'notes': notes}
        ptr = any(r.startswith('ptr') for r in d['refs'])
        row['plan'] = ('in situ' if fits else 'reubicar' if ptr else 'reubicar (código)' if d['refs']
                       else 'corta' if short and blen(short) + 1 <= room else 'sin solución')
        if d.get('derived'):
            extra = 'dirección corregida (el volcado leyó mal el inicio); referencias sin verificar'
            row['notes'] = f'{notes}; {extra}' if notes else extra
        if not fits:
            row['en_short'] = short
            row['fits_short'] = bool(short) and blen(short) + 1 <= room
            if not row['fits_short'] and row['plan'] == 'sin solución':
                extra = 'no entra ni la forma corta y no tiene referencia directa'
                row['notes'] = f"{row['notes']}; {extra}" if row['notes'] else extra
        out.append(row)
    dst = os.path.join(WORK, 'translation', 'menus_en.jsonl')
    with open(dst, 'w', encoding='utf-8') as fo:
        for r in out:
            fo.write(json.dumps(r, ensure_ascii=False) + '\n')
    plans = ('in situ', 'reubicar', 'reubicar (código)', 'corta', 'sin solución')
    c = collections.Counter((r['file'], r['plan']) for r in out)
    print(f'{len(out)} strings ({len(used)} textos únicos) → {dst}')
    print('        filas  ' + '  '.join(plans))
    for f in FILES:
        print(f"  {f:5} {sum(c[(f, p)] for p in plans):5}  " + '  '.join(f'{c[(f, p)]:{len(p)}}' for p in plans))
    unused = [jp for jp in m if jp not in used]
    if unused:
        print('entradas del mapa sin uso:', unused)
    if '--report' in sys.argv:
        for r in out:
            if r['plan'] in ('corta', 'sin solución') or (r['plan'] == 'reubicar (código)'):
                print(f"  {r['plan'].upper()} {r['file']} {r['addr']} room={r['room']} refs={len(r['refs'])} "
                      f"{r['jp']!r} → {r['en']!r} / {r['en_short']!r}")


if __name__ == '__main__':
    main()
