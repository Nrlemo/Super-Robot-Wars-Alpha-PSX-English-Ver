"""Pruebas de mdata_bin.py sin la ISO (#221). Correr desde work/tools/src: python3 -m unittest test_mdata_bin"""
import json
import os
import unittest

import mdata_bin as mb


def record(name, hdr=b'\x01\0\x08\0'):
    return hdr + name.encode('cp932').ljust(mb.FIELD, b'\0')


def fake(*names):
    """Archivo sintético: 4 B de cabecera de relleno + registros de 20 B."""
    return b'\0\0\0\0' + b''.join(record(n) for n in names) + b'\0' * 8


class CamposTest(unittest.TestCase):
    def test_encuentra_los_nombres(self):
        got = [t for _, t in mb.fields(fake('領域外', '平原', '光子力研究所'))]
        self.assertEqual(got, ['領域外', '平原', '光子力研究所'])

    def test_no_cuenta_sufijos_alineados(self):
        # 領域外 = 6 bytes; a +4 empieza "外": no es un campo (hubo 1.463 campos con ese error, ahora 1.375)
        self.assertEqual(len(mb.fields(fake('領域外'))), 1)

    def test_kana_de_ancho_medio(self):
        got = [t for _, t in mb.fields(fake('ﾏｸﾛｽﾄﾞｯｸ', 'ﾀﾀ'))]
        self.assertEqual(got, ['ﾏｸﾛｽﾄﾞｯｸ'])        # ≥3 caracteres; "ﾀﾀ" es ruido de gráficos

    def test_nombres_con_ascii(self):
        got = [t for _, t in mb.fields(fake('ｺﾛﾆ-', 'NERV本部', 'DC本部ﾋﾞﾙ', 'ABC'))]
        self.assertEqual(got, ['ｺﾛﾆ-', 'NERV本部', 'DC本部ﾋﾞﾙ'])   # 'ABC' sola no es un nombre japonés

    def test_ignora_basura(self):
        self.assertEqual(mb.fields(b'\0\0\0\0' + bytes(range(0x80, 0x94)) * 3), [])


class ReemplazoTest(unittest.TestCase):
    def test_mismo_tamano_y_resto_intacto(self):
        data = fake('領域外', '平原')
        off = mb.fields(data)[1][0]
        out, n = mb.build(data, [{'file': 'X', 'off': off, 'jp': '平原', 'en': 'Plains'}])
        self.assertEqual((n, len(out)), (1, len(data)))
        self.assertEqual(out[off:off + 16], b'Plains' + b'\0' * 10)
        self.assertEqual(out[:off], data[:off])
        self.assertEqual(out[off + 16:], data[off + 16:])

    def test_sin_traduccion_es_identico(self):
        data = fake('領域外')
        self.assertEqual(mb.build(data, [{'file': 'X', 'off': 8, 'jp': '領域外', 'en': ''}])[0], data)

    def test_espacio_es_0xA0(self):
        self.assertEqual(mb.encode_en('Out of Bounds')[:3], b'Out')
        self.assertIn(b'\xa0', mb.encode_en('Out of Bounds'))

    def test_tope_15(self):
        mb.encode_en('x' * 15)
        with self.assertRaises(ValueError):
            mb.encode_en('x' * 16)

    def test_rechaza_fila_desfasada(self):
        with self.assertRaises(AssertionError):
            mb.build(fake('領域外'), [{'file': 'X', 'off': 8, 'jp': '平原', 'en': 'Plains'}])


@unittest.skipUnless(os.path.exists(os.path.join(mb.WORK, 'dump', 'mdata.jsonl')), 'sin work/dump/mdata.jsonl')
class VolcadoTest(unittest.TestCase):
    def test_cobertura_y_topes(self):
        with open(os.path.join(mb.WORK, 'dump', 'mdata.jsonl'), encoding='utf-8') as f:
            rows = [json.loads(l) for l in f]
        self.assertEqual(len(rows), 1426)
        self.assertEqual(len({r['jp'] for r in rows}), 79)
        self.assertEqual(sum(r['file'] == 'SNMAP' for r in rows), 1343)
        for r in rows:
            self.assertTrue(r['en'], r)
            mb.encode_en(r['en'])


if __name__ == '__main__':
    unittest.main()
