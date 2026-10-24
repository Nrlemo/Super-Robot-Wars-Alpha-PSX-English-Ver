"""Pruebas de check_text.py con líneas sintéticas. Correr desde work/tools/src: python3 -m unittest test_check_text"""
import json
import tempfile
import unittest
from pathlib import Path

import check_text as ct
from check_text import FORMATS, check_text, line_px, marker_positions, wrap
from sjis_text import encode


def kinds(viol):
    return sorted((v['kind'], v['severity']) for v in viol)


class Medicion(unittest.TestCase):
    def test_frase_de_referencia(self):
        # notes/fuente_en.md: 42 caracteres = 175 px con la fuente actual
        self.assertEqual(line_px('The EOT fleet we built is being torn apart', adv=ct.table_from_font(ct.FONT_TXT)), 175)

    def test_espacio_y_digitos(self):
        t = ct.table_from_font(ct.FONT_TXT)
        self.assertEqual(t[0xA0], 3)                     # espacio inglés
        self.assertEqual(t[0x20], 8)                     # 0x20 y dígitos conservan 8 px
        self.assertTrue(all(t[b] == 8 for b in b'0123456789'))
        self.assertEqual(line_px('a b', adv=t), t[ord('a')] + 3 + t[ord('b')])

    def test_variable_y_sjis(self):
        self.assertEqual(line_px('$n'), 48)             # apodo ≤ 8 letras × 6 px
        self.assertEqual(line_px('$N $f'), 48 + 3 + 108)  # nombre completo 8 + espacio + 9 × 6 px
        self.assertEqual(line_px('「」'), 24)
        self.assertEqual(line_px('あ', kana_px=8), 8)


class Validacion(unittest.TestCase):
    def test_linea_correcta(self):
        self.assertEqual(check_text('Amuro: "Gundam, launching!"', '', FORMATS['snmsg']), [])

    def test_linea_ancha(self):
        v = check_text('W' * 60, '', FORMATS['snmsg'])
        self.assertEqual(kinds(v), [('px', 'error')])
        self.assertEqual(v[0]['line'], 1)

    def test_demasiadas_lineas_supuesto(self):
        # un límite supuesto (assumed) da aviso, no error; BXCLIST ya está medido (#31): 2 líneas → error
        import dataclasses
        supuesto = dataclasses.replace(FORMATS['bxclist'], assumed={'lines'})
        self.assertEqual(kinds(check_text('a\nb\nc', '', supuesto)), [('lines', 'warn')])
        self.assertEqual(kinds(check_text('a\nb\nc', '', FORMATS['bxclist'])), [('lines', 'error')])
        self.assertEqual(kinds(check_text('a\nb\nc\nd', '', FORMATS['snmsg'])), [('lines', 'error')])

    def test_bxclist_sin_corchetes(self):
        # desde #266 (BTL_GRP con %s) el juego ya no agrega 「」 en batalla: sin reserva, 30 dígitos (240 px) entran
        with tempfile.TemporaryDirectory() as d:
            src = Path(d, 'bx.jsonl')
            src.write_text(json.dumps({'pilot': 0, 'idx': 0, 'jp': '', 'en': '1' * 30}) + '\n', encoding='utf-8')
            (_, _, en, cap, reserve), = ct.iter_rows('bxclist', src)
            self.assertEqual(reserve, (0, 0))
            self.assertEqual(check_text(en, '', FORMATS['bxclist'], cap, reserve), [])
            self.assertEqual(kinds(check_text('1' * 31, '', FORMATS['bxclist'], cap, reserve)), [('px', 'error')])

    def test_bytes(self):
        f = FORMATS['deadmess']
        self.assertEqual(check_text('\n'.join(['i' * 83] * 3), '', f), [])            # 251 bytes justos, 3 líneas
        v = check_text('\n'.join(['i' * 84] * 3), '', f)
        self.assertIn(('bytes', 'error'), kinds(v))

    def test_formato_hablante(self):
        # #23: `Nombre: texto` (probado en el emulador); pensamientos `Nombre: (texto)`; renglones 2–3 sin sangría
        f = FORMATS['script']
        sp = lambda en, jp: [x['detail'] for x in check_text(en, jp, f) if x['kind'] == 'speaker']
        self.assertEqual(sp('Euzeth: Yes...', 'ユーゼス「はっ…」'), [])
        self.assertEqual(sp('Euzeth: (Heh...)\nAll according to plan.', 'ユーゼス（フ…\n　全て…）'), [])
        self.assertEqual(sp('$n: Yes...', '$n「はい」'), [])
        self.assertEqual(sp('Vice Captain: Only ours.', '副長「本艦一隻のみです…」'), [])
        self.assertEqual(len(sp('Euzeth「Yes...」', 'ユーゼス「はっ…」')), 2)
        self.assertEqual(sp('Euzeth: Yes,\n  sir.', 'ユーゼス「はっ…」'), ['renglón 2–3 con sangría'])
        self.assertEqual(sp('Yes...', 'ユーゼス「はっ…」'), ['no empieza con "Nombre: "'])
        self.assertEqual(sp('Narration text.', '西暦２０××年。'), [])          # sin hablante: no aplica
        self.assertEqual([x for x in check_text('Koji「Go!!」', '甲児「行くぜ！！」', FORMATS['bxclist'])
                          if x['kind'] == 'speaker'], [])                       # BXCLIST conserva 「」

    def test_reserva_deadmess(self):
        # En juego: "RG Short「" + renglón 1 de 210 px se cortó; el renglón 2 de 222 px entró (deadmess_em.md)
        f = FORMATS['deadmess']
        r = (line_px('RG Short', 12) + 12, 12)
        l1 = 'DM 460 v1 t2: Damn it... I cannot go down here!'
        l2 = ' The quick brown fox jumps over the lazy dog, twice.'
        v = check_text(f'{l1}\n{l2}\nOK', '', f, reserve=r)
        self.assertEqual([(x['kind'], x['line']) for x in v], [('px', 1)])
        self.assertEqual(v[0]['limit'], 240 - r[0])
        self.assertEqual(check_text(f'Hm.\n{l2}\nOK', '', f, reserve=r), [])
        # el último renglón pierde 12 px por el 」
        self.assertEqual(kinds(check_text('W' * 39 + 'i', '', f, reserve=(0, 12))), [('px', 'error')])

    def test_placeholders(self):
        f = FORMATS['snmsg']
        self.assertEqual(check_text('$n: Hi, $N!', '$n「やあ、$N！」', f), [])
        self.assertEqual(kinds(check_text('Hi!', '$n「やあ！」', f)), [('placeholder', 'error'), ('speaker', 'warn')])
        self.assertEqual(kinds(check_text('$n $n', '$n', f)), [('placeholder', 'error')])

    def test_decision_snmsg(self):        # #266: cada opción de una decisión de mapa va en su propia línea
        f, jp = FORMATS['snmsg'], '　$n選択\n「デュオを止める」\n「デュオを止めない」'
        self.assertEqual(check_text("$n's choice\nStop Duo\nDon't stop Duo", jp, f), [])
        self.assertEqual(kinds(check_text("$n's choice Stop Duo Don't stop Duo", jp, f)), [('choice', 'error')])
        self.assertFalse(ct.is_choice('トレーズ「…そう。\n　その選択もまた人として正しいのです」'))

    def test_marcador_dakuten(self):
        f = FORMATS['snmsg']
        self.assertEqual(kinds(check_text('Mkﾟ', '', f)), [('marker', 'error')])
        self.assertEqual(kinds(check_text('A{DE}', '', f)), [('marker', 'error')])
        self.assertEqual(marker_positions(encode('ﾞ')), [])        # al comienzo no sigue a nada
        self.assertEqual(marker_positions(encode('ガ')), [])        # 0x83 0x4B: par SJIS, no es marcador
        self.assertEqual(marker_positions(bytes([0x88, 0xDF])), [])  # 0xDF como 2º byte de un kanji

    def test_encoding(self):
        self.assertEqual(kinds(check_text('café', '', FORMATS['snmsg'])), [('encoding', 'error')])

    def test_dc_tope_por_campo(self):
        f = FORMATS['dc']
        self.assertEqual(kinds(check_text('Irm', '', f, max_bytes=2)), [('bytes', 'error')])   # layout confirmado


class Ajuste(unittest.TestCase):
    def test_wrap_entra(self):
        text = ('The EOT fleet we built is being torn apart like paper! '
                'Get me a status report on the machine weapon squadron, now!')
        lines = wrap(text, 240)
        self.assertGreater(len(lines), 1)
        self.assertTrue(all(line_px(ln) <= 240 for ln in lines))
        self.assertEqual(' '.join(lines), text)

    def test_wrap_palabra_larga(self):
        lines = wrap('W' * 80, 240)
        self.assertTrue(all(line_px(ln) <= 240 for ln in lines))
        self.assertEqual(''.join(lines), 'W' * 80)

    def test_keep_breaks(self):
        self.assertEqual(wrap('Hi.\nBye.', 240, keep_breaks=True), ['Hi.', 'Bye.'])
        self.assertEqual(wrap('Hi.\nBye.', 240), ['Hi. Bye.'])


class Programa(unittest.TestCase):
    def test_run_csv_y_wrap(self):
        rows = [
            {'id': 0, 'jp': '$n「テスト」', 'en': '$n: Test.'},
            {'id': 1, 'jp': 'タシロ「副長！」', 'en': 'Tashiro: ' + 'Number One, how many ships survived? ' * 3},
            {'id': 2, 'jp': 'x', 'en': ''},
        ]
        with tempfile.TemporaryDirectory() as d:
            src, out, wr = Path(d, 's.jsonl'), Path(d, 'o.csv'), Path(d, 'w.jsonl')
            src.write_text(''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in rows), encoding='utf-8')
            n_err = ct.run(['snmsg'], {'snmsg': src}, out, wr, False)
            self.assertEqual(n_err, 1)
            self.assertIn('snmsg,1,px,error', out.read_text(encoding='utf-8'))
            prop = [json.loads(x) for x in wr.read_text(encoding='utf-8').splitlines()]
            self.assertEqual(len(prop), 1)
            self.assertTrue(prop[0]['fits'])

    def test_dc_en_paralelo(self):
        row = {'id': 1, 'size': 100, 'fields': [{'off': 0, 'text': 'イルム'}, {'off': 48, 'text': 'イ'}],
               'en': ['Irm', 'A name much longer than the fifty one bytes that the last field has left']}
        with tempfile.TemporaryDirectory() as d:
            src = Path(d, 'dc.jsonl')
            src.write_text(json.dumps(row, ensure_ascii=False) + '\n', encoding='utf-8')
            got = list(ct.iter_rows('dc', src))
            self.assertEqual([(k, cap) for k, _, _, cap, _ in got], [('1@0', 47), ('1@48', 19)])   # option_dict.LAYOUT


if __name__ == '__main__':
    unittest.main()
