"""Arma DEADMESS.BIN y EM.BIN de prueba para verificar en el juego ventana, renglones y ancho (2026-09-28).

DEADMESS: activa el bit de frase de los 512 pilotos (así cualquier derribo, incluso de soldados genéricos, muestra
una) y pone en cada slot un texto inglés de 3 renglones que identifica piloto y variante:
  "DM <piloto> v<variante> <tipo> ..." — el tipo (u32) se conserva; en los slots vacíos queda 0.
EM: los 30 registros con 3 renglones ingleses "Nombre: "[EM <n>] ..."".
Los renglones se miden con la tabla VWF real (check_text.line_px) y se imprimen los anchos.

Uso: mk_deadem_test.py <dir_iso_jp/SNMAP> <dir_salida>
"""
import os, struct, sys

sys.path.insert(0, os.path.dirname(__file__))
from script_bin import encode_en  # noqa: E402
from check_text import line_px  # noqa: E402

DM_LINES = [
    'DM {p} v{v} t{t}: Damn it... I cannot go down here!',
    ' The quick brown fox jumps over the lazy dog, twice.',
    ' Third line: measuring the box width ......... |',
]
EM_LINES = [
    'Rai: "[EM {i}] Suspending already? A wise decision.',
    ' Long operations are bad for your health, you know.',
    ' Get some rest, then rejoin the mission! ....... |"',
]


def main():
    src, out = sys.argv[1], sys.argv[2]
    os.makedirs(out, exist_ok=True)

    dm = bytearray(open(os.path.join(src, 'DEADMESS.BIN'), 'rb').read())
    assert len(dm) == 262208
    dm[0:0x40] = b'\xff' * 0x40
    for slot in range(1024):
        o = 0x40 + slot * 0x100
        t = struct.unpack_from('<I', dm, o)[0]
        text = '\n'.join(DM_LINES).format(p=slot // 2, v=slot % 2, t=t)
        b = encode_en(text)
        assert len(b) <= 252, (slot, len(b))
        dm[o + 4:o + 0x100] = b + b'\0' * (252 - len(b))
    open(os.path.join(out, 'DEADMESS.BIN'), 'wb').write(dm)

    em = bytearray(open(os.path.join(src, 'EM.BIN'), 'rb').read())
    assert len(em) == 85264
    for i in range(30):
        o = i * 0x108 + 8
        b = encode_en('\n'.join(EM_LINES).format(i=i))
        assert len(b) <= 256
        em[o:o + 256] = b + b'\0' * (256 - len(b))
    open(os.path.join(out, 'EM.BIN'), 'wb').write(em)

    if '--boost-nu' in sys.argv:  # derribo garantizado en CP04: armas del ν Gundam (ﾙﾟｶﾞﾝﾀﾞﾑ*) con potencia ×6
        import robot_raf
        raf = open(os.path.join(src, '..', 'UNITPRAM', 'ROBOT.RAF'), 'rb').read()
        raws = []
        for _, _, rec in robot_raf.entries(raf):
            rec = bytearray(rec)
            if robot_raf.cstr(rec[0:0x1A]).startswith('ﾙﾟｶﾞﾝﾀﾞﾑ'):
                for k in range(len(robot_raf.parse(rec)['weapons'])):  # ×6 conserva el orden (el cursor elige por potencia)
                    o = robot_raf.W0 + k * robot_raf.WSIZE + 4
                    struct.pack_into('<H', rec, o, min(65535, 6 * struct.unpack_from('<H', rec, o)[0]))
                print('boost:', robot_raf.cstr(rec[0:0x1A]))
            raws.append(bytes(rec))
        open(os.path.join(out, 'ROBOT.RAF'), 'wb').write(robot_raf.build_raf(raws))

    for name, lines, kw in (('DEADMESS', DM_LINES, dict(p=460, v=1, t=2)), ('EM', EM_LINES, dict(i=29))):
        for ln in lines:
            s = ln.format(**kw)
            print(f'{name:8} {line_px(s):4d} px  {s!r}')


if __name__ == '__main__':
    main()
