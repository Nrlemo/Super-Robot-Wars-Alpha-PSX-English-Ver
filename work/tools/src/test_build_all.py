"""Pruebas de build_all.py y shots_check.py (sin la ISO real). Correr desde work/tools/src:
python3 -m unittest test_build_all

La verificación de imagen se prueba con una ISO sintética MODE2/2352 (necesita pycdlib) y shots_check.py con capturas
sintéticas (necesita Pillow): los dos están en el venv de server1; si faltan, esas pruebas se saltean.
"""
import argparse
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import build_all as ba

try:
    import pycdlib
except ImportError:
    pycdlib = None
try:
    from PIL import Image
    import shots_check
except ImportError:
    Image = None


def row(file='IMIS', addr='0x800d6200', jp='あい', en='Ok', en_short='', room=8, plan='in situ', refs=(),
        fits_short=None, notes=''):
    return {'file': file, 'addr': addr, 'jp': jp, 'en': en, 'en_short': en_short, 'room': room, 'plan': plan,
            'refs': list(refs), 'fits_short': fits_short, 'notes': notes}


class Menus(unittest.TestCase):
    def test_menus_stale(self):
        with tempfile.TemporaryDirectory() as d:
            m = Path(d) / 'map.txt'
            m.write_text('# comentario\nユニット || Unit || Un. || nota\n', encoding='utf-8')
            self.assertEqual(ba.menus_stale([row(jp='ユニット', en='Unit')], m), [])
            self.assertEqual(len(ba.menus_stale([row(jp='ユニット', en='Units')], m)), 1)
            self.assertEqual(len(ba.menus_stale([row(jp='パイロット', en='Pilot')], m)), 1)


class Exe(unittest.TestCase):
    def setUp(self):
        self.orig = bytes(0x50000)
        self.table = bytes(range(256))
        new = bytearray(self.orig)
        o = 0x80018F30 - ba.EXE_BASE
        new[o:o + 4] = b'\x01\x02\x03\x04'
        t = ba.VWF_TABLE_ADDR - ba.EXE_BASE
        new[t:t + 256] = self.table
        self.new = new

    def test_dentro_de_las_ventanas(self):
        self.assertEqual(ba.exe_problems(self.orig, bytes(self.new), self.table), [])

    def test_fuera_de_las_ventanas(self):
        self.new[0x100] = 1
        p = ba.exe_problems(self.orig, bytes(self.new), self.table)
        self.assertEqual(len(p), 1)
        self.assertIn('0x100', p[0])

    def test_tamano_y_tabla(self):
        self.assertIn('tamaño', ba.exe_problems(self.orig, bytes(self.new) + b'\0', self.table)[0])
        self.assertIn('tabla VWF', ba.exe_problems(self.orig, bytes(self.new), bytes(256))[-1])

    def test_diff_ranges(self):
        self.assertEqual(ba.diff_ranges(b'abcdef', b'aXcdYY'), [(1, 2), (4, 6)])
        self.assertEqual(ba.diff_ranges(b'abc', b'abc'), [])


class Varios(unittest.TestCase):
    def test_capacidad(self):
        self.assertEqual(ba.capacity(ba.CD_74), 'ok')
        self.assertEqual(ba.capacity(ba.CD_74 + 1), 'aviso')
        self.assertEqual(ba.capacity(ba.CD_80 + 1), 'error')

    def test_cue(self):
        good = 'FILE "x.bin" BINARY\n  TRACK 01 MODE2/2352\n    INDEX 01 00:00:00\n'
        self.assertEqual(ba.cue_problems(good, 'x.bin', good), ([], []))
        self.assertTrue(ba.cue_problems(good, 'y.bin')[0])
        self.assertTrue(ba.cue_problems(good.replace('"x.bin"', '"/tmp/x.bin"'), 'x.bin')[1])
        self.assertTrue(ba.cue_problems(good.replace('MODE2', 'MODE1'), 'x.bin')[0])
        two = good + '  TRACK 02 AUDIO\n    INDEX 01 10:00:00\n'
        self.assertTrue(ba.cue_problems(good, 'x.bin', two)[0])

    def test_count_rows(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / 'x.jsonl'
            p.write_text('\n'.join(json.dumps(r) for r in [{'en': 'a'}, {'en': ''}, {'jp': 'x'}]) + '\n')
            self.assertEqual(ba.count_rows('snmsg', p), (3, 1))
            p.write_text(json.dumps({'full_en': '', 'short_en': 'Amuro'}) + '\n' + json.dumps({'full_en': ''}) + '\n')
            self.assertEqual(ba.count_rows('pilot', p), (2, 1))
            p.write_text(json.dumps({'en': ['', None]}) + '\n' + json.dumps({'en': ['Amuro Ray']}) + '\n'
                         + json.dumps({'en': None}) + '\n')
            self.assertEqual(ba.count_rows('dc', p), (3, 1))


def ns(**kw):
    base = dict(only=None, skip=None, selftest=False, smoke=False, release=False, null=False)
    base.update(kw)
    return argparse.Namespace(**base)


class Etapas(unittest.TestCase):
    def test_tabla(self):
        ids = [s.id for s in ba.STAGES]
        self.assertEqual(len(ids), len(set(ids)))
        for s in ba.STAGES:
            if s.run is None:
                self.assertTrue(s.needs, s.id)
        pos = {s: i for i, s in enumerate(ids)}
        # fuente antes de validar (vwf_table.bin), EXE después de la fuente (incluye la tabla), todo antes de la ISO
        self.assertLess(pos['font'], pos['validate'])
        self.assertLess(pos['font'], pos['exe'])
        self.assertLess(pos['exe'], pos['exe_strings'])
        for s in ids[pos['font']:pos['iso']]:
            self.assertLess(pos[s], pos['iso'])
        self.assertLess(pos['iso'], pos['verify'])

    def test_seleccion(self):
        ids = lambda **kw: [s.id for s in ba.select(ns(**kw))]
        default = ids()
        self.assertNotIn('selftest', default)
        self.assertNotIn('smoke', default)
        self.assertIn('dc', default)                              # las pendientes se muestran
        self.assertEqual(ids(null=True), ['preflight', 'iso', 'verify'])
        self.assertEqual(ids(null=True, selftest=True), ['preflight', 'selftest', 'iso', 'verify'])
        self.assertEqual(ids(only='snmsg'), ['preflight', 'snmsg'])
        self.assertIn('selftest', ids(selftest=True))
        self.assertNotIn('menus', ids(skip='menus'))
        with self.assertRaises(SystemExit):
            ids(only='verify')                                       # verify sin iso
        with self.assertRaises(SystemExit):
            ids(only='noexiste')


def mode2(iso2048: bytes) -> bytes:
    """ISO de sectores de 2048 → MODE2/2352 (sync + cabecera + subcabecera + datos + EDC/ECC en cero)."""
    out = bytearray()
    for i in range(0, len(iso2048), 2048):
        out += b'\x00' + b'\xff' * 10 + b'\x00' + bytes(12) + iso2048[i:i + 2048] + bytes(280)
    return bytes(out)


@unittest.skipIf(pycdlib is None, 'pycdlib no instalado (está en el venv de server1)')
class Verificacion(unittest.TestCase):
    FILES = {'SYSTEM.CNF': b'BOOT = cdrom:\\SLPS_026.36;1\r\n', 'SLPS_026.36': bytes(range(256)) * 40,
             'SNMAP/SNMSG.BIN': b'\x82\xa0' * 3000, 'STR/OP.STR': b'\x11' * 5000}

    def image(self, files: dict) -> bytes:
        iso = pycdlib.PyCdlib()
        iso.new(interchange_level=1)
        for d in sorted({p.split('/')[0] for p in files if '/' in p}):
            iso.add_directory('/' + d)
        for p, data in files.items():
            iso.add_fp(io.BytesIO(data), len(data), '/' + p + ';1')
        buf = io.BytesIO()
        iso.write_fp(buf)
        iso.close()
        return mode2(buf.getvalue())

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        t = self.d = Path(self.tmp.name)
        jp = t / 'iso_jp'
        for p, data in self.FILES.items():
            (jp / p).parent.mkdir(parents=True, exist_ok=True)
            (jp / p).write_bytes(data)
        (jp / 'layout.xml').write_text(
            '<iso_project><track type="data"><directory_tree>'
            '<file name="SYSTEM.CNF"/><file name="SLPS_026.36"/>'
            '<dir name="SNMAP"><file name="SNMSG.BIN"/></dir><dir name="STR"><file name="OP.STR" type="str"/></dir>'
            '</directory_tree></track></iso_project>')
        self.cue = 'FILE "{}" BINARY\n  TRACK 01 MODE2/2352\n    INDEX 01 00:00:00\n'
        self.jp_bin = t / 'orig.bin'
        self.jp_bin.write_bytes(self.image(self.FILES))
        self.jp_bin.with_suffix('.cue').write_text(self.cue.format('orig.bin'))

    def tearDown(self):
        self.tmp.cleanup()

    def build(self, files, name='b.bin'):
        b = self.d / name
        b.write_bytes(self.image(files))
        b.with_suffix('.cue').write_text(self.cue.format(name))
        return b

    def verify(self, b, repl=None, **kw):
        return ba.verify_image(b, repl or {}, jp_bin=self.jp_bin, iso_jp=self.d / 'iso_jp', **kw)

    def test_sin_cambios_y_null(self):
        b = self.build(self.FILES)
        rep = self.verify(b, null=True)
        self.assertEqual(rep['errores'], [])
        self.assertEqual(rep['xa_str'], 1)
        self.assertEqual(rep['comparados'], 3)

    def test_reemplazo(self):
        new = b'Tashiro: Ugh...\xa0' * 400                           # otro tamaño: el FS se reacomoda
        local = self.d / 'SNMSG_en.BIN'
        local.write_bytes(new)
        b = self.build(dict(self.FILES, **{'SNMAP/SNMSG.BIN': new}))
        self.assertEqual(self.verify(b, {'SNMAP/SNMSG.BIN': local})['errores'], [])
        self.assertEqual(self.verify(b, {'SNMAP/SNMSG.BIN': local}, mode='reemplazos')['errores'], [])
        # sin declarar el reemplazo, la imagen no coincide con iso_jp
        self.assertTrue(any('SNMSG' in e for e in self.verify(b)['errores']))
        self.assertTrue(any('--null' in e for e in self.verify(b, {'SNMAP/SNMSG.BIN': local}, null=True)['errores']))

    def test_contenido_distinto_mismo_tamano(self):
        bad = bytearray(self.FILES['SLPS_026.36'])
        bad[10] ^= 0xFF
        b = self.build(dict(self.FILES, **{'SLPS_026.36': bytes(bad)}))
        self.assertTrue(any('SLPS_026.36' in e and 'contenido' in e for e in self.verify(b)['errores']))

    def test_faltantes_str_y_cue(self):
        files = {k: v for k, v in self.FILES.items() if k != 'SYSTEM.CNF'}
        files['STR/OP.STR'] = b'\x11' * 6000
        b = self.build(files)
        b.with_suffix('.cue').write_text(self.cue.format('otro.bin'))
        errs = self.verify(b)['errores']
        self.assertTrue(any('falta en la imagen: SYSTEM.CNF' in e for e in errs))
        self.assertTrue(any('OP.STR' in e for e in errs))
        self.assertTrue(any('.cue' in e for e in errs))


@unittest.skipIf(Image is None, 'Pillow no instalado (está en el venv de server1)')
class Capturas(unittest.TestCase):
    def shots(self, d: Path, colors: dict, size=(320, 240)):
        d.mkdir(parents=True, exist_ok=True)
        for f, c in colors.items():
            im = Image.new('RGB', size, c)
            if c != (0, 0, 0):
                im.paste((255, 255, 255), (10, 10, 60, 30))              # "texto": no uniforme
            im.save(d / f'f{f:05d}_{size[0]}x{size[1]}_16.png')

    def test_controles(self):
        with tempfile.TemporaryDirectory() as t:
            t = Path(t)
            self.shots(t / 'ok', {600: (0, 0, 0), 1500: (0, 0, 90), 2400: (90, 0, 0)})
            self.assertEqual(shots_check.check(t / 'ok', 3)[0], [])
            self.assertEqual(shots_check.check(t / 'ok', 3)[1]['uniformes'], ['f00600'])
            self.assertTrue(shots_check.check(t / 'ok', 5)[0])            # faltan capturas
            self.shots(t / 'negro', {600: (0, 0, 0), 1500: (0, 0, 0)})
            self.assertTrue(shots_check.check(t / 'negro')[0])
            self.shots(t / 'congelado', {600: (0, 0, 90), 1500: (0, 0, 90)})
            self.assertTrue(any('idénticas' in p for p in shots_check.check(t / 'congelado')[0]))
            self.assertEqual(shots_check.main([str(t / 'ok'), '--expect', '3']), 0)
            self.assertEqual(shots_check.main([str(t / 'negro')]), 1)

    def test_comparacion(self):
        with tempfile.TemporaryDirectory() as t:
            t = Path(t)
            self.shots(t / 'ref', {600: (0, 0, 90), 1500: (0, 90, 0), 3000: (0, 0, 90)})
            self.shots(t / 'new', {600: (0, 0, 90), 1500: (90, 0, 0), 2400: (9, 9, 9)})
            self.shots(t / 'new', {3000: (0, 0, 90)}, size=(512, 240))   # otra resolución: se reescala, no se rompe
            changed, only = shots_check.compare(t / 'new', t / 'ref', t / 'diff.png')
            self.assertEqual([k for k, _ in changed], ['f01500', 'f03000'])
            self.assertEqual(only, ['f02400'])
            self.assertTrue((t / 'diff.png').exists())


class DryRun(unittest.TestCase):
    def test_pipeline_en_seco(self):
        """El pipeline completo en --dry-run sobre los volcados reales: valida textos y planifica los menús."""
        with tempfile.TemporaryDirectory() as d:
            env = dict(os.environ, SRW_BUILD_DIR=d)
            p = subprocess.run([sys.executable, str(ba.SRC / 'build_all.py'), '--dry-run', '--name', 't'],
                               env=env, capture_output=True, text=True)
            self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
            m = json.loads(next(Path(d).glob('t_v*/manifest.json')).read_text(encoding='utf-8'))
            st = {e['id']: e['estado'] for e in m['etapas']}
            self.assertIn(st['validate'], ('ok', 'aviso'))
            self.assertEqual(st['dc'], 'plan')
            self.assertEqual(st['entry'], 'plan')
            self.assertEqual(st['titles'], 'plan')
            self.assertIn(st['graphics'], ('pendiente', 'plan'))   # pendiente si no hay gfx/render/out (nube)
            self.assertEqual(st['menus'], 'plan')


if __name__ == '__main__':
    unittest.main()
