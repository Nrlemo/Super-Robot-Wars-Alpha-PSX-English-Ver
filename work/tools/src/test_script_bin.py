"""Pruebas de script_bin.py sin la ISO (#220). Correr desde work/tools/src: python3 -m unittest test_script_bin

Protegen que el extractor siga tomando los tres tipos de texto de SCRIPT.BIN (0x10 diálogo, 0x210 línea hablada,
0x80 menú de decisión) y que el volcado de trabajo no los pierda.
"""
import json
import os
import struct
import unittest

import script_bin as sb


def inst(op, sub, body, pad=b''):
    padded = (len(body) + 3) & ~3
    pad = (pad + b'\0' * padded)[:padded - len(body)]
    return struct.pack('<4H', op, sub, 0, len(body)) + body + pad


def fake_bin(per_script):
    """SCRIPT.BIN sintético: 255 scripts, los de `per_script` (dict n → bytes) con contenido, el resto vacío."""
    first = 4 * sb.NSCRIPTS
    blobs = [per_script.get(k, b'') for k in range(sb.NSCRIPTS)]
    offs, cur = [], first
    for b in blobs:
        offs.append(cur)
        cur += len(b)
    return struct.pack('<%dI' % sb.NSCRIPTS, *offs) + b''.join(blobs)


class ExtraccionTest(unittest.TestCase):
    def setUp(self):
        body = (inst(sb.TEXT_OP, 8, '$n「見たことがない」'.encode('cp932') + b'\0')
                + inst(sb.SPOKEN_OP, 8, '$n「ど、どうする…？」'.encode('cp932') + b'\0')
                + inst(sb.CHOICE_OP, 1, '「ロボットに乗る」\n「恋人を捜す」'.encode('cp932') + b'\0')
                + inst(sb.CHOICE_OP, 1, b'372 384 \0')                # 0x80 sin texto japonés: no es una opción
                + inst(0x0009, 24, '70 小さい振動'.encode('cp932') + b'\0'))
        self.data = fake_bin({1: body})
        self.scripts, _, self.first = sb.parse(self.data)

    def test_toma_los_tres_tipos(self):
        got = [(i, ins['op']) for _, i, _, ins in sb.texts(self.scripts)]
        self.assertEqual(got, [(0, sb.TEXT_OP), (1, sb.SPOKEN_OP), (2, sb.CHOICE_OP)])

    def test_line_solo_cuenta_op_0x10(self):
        # la numeración `line` de las 0x10 no puede moverse al agregar tipos (las traducciones se casan por script/inst)
        self.assertEqual([t for _, _, t, _ in sb.texts(self.scripts)], [0, 1, 1])

    def test_reconstruccion_identica(self):
        self.assertEqual(sb.build(self.scripts, self.first, self.data), self.data)

    def test_reemplazo_de_una_decision(self):
        self.scripts[1][2]['data'] = sb.encode_en('"Board the robot"\n"Look for my partner"')
        out = sb.build(self.scripts, self.first, self.data)
        again, _, _ = sb.parse(out)
        self.assertEqual(again[1][2]['data'].split(b'\0')[0].replace(b'\xa0', b' ').decode('cp932'),
                         '"Board the robot"\n"Look for my partner"')
        self.assertEqual(again[1][0]['data'], self.scripts[1][0]['data'])


@unittest.skipUnless(os.path.exists(os.path.join(sb.WORK, 'dump', 'script.jsonl')), 'sin work/dump/script.jsonl')
class VolcadoTest(unittest.TestCase):
    """El volcado versionado tiene las decisiones y las líneas 0x210 (sin la ISO no se puede regenerar: se cuentan)."""

    def test_cobertura(self):
        ops = {}
        with open(os.path.join(sb.WORK, 'dump', 'script.jsonl'), encoding='utf-8') as f:
            for line in f:
                r = json.loads(line)
                op = r.get('op', sb.TEXT_OP)
                ops[op] = ops.get(op, 0) + 1
        self.assertEqual(ops.get(sb.CHOICE_OP), 68)
        self.assertEqual(ops.get(sb.SPOKEN_OP), 281)
        self.assertEqual(ops.get(sb.TEXT_OP), 45363)


if __name__ == '__main__':
    unittest.main()
