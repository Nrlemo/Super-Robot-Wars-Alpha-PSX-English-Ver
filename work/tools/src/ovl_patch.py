"""Reemplaza textos de los overlays por inglés: in situ si entra, si no los **reubica** (tabla de punteros o par
lui/addiu) dentro de un **pool de espacio libre** y corrige las referencias (reempaquetado; ver notes/menus.md).

Entrada:
  - translation/menus_en.jsonl (una fila por string: file, addr, jp, en, en_short) — modo normal, o
  - JSON {"file": "IMIS", "texts": {"0x800d7f40": "Unit Stats", ...}} (formato de la primera prueba).
Reglas (2026-09-28):
  - Lugar de un string: in situ = todos los ceros tras su NUL (campos de ancho fijo, como en la 1.ª prueba); para el
    pool, solo hasta la alineación a 4 (más allá podría haber variables en cero). Nunca más allá del próximo destino de
    una referencia (hay punteros a ceros de relleno en PRM = strings vacíos/datos). Ver work/notes/menus.md.
  - Reubicable = tiene referencias y todas son 'ptr' (palabra de 32 bits) o 'code' (lui + addiu/ori). Los strings que
    son cola de otro (byte anterior ≠ NUL, "fragmentos") nunca se reubican ni aportan espacio.
  - Pool = lugar de los strings reubicados + sobrante de los reemplazados in situ + cola de la zona (si su límite es
    conocido: zonas PRM/A/B; la C no). Asignación de mayor a menor, primer hueco.
  - Referencias 'code': **no se toca el lui** (puede compartirse con otras instrucciones); el texto se ubica en un hueco
    con el mismo %hi y solo se reescribe el addiu/ori.
  - Preferencia de texto: en (in situ) → en (reubicado) → en_short (in situ) → en_short (reubicado) → sin cambio.
Espacio inglés = 0xA0 (notes/fuente_en.md).
Uso:
  ovl_patch.py --jsonl translation/menus_en.jsonl [--files IMIS,PRM] [--out build/menus]   → <out>/<X>_GRP.BIN + report
  ovl_patch.py cambios.json salida.BIN                                                       (formato viejo)
"""
import argparse, collections, csv, json, os, struct, sys
from ovl_strings import BASES, WORK

# tamaño máximo por zona (hasta donde empieza la zona siguiente); la zona C no tiene límite conocido
ZONE_MAX = {0x800A8920: 0x800D61D8 - 0x800A8920, 0x800D61D8: 0x800FF190 - 0x800D61D8,
            0x800FF190: 0x8011308C - 0x800FF190}


def encode(s):
    """Inglés → bytes (espacio = 0xA0). '{blank}' = string vacío (p. ej. el contador 機 de "36機")."""
    if s == '{blank}':
        return b''
    return s.encode('cp932').replace(b' ', b'\xa0')


SOFT_MAX = 64   # bytes máximos entre el lui y un addiu/ori alcanzado tras un salto


def scan_refs(d, base):
    """dirección → [(tipo, offset, extra)]: ('ptr', off, None) o ('code', off_addiu, (op, off_lui))."""
    out = collections.defaultdict(list)
    n = len(d) // 4
    ws = struct.unpack_from('<%dI' % n, d, 0)
    hi = {}
    soft = {}   # lui que sobreviven a j/jr: el addiu puede estar en otra rama (p. ej. delay slot tras un beq)
    for i, w in enumerate(ws):
        if 0x80010000 <= w < 0x80200000:
            out[w].append(('ptr', i * 4, None))
        op, rs, rt, imm = w >> 26, (w >> 21) & 31, (w >> 16) & 31, w & 0xFFFF
        if op == 0x0F:
            hi[rt] = soft[rt] = (imm << 16, i * 4)
        elif op in (0x09, 0x0D) and rs in hi:
            lo = imm - 0x10000 if (op == 0x09 and imm & 0x8000) else imm
            v = (hi[rs][0] + lo) & 0xFFFFFFFF
            out[v].append(('code', i * 4, (op, hi[rs][1])))
        elif op in (0x09, 0x0D) and rs in soft and i * 4 - soft[rs][1] <= SOFT_MAX:
            lo = imm - 0x10000 if (op == 0x09 and imm & 0x8000) else imm
            v = (soft[rs][0] + lo) & 0xFFFFFFFF
            out[v].append(('code', i * 4, (op, soft[rs][1])))
        if op in (0x02, 0x03) or (op == 0 and (w & 0x3F) in (8, 9)):   # j/jal/jr/jalr: los lui dejan de valer
            hi = {}
    return out


def hi_window(addr, op):
    """Rango [lo, hi) de direcciones alcanzables cambiando solo el inmediato (mismo lui)."""
    if op == 0x09:   # addiu: inmediato con signo
        h = ((addr + 0x8000) >> 16) << 16
        return h - 0x8000, h + 0x8000
    h = (addr >> 16) << 16   # ori: sin signo
    return h, h + 0x10000


class Pool:
    def __init__(self):
        self.free = []   # [(inicio, fin)] en direcciones

    def add(self, a, b):
        if b > a:
            self.free.append((a, b))

    def normalize(self):
        self.free.sort()
        out = []
        for a, b in self.free:
            if out and a <= out[-1][1]:
                out[-1] = (out[-1][0], max(out[-1][1], b))
            else:
                out.append((a, b))
        self.free = out

    def take(self, size, lo=0, hi=1 << 33):
        for k, (a, b) in enumerate(self.free):
            s = max(a, lo)
            if s + size <= min(b, hi):
                self.free[k:k + 1] = [x for x in ((a, s), (s + size, b)) if x[1] > x[0]]
                return s
        return None

    def total(self):
        return sum(b - a for a, b in self.free)


# strings alineados que siguen a una tabla de punteros: el byte anterior (0x80 del puntero) no es cola de texto
NOT_FRAG = {('ENTR', 0x80114C94)}   # 男 de la ficha (#276; fila agregada en menus_draft.EXTRA)
# (el 愛称 de la ficha del diccionario, SNDM 0x800D9410, queda como fragmento a propósito: va "Nick" in situ, porque
#  "Nickname" pisa la columna de valores, que está en x fija; #281)


def patch_overlay(name, rows, d=None):
    """rows: [{'addr', 'jp', 'en', 'en_short'}] → (bytes, informe[dict])."""
    path = os.path.join(WORK, 'iso_jp', 'OVL', f'{name}_GRP.BIN')
    orig = bytes(open(path, 'rb').read()) if d is None else bytes(d)
    base = BASES[name]
    R = scan_refs(orig, base)
    targets = sorted(R)

    info = {}
    for r in rows:
        addr = int(r['addr'], 16)
        off = addr - base
        n = len(orig[off:].split(b'\0')[0])
        full = off + n + 1                             # room completo: todos los ceros (campos de ancho fijo)
        while full < len(orig) and orig[full] == 0:
            full += 1
        for t in targets:                              # nunca pisar un destino de referencia
            if addr + n < t < base + full:
                full = t - base
                break
        end = off + n + 1                              # para el pool: solo hasta la alineación a 4
        while end < full and end % 4:
            end += 1
        refs = R.get(addr, [])
        info[addr] = dict(row=r, off=off, n=n, slot=full - off, pool_slot=end - off, refs=refs,
                          frag=off > 0 and orig[off - 1] != 0 and (name, addr) not in NOT_FRAG,
                          movable=bool(refs) and not (off > 0 and orig[off - 1] != 0 and (name, addr) not in NOT_FRAG))

    def window(i):
        lo, hi = 0, 1 << 33
        for k, o, extra in i['refs']:
            if k == 'code':
                a, b = hi_window(base + i['off'], extra[0])
                lo, hi = max(lo, a), min(hi, b)
        return lo, hi

    forced_short = set()   # textos que no consiguieron lugar con 'en' → se prueba 'en_short'
    forced_keep = set()    # sin lugar ni con la forma corta → quedan en japonés
    for _ in range(20):
        d = bytearray(orig)
        pool = Pool()
        plan = {}
        for addr, i in info.items():
            r = i['row']
            cands = [] if addr in forced_keep else [x for x in (
                (r.get('en') if addr not in forced_short else None), r.get('en_short')) if x]
            choice = None
            for txt in cands:
                b = encode(txt) + b'\0'
                if len(b) <= i['slot']:
                    choice = ('in situ', txt, b)
                    break
                if i['movable']:
                    choice = ('reubicado', txt, b)
                    break
            plan[addr] = choice
            if choice is None:
                continue
            if choice[0] == 'in situ':
                pool.add(addr + len(choice[2]), addr + i['pool_slot'])
            else:
                pool.add(addr, addr + i['pool_slot'])
        lim = ZONE_MAX.get(base)
        tail = (len(orig) + 3) & ~3
        if lim:
            pool.add(base + tail, base + lim)
        pool.normalize()
        pool_before = pool.total()
        # asignar: primero los más restringidos (con code) y los más largos
        moves = sorted((a for a, c in plan.items() if c and c[0] == 'reubicado'),
                       key=lambda a: (window(info[a]) == (0, 1 << 33), -len(plan[a][2])))
        failed = []
        where = {}
        for a in moves:
            lo, hi = window(info[a])
            s = pool.take(len(plan[a][2]), lo, hi)
            if s is None:
                failed.append(a)
            else:
                where[a] = s
        if not failed:
            break
        for a in failed:
            (forced_keep if a in forced_short or not info[a]['row'].get('en_short') else forced_short).add(a)
    else:
        raise SystemExit(f'{name}: la asignación no converge')

    # escribir: primero borrar los slots de los reubicados, después in situ, después reubicados
    for a, c in plan.items():
        if c and c[0] == 'reubicado':
            o = info[a]['off']
            d[o:o + info[a]['pool_slot']] = b'\0' * info[a]['pool_slot']
    for a, c in plan.items():
        if c and c[0] == 'in situ':
            o, sl = info[a]['off'], info[a]['slot']
            d[o:o + sl] = c[2] + b'\0' * (sl - len(c[2]))
    grow = 0
    for a, s in where.items():
        b = plan[a][2]
        o = s - base
        if o + len(b) > len(d):
            d += b'\0' * (o + len(b) - len(d))
        d[o:o + len(b)] = b
        for k, ro, extra in info[a]['refs']:
            if k == 'ptr':
                struct.pack_into('<I', d, ro, s)
            else:
                w = struct.unpack_from('<I', d, ro)[0]
                lo16 = (s - (((s + 0x8000) >> 16) << 16)) & 0xFFFF if extra[0] == 0x09 else s & 0xFFFF
                struct.pack_into('<I', d, ro, (w & 0xFFFF0000) | lo16)
    while len(d) % 4:
        d.append(0)
    lim = ZONE_MAX.get(base)
    if lim and len(d) > lim:
        raise SystemExit(f'{name}: {len(d)} bytes supera el máximo de la zona ({lim})')

    report = []
    for a, i in info.items():
        c = plan[a]
        r = i['row']
        how = 'sin cambio' if c is None else c[0]
        report.append({'file': name, 'addr': r['addr'], 'jp': r.get('jp', ''), 'used': c[1] if c else '',
                       'short': bool(c and c[1] != r.get('en')), 'how': how,
                       'new': f'{where[a]:#x}' if a in where else '', 'refs': len(i['refs']),
                       'slot': i['slot'], 'frag': i['frag']})
    stats = dict(file=name, size_before=len(orig), size_after=len(d), pool=pool_before,
                 pool_left=pool.total())
    return bytes(d), report, stats


def verify(name, out, report):
    """Relee el overlay parcheado: cada texto usado debe leerse en su dirección final y cada referencia debe apuntarla."""
    base = BASES[name]
    R = scan_refs(out, base)
    bad = []
    for r in report:
        if r['how'] == 'sin cambio':
            continue
        a = int(r['new'] or r['addr'], 16)
        got = out[a - base:].split(b'\0')[0]
        if got != encode(r['used']):
            bad.append((r['addr'], 'texto', got[:20]))
        if r['new'] and len(R.get(a, [])) != r['refs']:
            bad.append((r['addr'], 'refs', len(R.get(a, [])), r['refs']))
    return bad


def main():
    if len(sys.argv) == 3 and sys.argv[1].endswith('.json'):   # formato viejo
        spec = json.load(open(sys.argv[1], encoding='utf-8'))
        rows = [{'addr': a, 'en': t} for a, t in spec['texts'].items()]
        out, rep, st = patch_overlay(spec['file'], rows)
        open(sys.argv[2], 'wb').write(out)
        for r in rep:
            print(r['addr'], repr(r['used']), r['how'], r['new'])
        print(st)
        return
    ap = argparse.ArgumentParser()
    ap.add_argument('--jsonl', default=os.path.join(WORK, 'translation', 'menus_en.jsonl'))
    ap.add_argument('--files', default='')
    ap.add_argument('--out', default=os.path.join(WORK, 'build', 'menus'))
    a = ap.parse_args()
    rows = collections.defaultdict(list)
    for line in open(a.jsonl, encoding='utf-8'):
        if line.strip():
            r = json.loads(line)
            if r.get('en') or r.get('en_short'):
                rows[r['file']].append(r)
    files = [f for f in a.files.split(',') if f] or sorted(rows)
    os.makedirs(a.out, exist_ok=True)
    allrep, allstats, nbad = [], {}, 0
    print(f'{"ovl":5} {"antes":>7} {"después":>7} {"pool":>6} {"sobra":>6}  in situ  reubic.  corta  sin cambio  errores')
    for f in files:
        out, rep, st = patch_overlay(f, rows[f])
        bad = verify(f, out, rep)
        open(os.path.join(a.out, f'{f}_GRP.BIN'), 'wb').write(out)
        c = collections.Counter(r['how'] for r in rep)
        print(f'{f:5} {st["size_before"]:7} {st["size_after"]:7} {st["pool"]:6} {st["pool_left"]:6}  '
              f'{c["in situ"]:7}  {c["reubicado"]:7}  {sum(r["short"] for r in rep):5}  {c["sin cambio"]:10}  {len(bad)}')
        for b in bad[:5]:
            print('   ERROR', b)
        nbad += len(bad)
        allstats[f] = {**st, **{k: c[k] for k in ('in situ', 'reubicado', 'sin cambio')},
                       'corta': sum(r['short'] for r in rep), 'errores': len(bad)}
        allrep += rep
    with open(os.path.join(a.out, 'report.csv'), 'w', encoding='utf-8', newline='') as fh:
        w = csv.DictWriter(fh, list(allrep[0]))
        w.writeheader()
        w.writerows(allrep)
    with open(os.path.join(a.out, 'stats.json'), 'w', encoding='utf-8') as fh:
        json.dump(allstats, fh, ensure_ascii=False, indent=1)
    print('informe →', os.path.join(a.out, 'report.csv'))
    if nbad:
        sys.exit(f'{nbad} errores de verificación')


if __name__ == '__main__':
    main()
