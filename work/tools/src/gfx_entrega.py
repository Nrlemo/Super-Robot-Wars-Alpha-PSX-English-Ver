"""Paquete de gráficos con texto para edición manual (#2, #17): exporta, valida lo devuelto y reinserta.

Uso:
  gfx_entrega.py export <dir>              editar/Gxx.png + guias/ + vistas/ + manifest.json + ACEPTACION.md
  gfx_entrega.py check <dir_png>           valida los Gxx.png devueltos contra los parámetros de aceptación
  gfx_entrega.py import <dir_png> <out>    check + escribe los archivos modificados en <out>/<ruta ISO>
                                           (WINTEX #1 también se trasplanta a WINDOW.TIM, zonas de rótulos)

Las piezas y sus parámetros están en PIECES; ACEPTACION.md se genera desde acá (no editarlo a mano).
"""
import csv
import json
import os
import sys

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lzpack  # noqa: E402
import tim  # noqa: E402

WORK = tim.WORK
REPO = os.path.dirname(WORK)

# Rótulos de WINTEX #1 (= WINDOW.TIM): (id, jp, x, y, w, h, sugerencia EN). Cajas medidas sobre el original;
# la del juego podría ser algo mayor, pero hasta ubicar el rectángulo en el código la caja medida es el límite.
LABELS = [
    ('L01', 'ユニット', 0, 114, 35, 13, 'Unit'),
    ('L02', 'パイロット', 62, 114, 46, 13, 'Pilot'),
    ('L03', 'レベル', 110, 114, 29, 13, 'Level / Lv.'),
    ('L04', '気力', 190, 114, 29, 13, 'Will'),
    ('L05', '命中', 222, 114, 29, 13, 'Hit'),
    ('L06', '武器名', 0, 138, 39, 13, 'Weapon'),
    ('L07', '攻撃力', 46, 138, 40, 13, 'Attack'),
    ('L08', '射程', 94, 138, 29, 13, 'Range / Rng'),
    ('L09', '勝利条件', 126, 138, 54, 13, 'Victory'),
    ('L10', '敗北条件', 182, 138, 54, 13, 'Defeat'),
    ('L11', '妖精', 0, 162, 27, 13, 'Fairy'),
    ('L12', '獲得経験値', 30, 162, 65, 13, 'EXP Gained'),
    ('L13', '命令内容', 102, 162, 53, 13, 'Orders'),
    ('L14', '強化パーツ', 158, 162, 54, 13, 'Parts'),
    ('L15', '主人公', 48, 178, 38, 13, 'Hero'),
    ('L16', '熟練度', 94, 178, 41, 13, 'Expert Pts'),
    ('L17', 'シナリオ', 141, 177, 37, 13, 'Stage'),
    ('L18', '修理費', 182, 177, 41, 13, 'Repair'),
    ('L19', '取得経験値', 182, 194, 65, 13, 'EXP'),
    ('I01', '反(撃)', 162, 2, 12, 12, 'C (Counter)'),
    ('I02', '防(御) (variante)', 178, 2, 12, 12, 'D (Defend)'),
    ('I03', '防(御)', 194, 2, 12, 12, 'D (Defend)'),
    ('I04', '避 (回避)', 210, 2, 12, 12, 'E (Evade)'),
    ('I05', '攻(撃)', 242, 2, 12, 12, 'A (Attack)'),
]

# Hojas de títulos: (índice TIM en SUBTITLE.BIN, ids de misiones.csv, títulos que solo existen como imagen)
SHEETS = [(2, range(1, 10), []), (3, range(10, 20), []), (4, range(20, 32), []), (5, range(32, 42), []),
          (6, range(42, 52), []), (7, range(52, 62), []), (8, range(62, 72), []), (9, range(72, 82), []),
          (10, range(82, 95), []), (11, range(95, 106), []),
          (12, range(106, 117), [('愛に時間を', 'Time for Love (propuesta)')]),
          (13, [117, 118, 119, 120, 122, 123, 124, 125, 126, 127, 128, 129],
           [('サイキック・エナジー', 'Psychic Energy (propuesta)')])]

T_SUB = ('Mismo diseño que el japonés: letra blanca con contorno oscuro, renglones de 24 px (glifo ≤ 23 px), '
         'hasta 10 renglones (y 0–239).')
R_SUB = [
    'Cada título (o fragmento) queda **en el mismo renglón** y **empieza en la misma x** (±2 px) que el japonés.',
    'Un título partido en dos renglones sigue partido en esos mismos dos renglones (el juego recorta fragmentos).',
    'Ningún fragmento pasa del borde derecho del fragmento japonés. Si no entra: usar `en_corto`, condensar la letra '
    'o avisarme para ampliar el rectángulo (requiere ubicar la tabla de recortes, #18).',
    'No mover títulos a otra hoja ni cambiar el orden.',
]

# Largo del prólogo desplazable (OVL/PRO_GRP.BIN, base 0x800D61D8). La rutina 0x800D62AC lee, por cada renglón que
# saca, una pausa de la tabla 0x800D87E8 (s16: 40 cuadros, 80 al cerrar párrafo, -1 = fin; 67 en el japonés, con
# datos pegados detrás). Parche: la tabla pasa a s8 (sll → nop, lhu → lb) → entran 135 renglones en los mismos 136 B.
PRO_OVL = 'OVL/PRO_GRP.BIN'
PRO_TABLE = 'prologo_pausas.json'           # lo escribe gfx_render.py render (G14–G17)
PRO_TABLE_OFF, PRO_TABLE_LEN = 0x2610, 136
PRO_TABLE_MAX = PRO_TABLE_LEN - 1
PRO_CODE = {0xF8: (0x00021040, 0x00000000),  # sll $v0,$v0,1 → nop
            0x100: (0x94420000, 0x80420000)}  # lhu $v0,0($v0) → lb $v0,0($v0)


def pro_patch(data, delays):
    """PRO_GRP.BIN con la tabla de pausas del prólogo en bytes (ver PRO_CODE)."""
    import struct
    if not delays or len(delays) > PRO_TABLE_MAX or any(not 0 < v < 128 for v in delays):
        sys.exit(f'{PRO_TABLE}: {len(delays)} pausas (1–{PRO_TABLE_MAX}, cada una 1–127)')
    out = bytearray(data)
    for off, (old, new) in PRO_CODE.items():
        if struct.unpack_from('<I', out, off)[0] != old:
            sys.exit(f'{PRO_OVL}: la instrucción en 0x{off:x} no es la esperada (¿otra versión?)')
        struct.pack_into('<I', out, off, new)
    old = struct.unpack_from(f'<{PRO_TABLE_LEN // 2}h', out, PRO_TABLE_OFF)
    if old[67] != -1:
        sys.exit(f'{PRO_OVL}: la tabla de pausas no está en 0x{PRO_TABLE_OFF:x}')
    tab = bytes(delays) + b'\xff'
    out[PRO_TABLE_OFF:PRO_TABLE_OFF + PRO_TABLE_LEN] = tab + b'\x00' * (PRO_TABLE_LEN - len(tab))
    return bytes(out)


PIECES = []
PIECES.append(dict(id='G01', file='TITLE/SUBTITLE.BIN', n=1, name='Número de escenario (0–9, 第, 話)',
                   prio='alta (bloquea títulos)', zones=[(0, 0, 208, 24)],
                   text=('Celdas: dígitos 0–9 de 16 px (x 0–159), 第 x 160–183, 話 x 184–207. El juego arma '
                         '「第 12 話」 con estas celdas.'),
                   rules=['Los dígitos pueden quedar como están (ya son arábigos).',
                          '**Decisión previa**: 第/話 → inglés. Las celdas son de 24×24, así que "Stage" no entra '
                          'en una celda. Opciones: (a) 第 = "No." / "#" y 話 vacío → "No.12"; (b) 第 vacío y '
                          '話 vacío (solo el número). Recomiendo (a) "#".',
                          'Cada celda conserva su ancho: no correr dígitos.']))
for k, (n, ids, extra) in enumerate(SHEETS):
    PIECES.append(dict(id=f'G{k + 2:02d}', file='TITLE/SUBTITLE.BIN', n=n, name=f'Títulos de escenario, hoja {k + 1}',
                       prio='media (esperar #18 si se puede)', zones=[(0, 0, 256, 240)], text=T_SUB, rules=R_SUB,
                       titles=(list(ids), extra)))
for k in range(4):
    PIECES.append(dict(
        id=f'G{14 + k:02d}', file=f'TEST/TXT3{k}.TIM', n=0, name=f'Prólogo, texto desplazable, página {k + 1}/4',
        prio='alta', zones=[(0, 0, 240, 252)],
        text=('Rollo continuo TXT30→TXT33 (4 páginas de 256 px, se muestran una debajo de otra). 21 renglones por '
              'página, **interlineado 12 px**, ancho útil **240 px** (x 0–239), glifo ≤ 11 px + contorno.'),
        rules=['El texto inglés fluye libremente de una página a la siguiente (84 renglones en total; import ajusta la tabla de pausas de PRO_GRP; el japonés '
               'usa 67). Ningún renglón puede quedar cortado entre dos páginas (y 252–255 vacío).',
               'Solo índices 1, 2, 3 (tonos del texto) y transparente. Mismo estilo: letra clara con borde.',
               'Contenido: traducción del prólogo (texto fuente: estas mismas imágenes; referencia de contenido en '
               '`info/` Akurasu "Story").']))
PIECES.append(dict(id='G18', file='TEST/PRO_FONT.TIM', n=0, name='Prólogo, cartel inicial (fecha / Excelion)',
                   prio='alta', zones=[(0, 52, 320, 188)],
                   text=('8 renglones centrados, letra serif blanca de ~18–22 px. Renglones 1–2 ("BANPRESTO PRESENTS", '
                         '"SUPER ROBOT WARS α") ya están en inglés: **no se tocan** (y < 52). Renglones 3–8 '
                         '(y 52–239): 新西暦一八六年十二月十四日 / 午前七時四十五分 / 太陽系第十番惑星・雷王星宙域 / '
                         '連邦特別宇宙軍SDF艦隊 / 第零番旗艦ヱクセリヲン / 正体不明ノ敵集団ト遭遇セリ.'),
                   rules=['Todo el texto dentro de x 8–312 (el cartel se ve a pantalla completa, 320×240).',
                          'Mismo estilo tipográfico (serif, centrado). Tono de parte militar/telegrama (homenaje a '
                          'Gunbuster: "…encountered unidentified enemy force").',
                          'Nombres: Excelion, Uranus (雷王星 = "Planet Rai-Ō", ver glosario), SDF.']))
PIECES.append(dict(id='G19', file='FONTWIN/WINTEX.BIN', n=1, name='Rótulos de interfaz (encabezados, iconos 反防避攻)',
                   prio='alta (resuelve #58)', zones=[z[2:6] for z in LABELS], labels=LABELS, window=True,
                   text=('Textura compartida de ventanas (4 bpp, 16 CLUT). Cada rótulo es un recorte fijo: '
                         'caja exacta en la tabla de abajo. Texto: relleno índice 5, contorno 2, antialias 1/3. '
                         'Transparentes: 0, 4, 9. `vistas/` muestra la textura con las otras 15 paletas.'),
                   rules=['Cada rótulo dentro de **su caja** (tabla). Fuera de las cajas no cambia ningún píxel '
                          '(lo valida `check`).',
                          'HP, EN, SP, MIN, EXP y los dígitos ya están en inglés: no se tocan.',
                          'Iconos I01–I05: 16×16 con marco; solo se redibuja el interior de 12×12 (índices 5/6 '
                          'sobre fondo 7). El ✕ queda.',
                          'Términos coherentes con los menús ya insertados (Will, Hit, Attack, Repair, Counter/'
                          'Defend/Evade). Si un término no entra, abreviar y anotarlo.',
                          'La misma edición se trasplanta sola a `FONTWIN/WINDOW.TIM` (difiere solo fuera de los '
                          'rótulos).']))
PIECES.append(dict(id='G20', file='TITLE/TITLEDAT.BIN', n=2, name='Copyright de la pantalla de título',
                   prio='baja (opcional)', zones=[(0, 0, 256, 202)],
                   text='12 renglones de 16 px (letra ~13 px), alineados a x = 5.',
                   rules=['Romanizar/inglés según los créditos oficiales en inglés de cada licencia (p. ej. '
                          '"© Go Nagai / Dynamic Planning", "© Sotsu Agency · Sunrise"). Ver '
                          '`traduccion/referencia/creditos_y_canciones.md`.',
                          'Máximo 12 renglones, x 5–251.']))
PIECES.append(dict(id='G21', file='TITLE/TITLEDAT.BIN', n=4, name='Logo スーパーロボット大戦α',
                   prio='opcional (recomiendo dejarlo)', zones=[(0, 0, 256, 240)],
                   text=('8 bpp, 256 colores. Es solo una parte del logo (la cola de la α sigue en otro recorte). '
                         'Los parches de fans suelen conservar el logo japonés.'),
                   rules=['Si se reemplaza: paleta fija de 256 colores, mismo tamaño y posición; la α debe empalmar '
                          'con el resto del logo.']))

# --- Segunda tanda (2026-09-28): gráficos dentro de contenedores LZSS (lzpack.py) ---
# Rótulos de efectos especiales de batalla, BATTLE/COMMON.BIN entrada 1: (id, jp, x, y, w, h, EN del glosario)
EFFECTS = [
    ('E01', 'クリティカル', 27, 1, 42, 14, 'Critical!'),
    ('E02', 'シールド防御', 100, 1, 55, 14, 'Shield Defense'),
    ('E03', '分身', 190, 1, 36, 14, 'After Image'),
    ('E04', 'ゲッタービジョン', 16, 17, 64, 14, 'Getter Vision'),
    ('E05', 'マッハスペシャル', 96, 17, 65, 14, 'Mach Special'),
    ('E06', '真マッハスペシャル', 169, 17, 77, 14, 'Shin Mach Special'),
]
PIECES.append(dict(id='G22', file='BATTLE/COMMON.BIN', entry=1, n=0, name='Batalla: rótulos de efectos especiales',
                   prio='alta', zones=[z[2:6] for z in EFFECTS], labels=EFFECTS,
                   text=('Hoja de efectos de batalla; los 6 rótulos están en los dos primeros renglones (13 px de '
                         'alto, letra con degradé). Resto de la hoja: efectos, no se toca.'),
                   rules=['Cada rótulo dentro de **su caja** (tabla). La caja es la extensión del japonés: el '
                          'rectángulo real del juego todavía no está ubicado; si un texto no entra, abreviar '
                          '(p. ej. "Shield Def.", "Critical!") y anotarlo.',
                          'Mismos índices del original (degradé de relleno + contorno índice 1).']))
BARRIERS = [(5, 'ATフィールド', 'AT Field'), (7, 'オーラバリア', 'Aura Barrier'),
            (9, 'グラビティ・テリトリー', 'Gravity Territory'), (11, 'ピンポイントバリア', 'Pinpoint Barrier'),
            (13, 'グラビティ・ウォール', 'Gravity Wall'), (15, '念動フィールド', 'Telekinesis Field'),
            (17, 'イナーシャルキャンセラー', 'Inertial Canceller'), (19, 'Ｉフィールド (rosa oscuro)', 'I-Field'),
            (21, 'Ｉフィールド (rosa)', 'I-Field'), (23, 'ビームコーティング', 'Beam Coat')]
for k, (e, jp, en) in enumerate(BARRIERS):
    PIECES.append(dict(id=f'G{23 + k:02d}', file='BATTLE/COMMON.BIN', entry=e, n=0,
                       name=f'Batalla: barrera {jp}', prio='alta', zones=[(0, 160, 80, 16)],
                       text=(f'Rótulo de la barrera en la franja y 161–174 (13 px de alto), x ≤ 80. Inglés del '
                             f'glosario: **{en}**. El resto de la hoja es el efecto de la barrera: no se toca.'),
                       rules=['Solo dentro de la caja (0, 160, 80×16). Si no entra, letra condensada o abreviatura '
                              '(p. ej. "Grav. Territory"); el rectángulo real del juego está sin ubicar.',
                              'Mismo estilo: degradé del color de la barrera + contorno índice 1.']))
# Rótulos de avisos del mapa (#271): SNMAP/KIEFETIM.BIN entrada 3, tabla de offsets con relleno (lzpack.table). Los renglones
# se regeneran con kief_labels.py (modelo de copias/bandas verificado); zonas = las 4 áreas con rótulos de la hoja.
PIECES.append(dict(id='G37', file='SNMAP/KIEFETIM.BIN', entry=3, n=0, name='Mapa: rótulos de avisos (crítico, barreras, escudo)',
                   prio='alta', zones=[(0, 7, 251, 57), (0, 71, 240, 57), (0, 135, 240, 57), (0, 195, 192, 45)],
                   text=('Hoja de 256×256 con los rótulos que salen sobre las unidades del mapa con "Animation: OFF": barreras, '
                         '斬り払い, 分身 y クリティカル (BARRIER HIT!! y SHIELD MISS! ya están en inglés). Cada rótulo existe en '
                         'varias copias (animación de despliegue).'),
                   rules=['No se edita a mano: `kief_labels.py render` regenera todas las copias desde work/gfx/render/G37.csv '
                          '(mayúsculas de 5 renglones, estilo de BARRIER HIT!!).']))
MAPS = [(1, 'hoja 1 (Japón)'), (3, 'hoja 2 (Tierra)'), (5, 'hoja 3 (espacio; también entrada 7, idéntica)'),
        (9, 'hoja 4 (Sistema Solar)')]
for k, (e, what) in enumerate(MAPS):
    PIECES.append(dict(id=f'G{33 + k:02d}', file='BUSTUP/MAP.BIN', entry=e, n=0, also=[7] if e == 5 else [],
                       name=f'Intermisión: mapa "現在位置", nombres de lugares, {what}', prio='media',
                       zones=[(0, 0, 256, 240)],
                       text=('Cabecera (y 0–25): marcadores ▼ y 「現在位置」 (→ "Current Location" / "Location"). '
                             'Debajo, nombres de lugares en **renglones de 16 px desde y = 33**, en dos columnas '
                             '(la derecha empieza en x variable). 「移動中」 → "In Transit". Nombres: '
                             '`traduccion/referencia/lugares.csv` (80 lugares con su inglés).'),
                       rules=['Cada nombre en su mismo renglón, misma x inicial (±2 px) y sin pasar el borde derecho '
                              'del japonés: el juego recorta cada nombre con una tabla que todavía no ubiqué '
                              '(igual que los títulos, #18).',
                              'Los marcadores ▼ de la cabecera no se tocan.',
                              'Mismo estilo: letra naranja con contorno (índices del original).']))


def load(p):
    data = open(os.path.join(tim.ISO, p['file']), 'rb').read()
    if 'entry' in p:
        data = lzpack.read(data)[p['entry']]['raw']
    return data, tim.scan(data)[p['n']]


def where(p):
    return (f"entrada {p['entry']} (LZSS), " if 'entry' in p else '') + f"TIM #{p['n']}"


def transparent(data, t):
    return {i for i, v in enumerate(tim.cluts(data, t)[0]) if v == 0}


def zone_mask(p, shape):
    m = np.zeros(shape, bool)
    for x, y, w, h in p['zones']:
        m[max(0, y - 1):y + h + 1, max(0, x - 1):x + w + 1] = True
    return m


def missions():
    return {int(r['titulo_id']): r for r in csv.DictReader(open(os.path.join(REPO, 'traduccion', 'referencia',
                                                                              'misiones.csv')))}


def guide(p, data, t, out):
    idx = tim.indices(data, t)
    im = Image.fromarray(tim.bgr555(tim.cluts(data, t)[0][idx]), 'RGBA')
    bg = Image.new('RGBA', im.size, (70, 70, 80, 255))
    bg.alpha_composite(im)
    s = 3 if im.width <= 256 else 2
    bg = bg.resize((im.width * s, im.height * s), Image.NEAREST)
    d = ImageDraw.Draw(bg)
    if p.get('titles'):
        for r in range(11):
            d.line([(0, r * 24 * s), (bg.width, r * 24 * s)], fill=(0, 255, 255, 255))
    if p.get('labels'):
        for lid, jp, x, y, w, h, en in p['labels']:
            d.rectangle([x * s, y * s, (x + w) * s - 1, (y + h) * s - 1], outline=(0, 255, 0, 255))
            d.text((x * s + 1, (y + h) * s), lid, fill=(255, 255, 0, 255))
    elif p['id'] in ('G14', 'G15', 'G16', 'G17'):
        for r in range(22):
            d.line([(0, r * 12 * s), (240 * s, r * 12 * s)], fill=(0, 255, 255, 110))
        d.rectangle([0, 0, 240 * s - 1, 252 * s - 1], outline=(0, 255, 0, 255))
    else:
        for x, y, w, h in p['zones']:
            d.rectangle([x * s, y * s, (x + w) * s - 1, (y + h) * s - 1], outline=(0, 255, 0, 255))
    if p['id'] == 'G01':
        for x in list(range(0, 161, 16)) + [184, 208]:
            d.line([(x * s, 0), (x * s, bg.height)], fill=(0, 255, 255, 255))
    bg.save(out)


def export(outdir):
    for sub in ('editar', 'guias', 'vistas', 'original'):
        os.makedirs(os.path.join(outdir, sub), exist_ok=True)
    man, mis = [], missions()
    for p in PIECES:
        data, t = load(p)
        idx, cl = tim.indices(data, t), tim.cluts(data, t)
        png = f"editar/{p['id']}.png"
        for dst in (png, f"original/{p['id']}_jp.png"):
            tim.save_png(tim.indexed_png(idx, cl[0]), os.path.join(outdir, dst))
        for k in range(1, cl.shape[0]) if p.get('window') else []:
            tim.save_png(tim.indexed_png(idx, cl[k]), os.path.join(outdir, f"vistas/{p['id']}_clut{k:02d}.png"))
        guide(p, data, t, os.path.join(outdir, f"guias/{p['id']}_guia.png"))
        man.append({'id': p['id'], 'file': p['file'], 'entry': p.get('entry'), 'n': p['n'], 'off': t['off'], 'bpp': t['bpp'], 'w': t['w'],
                    'h': t['h'], 'png': png, 'zones': p['zones']})
    json.dump(man, open(os.path.join(outdir, 'manifest.json'), 'w'), indent=1, ensure_ascii=False)
    write_md(outdir, mis)
    return man


def write_md(outdir, mis):
    L = ['# Gráficos con texto — entrega para edición manual', '',
         'Generado por `work/tools/src/gfx_entrega.py export` desde la ISO japonesa. Issues: #2, #17–#20, #58.', '',
         '## Qué hay en esta carpeta', '',
         '| Carpeta | Contenido |', '|---|---|',
         '| `editar/` | **Los PNG a editar** (`Gxx.png`). Devolvé estos mismos archivos, con el mismo nombre. |',
         '| `original/` | Copia intacta del japonés, para comparar. |',
         '| `guias/` | Ampliación ×3 (×2 si es ancha) con las zonas permitidas (verde), renglones (celeste) e ids. |',
         '| `vistas/` | Solo G19: la textura con las otras 15 paletas (colores que usa el juego en cada ventana). |',
         '| `manifest.json` | Para la reinserción (no tocar). |', '',
         '## Reglas generales (todas las piezas)', '',
         '1. **PNG indexado** (modo "Indexed"/paleta), **mismo tamaño en px**, **misma paleta** (mismos colores en el '
         'mismo orden). No convertir a RGB; no optimizar ni reordenar la paleta al guardar. En GIMP: Imagen → Modo → '
         'Indexado ya viene así; exportar sin "optimizar paleta". En Aseprite/Photoshop: modo Indexed, paleta bloqueada.',
         '2. **Sin colores nuevos**: solo los de la paleta. Si hace falta un color que no está, avisame (la paleta '
         'está compartida en VRAM con otros gráficos y cambiarla es otro trabajo).',
         '3. **Transparencia**: el color transparente es el de valor 0x0000 (en el PNG, entrada con alfa 0; en '
         '`original/` se ve como fondo vacío). Todo lo que no sea texto nuevo queda transparente o igual al original.',
         '4. **Fuera de las zonas permitidas no cambia ningún píxel** (lo valida el script).',
         '5. Nombres y términos: glosario (`work/glossary/glossary.csv`), `traduccion/referencia/*.csv` y lo ya '
         'insertado en menús. Si hay que abreviar, anotarlo en `notas.txt` junto a los PNG.',
         '6. Estética: imitar el estilo del original (grosor, contorno, sombreado, antialias con los mismos índices). '
         'Pixel art a 1×: nada de escalar con suavizado.', '',
         '## Cómo lo valido cuando me lo devuelvas', '',
         '```', 'work/.venv/bin/python work/tools/src/gfx_entrega.py check <carpeta_con_los_Gxx.png>', '```', '',
         'Rechaza automáticamente: tamaño distinto, PNG no indexado, paleta cambiada, índice fuera de la paleta, '
         'píxeles modificados fuera de las zonas, índices no permitidos (G14–G17). Después la prueba es en el juego '
         '(build + captura en la pantalla correspondiente); ahí se revisa legibilidad y recorte.', '',
         '## Resumen de piezas', '', '| Id | Archivo (entrada / TIM) | Qué es | Tamaño | Prioridad |', '|---|---|---|---|---|']
    for p in PIECES:
        data, t = load(p)
        L.append(f"| {p['id']} | `{p['file']}` {where(p)} | {p['name']} | {t['w']}×{t['h']}, {t['bpp']} bpp, "
                 f"{t['clut']['wh'][0]} colores | {p['prio']} |")
    L += ['', '## Parámetros de aceptación por pieza', '']
    for p in PIECES:
        data, t = load(p)
        tr = sorted(transparent(data, t))
        L += [f"### {p['id']} — {p['name']}", '',
              f"- Archivo: `{p['file']}` ({where(p)}, offset 0x{t['off']:X}); VRAM {t['vram_xy']}.",
              f"- Tamaño exacto: **{t['w']}×{t['h']} px**, {t['bpp']} bpp, paleta de {t['clut']['wh'][0]} colores "
              f"(índices transparentes: {tr}).",
              f"- Zonas editables (x, y, ancho, alto): " + ('ver tabla de rótulos' if p.get('labels') else
                                                            ', '.join(f'({x}, {y}, {w}, {h})' for x, y, w, h in p['zones'])) + '.',
              f"- Texto: {p['text']}", '- Aceptación:']
        L += [f'  - {r}' for r in p['rules']]
        if p.get('labels'):
            L += ['', '| Id | JP | Caja x, y, ancho × alto | Sugerencia EN |', '|---|---|---|---|']
            L += [f'| {a} | {b} | {x}, {y}, {w}×{h} | {e} |' for a, b, x, y, w, h, e in p['labels']]
        if p.get('titles'):
            ids, extra = p['titles']
            L += ['', '| Id | JP | EN (aprobado) | EN corto |', '|---|---|---|---|']
            for i in ids:
                r = mis[i]
                L.append(f"| {i} | {r['jp']} | {r['en']} | {r['en_corto']} |")
            L += [f'| — | {jp} | {en} — *solo existe como imagen (escenario cortado)* | |' for jp, en in extra]
        L.append('')
    L += ['## Gráficos vistos y excluidos (con motivo)', '',
          '| Archivo | Motivo |', '|---|---|',
          '| `FONTWIN/WINTEX.BIN` #0 | Es la fuente del juego: la genera `font_build.py` (ya en inglés). |',
          '| `FONTWIN/WINDOW.TIM` | Copia de G19 con otros medidores: se actualiza sola desde G19. |',
          '| `TITLE/ENTRYDAT.BIN` #1–#8 | Grilla de kanji/kana para ingresar el nombre del protagonista: es una tabla '
          'de caracteres, no un rótulo. Cambiarla a A–Z requiere trabajo técnico (#16/#20). |',
          '| `TITLE/TITLEDAT.BIN` #6, #8, #9; `WINTEX.BIN` #2 | "PRESS ANY BUTTON", START/LOAD/CONTINUE/OPTION, '
          '"LOADING": ya en inglés. |',
          '| `FONTWIN/TITLEDAT.BIN`, `CPYLGT_*.TIM`, `ROGO.TIM`, `START_1.TIM`, `BANPRE*.TIM`, `TEST/EFE.TIM` | '
          'Ningún código los nombra (restos de desarrollo). Los rótulos de barreras que usa el juego son G23–G32 '
          '(`BATTLE/COMMON.BIN`). |',
          '| `SNMAP/MW.BIN`, `SPEFE.BIN`, `UTIM4.BIN`, `MTIM.BIN`, `FONTWIN/IMBG.BIN`, `TEST/MTIM.BIN`, '
          '`BUSTUP/BACK.BIN`, `CHARA.BIN`, `BATTLE/UNIT.BIN`, fondos | Sin texto (efectos, sprites, retratos, mapas, '
          'fondos de escena). Lo que el parche chino "cambió" en `CHARA.BIN`/`UNIT.BIN` son datos pisados, no '
          'traducciones. |',
          '| `BATTLE/BATTLE.WAC`, `FONTWIN/WINDATA*.DAT` | No son gráficos: tabla de datos de batalla y geometría '
          'de ventanas (registros id, x, y, ancho, alto). |', '']
    open(os.path.join(outdir, 'ACEPTACION.md'), 'w').write('\n'.join(L))


def check_one(p, png):
    data, t = load(p)
    errs = []
    try:
        new = tim.png_to_bytes(data, t, png)
    except ValueError as x:
        return [str(x)], None
    tmp = bytearray(data)
    tmp[t['pix_off']:t['pix_off'] + len(new)] = new
    a, b = tim.indices(data, t), tim.indices(bytes(tmp), t)
    ch = a != b
    out = ch & ~zone_mask(p, a.shape)
    if out.any():
        ys, xs = np.where(out)
        errs.append(f'{int(out.sum())} píxeles cambiados fuera de las zonas (p. ej. x={xs[0]}, y={ys[0]})')
    if p['id'] in ('G14', 'G15', 'G16', 'G17'):
        bad = set(np.unique(b[ch]).tolist()) - {1, 2, 3} - transparent(data, t)
        if bad:
            errs.append(f'índices no permitidos en el texto: {sorted(bad)} (solo 1, 2, 3 y transparente)')
    return errs, int(ch.sum())


# Archivos que ya no se reinsertan desde PNG: los genera otra herramienta (los PNG de esas piezas se ignoran)
OWNED = {'TITLE/SUBTITLE.BIN': 'subtitle.py (etapa titles, #18: hojas reempaquetadas con la tabla de recortes)'}


def pieces_in(pngdir):
    """Piezas con PNG en pngdir, sin las de archivos de OWNED (avisa una vez por archivo)."""
    out, told = [], set()
    for p in PIECES:
        if not os.path.exists(os.path.join(pngdir, p['id'] + '.png')):
            continue
        if p['file'] in OWNED:
            if p['file'] not in told:
                print(f"{p['file']}: se ignoran sus PNG (lo genera {OWNED[p['file']]})")
                told.add(p['file'])
            continue
        out.append(p)
    return out


def check(pngdir):
    ok = True
    for p in pieces_in(pngdir):
        png = os.path.join(pngdir, p['id'] + '.png')
        errs, n = check_one(p, png)
        ok &= not errs
        print(f"{p['id']}: " + ('OK' if not errs else 'RECHAZADO') + (f' ({n} píxeles cambiados)' if n is not None else ''))
        for e in errs:
            print('   -', e)
    return ok


def import_(pngdir, outdir, base=None):
    """base: carpeta con archivos ya modificados por otra etapa (p. ej. WINTEX.BIN de "font"); si un archivo está
    ahí se parte de esa versión en vez del japonés (las imágenes tienen que seguir en el mismo offset)."""
    def origen(rel):
        b = os.path.join(base, rel) if base else None
        return b if b and os.path.exists(b) else os.path.join(tim.ISO, rel)
    if not check(pngdir):
        sys.exit('hay piezas rechazadas: no se reinserta nada')
    files, ents = {}, {}  # archivo → bytes; (archivo, entrada) → TIM descomprimido modificado
    for p in pieces_in(pngdir):
        png = os.path.join(pngdir, p['id'] + '.png')
        if p['file'] not in files:
            files[p['file']] = bytearray(open(origen(p['file']), 'rb').read())
        if 'entry' in p:
            key = (p['file'], p['entry'])
            if key not in ents:
                ents[key] = bytearray(load(p)[0])
            buf = ents[key]
        else:
            buf = files[p['file']]
        ref = load(p)[1]
        t = tim.parse(bytes(buf), ref['off'])
        if (t['w'], t['h'], t['pix_off']) != (ref['w'], ref['h'], ref['pix_off']):
            sys.exit(f"{p['id']}: la imagen se movió en {origen(p['file'])} (base de otra etapa): no se reinserta")
        new = tim.png_to_bytes(bytes(buf), t, png)
        buf[t['pix_off']:t['pix_off'] + len(new)] = new
        for extra in p.get('also', []):  # entradas idénticas (MAP.BIN 5 = 7)
            ents[(p['file'], extra)] = buf
        if p.get('window'):  # trasplante a WINDOW.TIM: solo las cajas de los rótulos
            w = bytearray(open(origen('FONTWIN/WINDOW.TIM'), 'rb').read())
            tw = tim.parse(bytes(w))
            src, dst = tim.indices(bytes(buf), t), tim.indices(bytes(w), tw).copy()
            m = zone_mask(p, dst.shape)
            dst[m] = src[m]
            pk = dst.reshape(tw['h'], -1, 2)
            b = (pk[..., 0] | (pk[..., 1] << 4)).astype(np.uint8).tobytes()
            w[tw['pix_off']:tw['pix_off'] + len(b)] = b
            files['FONTWIN/WINDOW.TIM'] = w
    table = os.path.join(pngdir, PRO_TABLE)
    if os.path.exists(os.path.join(pngdir, 'G14.png')):
        if not os.path.exists(table):
            sys.exit(f'falta {table} (correr gfx_render.py render G14): sin él el juego corta el prólogo')
        files[PRO_OVL] = pro_patch(open(origen(PRO_OVL), 'rb').read(), json.load(open(table)))
    for rel in {f for f, _ in ents}:
        repl = {e: bytes(b) for (f, e), b in ents.items() if f == rel}
        files[rel], warn = lzpack.build(bytes(files[rel]), repl)
        for x in warn:
            print(f'AVISO {rel}: {x}')
    for rel, buf in files.items():
        dst = os.path.join(outdir, rel)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        open(dst, 'wb').write(buf)
        print('escrito', dst)


if __name__ == '__main__':
    cmd = sys.argv[1] if len(sys.argv) > 1 else ''
    if cmd == 'export':
        print(len(export(sys.argv[2])), 'piezas exportadas en', sys.argv[2])
    elif cmd == 'check':
        sys.exit(0 if check(sys.argv[2]) else 1)
    elif cmd == 'import':
        import_(sys.argv[2], sys.argv[3], sys.argv[4] if len(sys.argv) > 4 else None)
    else:
        print(__doc__)
