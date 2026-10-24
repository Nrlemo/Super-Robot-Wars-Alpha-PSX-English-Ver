"""Posiciones de texto en menús y títulos para el ancho real del inglés (#66).

Formato (verificado 2026-10-03; ver notes/menus.md, "Posiciones de texto"):
  SNMP_GRP (carga en 0x800D61D8) tiene una tabla de layouts de pantalla en 0x800FCF2C (archivo +0x26D54): registros
  de 12 bytes = u8 cantidad de posiciones · u8 cantidad de textos fijos · 2 bytes · puntero a posiciones (int16 x, y;
  relativas a la ventana) · puntero a la tabla de punteros de texto. Los primeros `textos fijos` textos van en las
  primeras posiciones; el resto de las posiciones son para textos que pone el código (nombres, números, títulos
  que cambian).
  El japonés trae la x precalculada para su ancho (12 px por kanji, 8 por kana de medio ancho): los títulos de las
  barras (y = 9) centrados en su recuadro, y los menús centrados en su columna. Con el inglés (VWF, más angosto o más
  ancho) quedan corridos. Este script recalcula la x con el ancho real del texto ya traducido (tabla VWF):
    · título (y = 9) o "centrar": se conserva el centro del japonés, x += (ancho_jp − ancho_en) // 2.
    · "izquierda": todas las opciones del menú a la x mínima del japonés (columna pareja, como en SRW OG).
  Títulos que pone el código (sin texto fijo en el layout): la lista de unidades usa 味方部隊表/敵方部隊表 de PRM
  (tabla en PRM+0x26C70) en la posición 4 de los layouts +0x26E20 y +0x26E2C.

  PRM_GRP (carga en 0x800A8920), menú de comandos de la unidad (Move/Attack/Transform…, FUN_800C7794): el recuadro
  mide 0x30 px fijos y el cursor 0x26; "Transform" (44 px desde x = 12) se salía. Se ensancha a ANCHO_CMD (el
  comando más ancho + 20, múltiplo de 8) y se corre lo mismo la ventana que se abre a su derecha
  ("Separate?/Disconnect?" Sí/No, FUN_800C78C0: x + 0x30 si x + 0x88 < 0x138; si no, x − 0x58).

  SNMP_GRP +0x5B0 / +0x5B4 (0x800D6788 / 0x800D678C; los usa solo SNMP code@+0xDC10/+0xDC2C): el 「 y el 」 que el
  juego pone alrededor de la frase de DEADMESS (después del nombre corto del piloto). Se cambian por ": " (colon +
  espacio VWF 0xA0) y "" → "Nombre: frase". Probado en emulador 2026-10-04. (Los de las frases de batalla están en
  BTL_GRP 0x80113124 y van por menus_en.jsonl: "%s".)

  SNMP_GRP layout +0x26E74 (menú «Combine», issue #8 del repo público): 4 posiciones, 3 textos fijos (あと, 回合体出来ます,
  合体しますか?) y el número de combinaciones, que dibuja el código en la posición 3 (x = 28, justo después de あと).
  «Left» mide 18 px y pisaba el número ("Left3  combines left"). Se deja «N combinations left»: el texto 0 pasa a una
  cadena vacía (solo en este layout; la pantalla de selección de unidades de salida sigue con «Left»), el número va en la
  x de «Left» y «combinations left» a 16 px (dos dígitos, como en el japonés).

Cada instrucción se compara con la original antes de cambiarla: si el overlay no es el esperado, sale con error.

Uso:
  layout_patch.py build <SNMP_entrada|-> <PRM_entrada|-> <dir_salida>   (- = iso_jp/OVL)
  layout_patch.py report [<SNMP_entrada> <PRM_entrada>]                   lista lo que cambiaría, sin escribir
"""
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(__file__))
from check_text import ADV, MARKERS  # noqa: E402  (tabla VWF de patches/vwf_table.bin o de la fuente)

WORK = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
ISO_OVL = os.path.join(WORK, 'iso_jp', 'OVL')
SNMP_BASE, PRM_BASE = 0x800D61D8, 0x800A8920
LAYOUTS = (0x26D54, 0x26FA4)          # tabla de layouts de SNMP (archivo), registros de 12 bytes
BRK = 0x5B0                           # 「 y 」 de DEADMESS en SNMP_GRP (archivo)
TITLE_Y = 9                           # y de los títulos en la barra superior

# Menús: offset del layout en SNMP → modo
MENUS = {
    0x26D9C: 'izquierda',   # mapa: End Turn / Spirit Search / Unit List / Counter / Objectives / System / Save
    0x26E14: 'izquierda',   # respuesta al ataque enemigo: Start Battle / Counter / Defend+Attack / Defend / Evade
    0x26EC8: 'izquierda',   # órdenes de contraataque: Manual / Aggressive! / Efficient! / No Counter!
    0x26F10: 'centrar',     # Sí / No
    0x26F64: 'centrar',     # animación de batalla: título + ON / OFF
}
# Centro fijo (x relativa a la ventana) para menús 'centrar' cuyo centro japonés no coincide con el del cursor:
# Sí/No mide el cursor de 6 a 41 → centro 24 (el japonés centraba en 28/30 y el inglés quedaba corrido, #277)
CENTERS = {0x26F10: 24}
# Títulos que pone el código: (layout, índice de posición) → punteros (archivo de PRM) a los textos posibles
DYN_TITLES = {(0x26E20, 4): (0x26C70, 0x26C74), (0x26E2C, 4): (0x26C70, 0x26C74)}

# Menú «Combine» (issue #8 del repo público): layout, posición del número (la pone el código) y ancho de su campo
COMBINE = 0x26E74
COMBINE_NUM, COMBINE_TXT, COMBINE_FIELD = 3, 1, 16

# Menú de comandos de la unidad (PRM): dirección → (instrucción original, cómo armar la nueva con el ancho W)
CMD_TABLE = (0x26B2C, 0x26B84)        # punteros a 移動 攻撃 精神 変形 … 能力 (PRM, archivo)
CMD_PATCH = {
    0x800C77B4: (0x24020030, lambda w: 0x24020000 | w),                   # addiu v0, zero, 0x30  (ancho)
    0x800C7884: (0x24070026, lambda w: 0x24070000 | (w - 10)),            # addiu a3, zero, 0x26  (cursor)
    0x800C78EC: (0x24620088, lambda w: 0x24620000 | (0x58 + w)),          # addiu v0, v1, 0x88    (cabe a la derecha?)
    0x800C7900: (0x24710030, lambda w: 0x24710000 | w),                   # addiu s1, v1, 0x30    (x de la ventana)
}
CMD_JP_W, CMD_X = 0x30, 12


def px(raw: bytes) -> int:
    """Ancho en px de un texto del juego (bytes), como FUN_80018CC4 con el parche VWF (sin variables $)."""
    w, i, prev = 0, 0, None
    while i < len(raw):
        b = raw[i]
        if (0x81 <= b <= 0x9F or 0xE0 <= b <= 0xFC) and i + 1 < len(raw):
            w, i, prev = w + 12, i + 2, None
        elif b in MARKERS and prev is not None:
            w, prev, i = w + 8 - ADV[prev], None, i + 1
        else:
            w, prev, i = w + ADV[b], b, i + 1
    return w


def px_jp(raw: bytes) -> int:
    """Ancho del japonés original: 12 px por carácter doble, 8 por byte simple (sin VWF)."""
    w, i = 0, 0
    while i < len(raw):
        b = raw[i]
        if (0x81 <= b <= 0x9F or 0xE0 <= b <= 0xFC) and i + 1 < len(raw):
            w, i = w + 12, i + 2
        else:
            w, i = w + (0 if b in MARKERS and i else 8), i + 1
    return w


def cstr(buf: bytes, base: int, addr: int) -> bytes:
    o = addr - base
    return buf[o:buf.index(b'\0', o)]


def u32(buf, o):
    return struct.unpack_from('<I', buf, o)[0]


def show(raw: bytes) -> str:
    return raw.replace(b'\xa0', b' ').decode('cp932', 'replace')


def plan(snmp_jp: bytes, snmp: bytes, prm_jp: bytes, prm: bytes):
    """→ (cambios de posición {offset_x: (viejo, nuevo, descripción)}, ancho del menú de comandos, avisos)."""
    moves, notes = {}, []

    def text(buf_jp, buf, base, ptr_off):
        return cstr(buf_jp, base, u32(buf_jp, ptr_off)), cstr(buf, base, u32(buf, ptr_off))

    def want(off, new, what):
        if off in moves and moves[off][1] != new:
            notes.append(f'AVISO posición compartida {off:#x}: {moves[off][2]} / {what}; queda la primera')
            return
        old = struct.unpack_from('<h', snmp, off)[0]
        moves[off] = (old, new, what)

    for lay in range(*LAYOUTS, 12):
        n_pos, n_txt = snmp_jp[lay], snmp_jp[lay + 1]
        pos_ptr, txt_ptr = u32(snmp_jp, lay + 4), u32(snmp_jp, lay + 8)
        if not pos_ptr:
            continue
        items = []
        for i in range(n_txt):
            off = pos_ptr - SNMP_BASE + 4 * i
            x, y = struct.unpack_from('<hh', snmp_jp, off)
            jp, en = text(snmp_jp, snmp, SNMP_BASE, txt_ptr - SNMP_BASE + 4 * i)
            items.append((off, x, y, jp, en))
        mode = MENUS.get(lay)
        if mode == 'izquierda':
            left = min(x for _, x, _, _, _ in items)
            for off, x, y, jp, en in items:
                want(off, left, f'menú {lay:#x} «{show(en)}»')
        for off, x, y, jp, en in items:
            if lay in CENTERS:
                want(off, CENTERS[lay] - px(en) // 2, f'centrado {lay:#x} «{show(en)}» ({px(en)} px; centro '
                     f'{CENTERS[lay]})')
            elif mode == 'centrar' or (mode is None and y == TITLE_Y):
                want(off, x + (px_jp(jp) - px(en)) // 2, f'{"título" if y == TITLE_Y else "centrado"} {lay:#x} '
                     f'«{show(en)}» ({px(en)} px; jp {px_jp(jp)})')

    for (lay, idx), ptrs in DYN_TITLES.items():
        off = u32(snmp_jp, lay + 4) - SNMP_BASE + 4 * idx
        x, y = struct.unpack_from('<hh', snmp_jp, off)
        pairs = [text(prm_jp, prm, PRM_BASE, p) for p in ptrs]
        shift = sum(px_jp(jp) - px(en) for jp, en in pairs) / len(pairs) / 2
        want(off, x + int(shift), f'título {lay:#x}[{idx}] ' + ' / '.join(f'«{show(en)}»' for _, en in pairs))

    pos_ptr, txt_ptr = u32(snmp_jp, COMBINE + 4) - SNMP_BASE, u32(snmp_jp, COMBINE + 8) - SNMP_BASE
    left_x = struct.unpack_from('<h', snmp_jp, pos_ptr)[0]                 # x de あと: ahí empieza «N combinations left»
    want(pos_ptr + 4 * COMBINE_NUM, left_x, f'combinar {COMBINE:#x}: número en la x de «Left»')
    want(pos_ptr + 4 * COMBINE_TXT, left_x + COMBINE_FIELD,
         f'combinar {COMBINE:#x} «{show(cstr(snmp, SNMP_BASE, u32(snmp, txt_ptr + 4)))}» a {COMBINE_FIELD} px del número')

    widest = max(px(cstr(prm, PRM_BASE, u32(prm, o))) for o in range(*CMD_TABLE, 4) if u32(prm, o))
    width = max(CMD_JP_W, -(-(CMD_X + widest + 8) // 8) * 8)
    return {k: v for k, v in moves.items() if v[0] != v[1]}, width, widest, notes


def hide_left(snmp_jp: bytes, snmp: bytearray) -> str:
    """Texto 0 del layout «Combine» (あと / «Left») → cadena vacía: el NUL que cierra al texto 1 (así no depende de dónde
    reubique el pipeline las cadenas). La otra pantalla con あと (+0x26D54) apunta a su propia tabla y no cambia."""
    ptrs = u32(snmp_jp, COMBINE + 8) - SNMP_BASE
    jp0 = cstr(snmp_jp, SNMP_BASE, u32(snmp_jp, ptrs))
    if jp0 != 'あと'.encode('cp932'):
        sys.exit(f'ERROR SNMP layout {COMBINE:#x}: el texto 0 no es あと ({show(jp0)})')
    nul = u32(snmp, ptrs + 4) + len(cstr(snmp, SNMP_BASE, u32(snmp, ptrs + 4)))
    if snmp[nul - SNMP_BASE] != 0:
        sys.exit(f'ERROR SNMP {nul:#x}: se esperaba un NUL')
    struct.pack_into('<I', snmp, ptrs, nul)
    return f'SNMP +{ptrs:#07x} texto 0 de {COMBINE:#x} → {nul:#x} (cadena vacía)'


def load(path: str, name: str) -> bytes:
    return open(path if path != '-' else os.path.join(ISO_OVL, name), 'rb').read()


def main(argv):
    if not argv or argv[0] not in ('build', 'report'):
        sys.exit(__doc__)
    snmp_in = argv[1] if len(argv) > 1 else '-'
    prm_in = argv[2] if len(argv) > 2 else '-'
    snmp_jp, prm_jp = load('-', 'SNMP_GRP.BIN'), load('-', 'PRM_GRP.BIN')
    snmp, prm = bytearray(load(snmp_in, 'SNMP_GRP.BIN')), bytearray(load(prm_in, 'PRM_GRP.BIN'))
    moves, width, widest, notes = plan(snmp_jp, bytes(snmp), prm_jp, bytes(prm))

    for off, (old, new, what) in sorted(moves.items()):
        print(f'SNMP +{off:#07x} x {old:3d} → {new:3d}  {what}')
        struct.pack_into('<h', snmp, off, new)
    print(hide_left(snmp_jp, snmp))
    print(f'PRM menú de comandos: comando más ancho {widest} px → recuadro {width} px (japonés {CMD_JP_W})')
    if width != CMD_JP_W:
        for addr, (orig, make) in CMD_PATCH.items():
            o = addr - PRM_BASE
            if u32(prm, o) != orig:
                sys.exit(f'ERROR PRM {addr:#x}: {u32(prm, o):#010x}, se esperaba {orig:#010x}')
            struct.pack_into('<I', prm, o, make(width))
    if bytes(snmp[BRK:BRK + 8]) == b'\x81\x75\0\0\x81\x76\0\0':      # 「 y 」 de la frase de DEADMESS
        snmp[BRK:BRK + 8] = b':\xa0\0\0\0\0\0\0'
        print('SNMP +0x5b0: 「 → ": ", +0x5b4: 」 → ""')
    elif bytes(snmp[BRK:BRK + 8]) != b':\xa0\0\0\0\0\0\0':
        sys.exit('ERROR SNMP +0x5b0: no es 「/」 ni ya parcheado')
    for n in notes:
        print(n)

    if argv[0] == 'build':
        out = argv[3]
        os.makedirs(out, exist_ok=True)
        for name, buf in (('SNMP_GRP.BIN', snmp), ('PRM_GRP.BIN', prm)):
            with open(os.path.join(out, name), 'wb') as f:
                f.write(buf)
    print(f'{len(moves)} posiciones cambiadas · menú de comandos {width} px')


if __name__ == '__main__':
    main(sys.argv[1:])
