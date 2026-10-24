"""Protagonista y pareja (#16): pantalla de ingreso (OVL/ENTR_GRP.BIN) y nombre completo en inglés.

Formato (verificado 2026-09-28 en el emulador; ver notes/nombres_protagonistas.md §7):
  ENTR carga en 0x8011308C (dirección = offset en el archivo + 0x8011308C).
  Tabla por defecto: 8 registros de 0x48 desde 0x80123184 (el orden de "登録キャラクターから選択"):
    +0x00 nombre · +0x15 apellido · +0x2A apodo (0x15 B c/u, NUL) · +0x3F 0 · +0x40 mes · +0x41 día
    +0x42 sangre (0 A, 1 B, 2 AB, 3 O) · +0x43 sexo (0 hombre, 1 mujer) · +0x44/+0x45 personalidad (0..3)
    +0x46 ? (0/1) · +0x47 orden del nombre (0 欧米読み = nombre apellido, 1 日本読み = apellido nombre).
    Mismo layout que la estructura en RAM (protagonista 0x8006E90C; punteros *0x8005C248 / *0x8005C24C).
  Editor de nombre (名前登録): S = *0x8012A41C; campo 0 apellido, 1 nombre, 2 apodo; arreglos de 9 casilleros de
    6 B (8 + terminador) en S+0x43C4 + campo·0x36; cursor S+0x4466 + campo·2; índice máximo S+0x446C + campo·2.
    0x8011B208 los carga con 0x8011B158(casilleros, texto, tope) = 8 / 8 / 4 y fija los máximos 7 / 7 / 3;
    0x80119B58(campo) da el largo útil (tope 4 si campo = 2, si no 8) al pasar casilleros → texto.
  En 英数 el juego guarda ASCII puro ('k' = 0x6B): el teclado ya sirve para inglés.
  Nombre completo: los menús usan "%s%s" (日本読み) y "%s=%s" (欧米読み) en ENTR, IMIS, PRM y TITL (una sola
    rutina por overlay); en el mapa, el expansor de SNMP_GRP (0x800E50F8: $n/$s/$m/$f protagonista, $N/$S/$M/$F
    pareja) arma nombre + "＝" (0x800D6950) + apellido, o apellido + nombre sin separador.

Qué aplica (topes 8/8/8, decisión 2026-09-28):
  ENTR  1. Apodo 4 → 8 (el arreglo ya tiene 9 casilleros): 0x8011B240, 0x8011B274 y 0x80119B64.
        2. Recorte seguro al cargar el editor (bucle de 0x8011B17C): antes convertía hasta el NUL y un valor de
           9 letras ("Luckfield") pisaba el primer casillero del nombre (nombre vacío y cuelgue al escribir). Ahora
           se ve entero en el juego y solo pierde lo que sobra si el jugador abre el editor y confirma.
        3. Nombres por defecto en inglés desde translation/entry_en.csv (espacios → 0xA0, como pilot_bin.py).
        4. (#276) Topes del apodo que quedaban en 4: cursor al cambiar de campo (0x80119B48) y corrimiento al borrar
           (0x80119F04). Barra de botones del editor (0x80114D24) rellena con 0x20 para que cada palabra quede
           después de su ícono.
  ENTR, IMIS, PRM, TITL: "%s%s" y "%s=%s" → "%s %s" (espacio 0xA0; "%s%s" tiene 4 bytes de relleno). ENTR tiene
        un 2.º "%s=%s" (ficha del protagonista, #276).
  TITL, SNDM (#276): x de la ficha "Edit Main Character" (Birthday/Blood a 102, título y "Face" centrados, valores a
        144), del calendario (Oct–Dec a 52, "Confirm" a 221) según el ancho real del inglés.
  SNMP  "＝" → " " y el orden 日本読み de $f/$F pasa por el mismo camino con los registros cruzados
        (apellido + espacio + nombre).
Cada cambio se compara con el original antes de aplicarse: si un overlay no es el esperado, sale con error.

Uso:
  entry_patch.py build <dir_entrada|-> <dir_salida>   {ENTR,SNMP,TITL,IMIS,PRM}_GRP.BIN desde dir_entrada (la
                                                      salida de la etapa "menus"; si falta uno, iso_jp/OVL)
  entry_patch.py dump                                 → la tabla por defecto del japonés
"""
import csv, os, struct, sys

from sjis_text import decode

WORK = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
ISO_OVL = os.path.join(WORK, 'iso_jp', 'OVL')
CSV = os.path.join(WORK, 'translation', 'entry_en.csv')
BASE = {'ENTR': 0x8011308C, 'SNMP': 0x800D61D8, 'SNDM': 0x800D61D8, 'IMIS': 0x800D61D8, 'PRM': 0x800A8920,
        'SNDU': 0x8011308C}
TABLE, RSIZE, COUNT = 0x80123184, 0x48, 8
FIELDS = (('first', 0x00), ('last', 0x15), ('nick', 0x2A))
FIELD_MAX = 20                  # 0x15 bytes con el NUL
EDIT_MAX = 8                    # casilleros del editor por campo (nombre, apellido y apodo)
EN_SPACE = b'\xa0'              # espacio angosto del inglés (notes/fuente_en.md)

ZERO, V0, V1, A0, A1, A2, T0, S0, S1, S2, S4 = 0, 2, 3, 4, 5, 6, 8, 16, 17, 18, 20


def li(rt, imm):
    return 0x24000000 | rt << 16 | imm                     # addiu rt, $zero, imm


def move(rd, rs):
    return rs << 21 | rd << 11 | 0x21                      # addu rd, rs, $zero


def jump(op, target):
    return op << 26 | (target >> 2) & 0x3FFFFFF            # j (2) / jal (3)


def branch(op, rs, pc, target):
    return op << 26 | rs << 21 | ((target - pc - 4) >> 2) & 0xFFFF   # beqz (4) / bnez (5)


def words(*ws):
    return b''.join(struct.pack('<I', w) for w in ws)


# (overlay, dirección, bytes originales, bytes nuevos, qué)
CODE = [
    ('ENTR', 0x8011B240, words(li(V1, 3)), words(li(V1, 7)), 'índice máximo del apodo 3 → 7'),
    ('ENTR', 0x8011B274, words(li(A2, 4)), words(li(A2, 8)), 'casilleros del apodo al cargar 4 → 8'),
    ('ENTR', 0x80119B64, words(li(A2, 4)), words(li(A2, 8)), 'largo del apodo al pasar casilleros → texto 4 → 8'),
    ('ENTR', 0x8011B17C,
     bytes.fromhex('01003126c36b040c21280002212040000000829000000000f9ff4014060010262a1032021200401000000000'),
     words(move(A1, S0),                         # b17c casillero destino
           jump(3, 0x8011AF0C),                  # b180 jal: convierte 1 carácter, v0 = siguiente
           0x24000000 | S1 << 21 | S1 << 16 | 1,  # b184 (retardo) s1++
           move(A0, V0),                         # b188
           0x90000000 | V0 << 21 | V1 << 16,     # b18c lbu v1, 0(v0): próximo carácter
           0x24000000 | S0 << 21 | S0 << 16 | 6,  # b190 s0 += 6
           S1 << 21 | S2 << 16 | V0 << 11 | 0x2A,  # b194 slt v0, s1, s2
           branch(4, V0, 0x8011B198, 0x8011B1EC),  # b198 tope alcanzado → terminador y fin
           0,
           branch(5, V1, 0x8011B1A0, 0x8011B17C),  # b1a0 quedan caracteres → bucle
           0),                                   # b1a4 fin del texto con s1 < s2 → relleno con espacios
     'la carga del editor corta en el tope (8/8/8)'),
    # $f / $F con 日本読み: en vez de strcpy(apellido) + strcat(nombre), cruzar s0/s1 y seguir por el camino de
    # 欧米読み (strcpy(s0) + strcat(separador) + strcat(s1)) → "apellido nombre"
    *[('SNMP', a, words(jump(3, 0x8002140C), move(A1, S1), move(A0, S2), jump(2, 0x800E5284), move(A1, S0)),
       words(move(T0, S0), move(S0, S1), jump(2, 0x800E5264), move(S1, T0), 0), f'{who}: 日本読み con espacio')
      for a, who in ((0x800E51F8, '$f'), (0x800E5250, '$F'))],
    ('SNMP', 0x800D6950, b'\x81\x81\x00\x00', EN_SPACE + b'\x00\x00\x00', 'separador de $f/$F: ＝ → espacio'),
    # Escenas (#224): al empezar la escena 0x800DB880 llama 6 veces a 0x800DB860(this, origen, destino) para pasar el
    # nombre/apellido/apodo del protagonista y la pareja a SJIS de ancho completo (tabla de 0x9E entradas, sin 0xA0):
    # el inglés salía a 12 px ("B u l l e t"). Se reemplaza por strcpy(destino, origen) de cola.
    ('SNDM', 0x800DB860, bytes.fromhex('0000c0a09f000d24'), words(jump(2, 0x8002140C), move(A0, A2)),
     'conversor a ancho completo → strcpy (nombres de escena en ASCII/VWF)'),
    ('SNDM', 0x800D65C8, b'\x81\x81\x00\x00', EN_SPACE + b'\x00\x00\x00', 'separador nombre＝apellido de escenas: ＝ → espacio'),
    # Escritura letra a letra de las escenas (#287): el intérprete de eventos de SNDM_GRP (0x800E0574) deja visibles de
    # golpe los glifos que hay antes del primer 「 (o （) del texto, contando de a 2 bytes, y el resto se revela de a uno;
    # 「 también enciende el bit 0x1000 del evento. El inglés no tiene 「: el bucle recorría todo, no encontraba nada
    # y mostraba la línea entera. Ahora se cuenta de a 1 byte hasta el primer ':' (el nombre del hablante), que se
    # muestra junto con el ':' y el espacio; 0x0A no cuenta (no tiene glifo) y sin ':' queda todo visible, como antes.
    ('SNDM', 0x800E0B74, bytes.fromhex('21202002106b6526ff84000c020006240a004010212020020d80053c146ba524ff84000c02000624080040100100522601009426d582030802003126'),
     words(0x90000000 | S1 << 21 | V0 << 16,                        # b74 lbu v0,0(s1)
           branch(4, V0, 0x800E0B78, 0x800E0BC0),                    # b78 fin del texto → s4 ya contado
           0x24030000 | 0x3A,                                        # b7c li v1,':'
           0x10000000 | V0 << 21 | V1 << 16 | ((0x800E0BA0 - 0x800E0B84) >> 2),   # b80 ':' → ba0
           0x24030000 | 0x0A,                                        # b84 li v1,0x0A
           0x10000000 | V0 << 21 | V1 << 16 | ((0x800E0B54 - 0x800E0B8C) >> 2) & 0xFFFF,   # b88 salto de línea → b54
           0x24000000 | S1 << 21 | S1 << 16 | 1,                     # b8c (retardo) s1++
           0x24000000 | S2 << 21 | S2 << 16 | 1,                     # b90 s2++ (glifo)
           jump(2, 0x800E0B54),                                      # b94 j b54
           0x24000000 | S4 << 21 | S4 << 16 | 1,                     # b98 (retardo) s4++ (visible)
           0,                                                        # b9c
           0x24000000 | S4 << 21 | S4 << 16 | 2,                     # ba0 s4 += 2 (':' y el espacio)
           jump(2, 0x800E0BB0),                                      # ba4 j bb0: enciende el bit 0x1000 del evento
           0, 0),                                                    # ba8, bac
     'SCRIPT: texto de escena letra a letra con el nombre del hablante «Nombre: …» (sin 「）'),
    # Valor "Type" de la ficha de unidad (空 水 陸 地中 / 宇宙): la rutina junta las etiquetas y rellena a la izquierda con
    # (4 − celdas) "　" para alinear a 4 celdas de kanji. Con etiquetas en inglés (ancho variable) el relleno las empuja
    # fuera del marco: blez s1 → b (se omite el bucle de relleno). IMIS 0x13164, PRM 0x1C020, SNDU 0x2CFC.
    ('IMIS', 0x800E933C, bytes.fromhex('0a00201a'), bytes.fromhex('0a000010'), 'Type: sin relleno de celdas (blez → b)'),
    ('PRM', 0x800C4940, bytes.fromhex('0900201a'), bytes.fromhex('09000010'), 'Type: sin relleno de celdas (blez → b)'),
    ('SNDU', 0x80115D88, bytes.fromhex('0900201a'), bytes.fromhex('09000010'), 'Type: sin relleno de celdas (blez → b)'),
    # #276: dos topes del apodo que quedaron en 4. 0x80119AC0(campo) da la casilla del cursor al cambiar de campo
    # (cuenta casilleros; con campo = 2 devolvía 3 fijo) y 0x80119EE8 corre los casilleros al borrar (máx. 3 → 7).
    ('ENTR', 0x80119B48, words(li(V0, 3)), words(move(V0, A1)), 'cursor al pasar al apodo: 3 fijo → cuenta como los otros'),
    ('ENTR', 0x80119F04, words(li(A2, 3)), words(li(A2, 7)), 'borrar en el apodo: corre hasta el casillero 7 (era 3)'),
    # #276: rayitas azules bajo los casilleros (0x8011CF64, sprites de 8×2): con campo = 2 el bucle cortaba en el
    # casillero 3 → solo 4 rayitas bajo el apodo.
    ('ENTR', 0x8011D144, words(li(V0, 3)), words(li(V0, 7)), 'rayitas del apodo: 4 → 8'),
    # #280: las letras de medio ancho del editor (0x8011CAB8), del teclado (0x8011B79C) y de la columna de opciones
    # (Western/Uppercase…, 0x8011C64C) son sprites de 8×12 que leen
    # las filas 1–12 de la celda de 16 de 8FONT_R; las colas de g j p q y (filas 13–14, font/en_8px.txt) quedaban
    # afuera. Alto 12 → 14. En el editor, el camino de medio ancho escribía w = 8 y h = t0 (12, compartido con el de
    # ancho completo): se escriben juntos con un sw (prim + 0x10, alineado).
    ('ENTR', 0x8011CBA8, words(li(V0, 8), 0xA6020006, 0xA6080008),
     words(0x3C02000E, 0x34420008, 0xAE020006), 'letras del editor (medio ancho): 8×12 → 8×14'),
    ('ENTR', 0x8011C6D4, words(li(V0, 12)), words(li(V0, 14)), 'columna de opciones del editor: alto 12 → 14'),
    ('ENTR', 0x8011B7E8, words(li(T0, 12)), words(li(T0, 14)), 'letras del teclado: alto 12 → 14'),
    # #276: el "=" entre los campos del editor es un sprite (plantilla de 0x8011CE30) con la celda del glifo 0x3D de
    # 8FONT_R (u 0xE8, v 0x11). Se apunta a la del 0x20 (u 0x80, v 0x01, en blanco): queda un espacio, como en la ficha.
    ('ENTR', 0x8011CE98, words(li(V0, 0xE8)), words(li(V0, 0x80)), '"=" del editor → espacio (u)'),
    ('ENTR', 0x8011CEA0, words(li(V0, 0x11)), words(li(V0, 0x01)), '"=" del editor → espacio (v)'),
]
# formato del nombre completo en los menús (se busca: la dirección cambia por overlay)
FORMAT_OLD = b'%s%s\x00\x00\x00\x00%s=%s\x00'
FORMAT_NEW = b'%s' + EN_SPACE + b'%s\x00\x00\x00%s' + EN_SPACE + b'%s\x00'
FORMAT_OVLS = ('ENTR', 'IMIS', 'PRM', 'TITL')
# ENTR tiene un segundo par, al revés ("%s=%s" y después "%s%s"; ficha del protagonista y listas, #276)
FORMAT2_OLD = b'\x00%s=%s\x00\x00\x00%s%s\x00'
FORMAT2_NEW = b'\x00%s' + EN_SPACE + b'%s\x00\x00\x00%s%s\x00'
OVLS = ('ENTR', 'SNMP', 'IMIS', 'PRM', 'TITL', 'SNDM', 'SNDU')

# Pantallas "Edit Main Character", calendario y "Enter Name" (#276). Las dibuja TITL (partida nueva) y una copia en
# SNDM con la misma tabla de layouts que SNMP (layout_patch.py): registros u8 posiciones · u8 textos fijos · 2 B ·
# puntero a posiciones (int16 x, y) · puntero a textos. El japonés trae la x precalculada para su ancho.
LAYOUT_BASE = {'TITL': 0x800FF190, 'SNDM': 0x800D61D8}
PROFILE = {'TITL': (0x8010DE78, 0x8010E0B4), 'SNDM': (0x800EFEA8, 0x800F0014)}   # (posiciones, textos)
CALENDAR = {'TITL': 0x8010DF04, 'SNDM': 0x800EFF38}
OPTIONS_LAYOUT = (0x800F2558, 0x800F26F4)     # SNDM: (posiciones, textos) del menú Options; 6 textos (título + 5 opciones)
OPTIONS_CX = 56                              # centro de la columna (el japonés: 56–58)
P_BIRTHDAY, P_BLOOD, P_FACE, P_TITLE, P_VALUES = 3, 4, 8, 9, range(10, 17)
C_OCT_DEC, C_CONFIRM = (9, 10, 11), 43                                         # C_CONFIRM solo en TITL
VALUE_X = 144       # columna de valores (japonés 140): "Nickname" (37 px desde x = 102) la tocaba
CONFIRM_X = 221     # "Confirm" (31 px) centrado en el recuadro del cursor (japonés 224, para 決定 de 24 px)
# Barra de botones del editor (ENTR, code@0xc35c, 36 B con el NUL): los íconos (○ □ △ ×) van en x fijas cada 56 px; el
# japonés deja un "　" (12 px) entre ícono y palabra. Con VWF, "　" = 12 px pero el espacio inglés 0xA0 = 3: las
# palabras se corrían a la izquierda bajo el ícono. Relleno con 0x20 (8 px) → palabras en x 3 / 58 / 116 / 172.
BUTTONS_ADDR = 0x80114D24
BUTTONS = EN_SPACE + b'Enter' + b' ' * 4 + b'Delete' + b' ' * 4 + b'Space' + b' ' * 4 + b'Back'
BUTTONS_ROOM = 36                    # 35 B del japonés + NUL


def table_off(i, o=0):
    return TABLE - BASE['ENTR'] + i * RSIZE + o


def read_table(data: bytes) -> list:
    rows = []
    for i in range(COUNT):
        rows.append({k: decode(data[table_off(i, o):][:0x15].split(b'\0')[0]) for k, o in FIELDS}
                    | {'extra': data[table_off(i, 0x3F):table_off(i, RSIZE)].hex()})
    return rows


def patch_code(ovl: str, data: bytearray, log: list):
    for o, addr, old, new, what in CODE:
        if o != ovl:
            continue
        p = addr - BASE[ovl]
        cur = bytes(data[p:p + len(old)])
        if cur not in (old, new):
            raise SystemExit(f'ERROR {ovl} {addr:#x}: se esperaba {old.hex()}, hay {cur.hex()} (¿overlay distinto?)')
        data[p:p + len(new)] = new
        log.append(f'{ovl} {addr:#x}: {what}')


def patch_format(ovl: str, data: bytearray, log: list):
    n_old, n_new = data.count(FORMAT_OLD), data.count(FORMAT_NEW)
    if (n_old, n_new) not in ((1, 0), (0, 1)):
        raise SystemExit(f'ERROR {ovl}: "%s%s"/"%s=%s" aparece {n_old} veces (y {n_new} ya cambiado); se esperaba 1')
    if n_old:
        p = data.find(FORMAT_OLD)
        data[p:p + len(FORMAT_OLD)] = FORMAT_NEW
    log.append(f'{ovl}: formato del nombre completo "%s%s" / "%s=%s" → "%s %s"')


def patch_format2(data: bytearray, log: list):
    n_old, n_new = data.count(FORMAT2_OLD), data.count(FORMAT2_NEW)
    if (n_old, n_new) not in ((1, 0), (0, 1)):
        raise SystemExit(f'ERROR ENTR: "%s=%s"/"%s%s" (2.º par) aparece {n_old} veces (y {n_new} ya cambiado)')
    if n_old:
        p = data.find(FORMAT2_OLD)
        data[p:p + len(FORMAT2_OLD)] = FORMAT2_NEW
    log.append('ENTR: 2.º formato del nombre completo "%s=%s" → "%s %s" (ficha del protagonista)')


def patch_buttons(data: bytearray, log: list):
    p = BUTTONS_ADDR - BASE['ENTR']
    cur = bytes(data[p:p + BUTTONS_ROOM])
    if cur[-1] != 0 or not (cur.startswith(b'\x81\x40\x93\xfc') or b'Enter' in cur[:8]):
        raise SystemExit(f'ERROR ENTR {BUTTONS_ADDR:#x}: no es la barra de botones ({cur.hex()})')
    assert len(BUTTONS) < BUTTONS_ROOM
    data[p:p + BUTTONS_ROOM] = BUTTONS.ljust(BUTTONS_ROOM, b'\0')
    log.append(f'ENTR {BUTTONS_ADDR:#x}: barra de botones con relleno de 8 px (Enter/Delete/Space/Back tras su ícono)')


def patch_layout(ovl: str, data: bytearray, log: list):
    """#276: x de la ficha del protagonista, del calendario y de los rótulos según el ancho real del inglés."""
    from layout_patch import px, px_jp, cstr, u32
    base = LAYOUT_BASE[ovl]
    jp = open(os.path.join(ISO_OVL, f'{ovl}_GRP.BIN'), 'rb').read()

    def setx(pos_tbl, idx, new, what):
        o = pos_tbl - base + 4 * idx
        old_jp, cur = struct.unpack_from('<h', jp, o)[0], struct.unpack_from('<h', data, o)[0]
        if cur not in (old_jp, new):
            raise SystemExit(f'ERROR {ovl} posición {pos_tbl:#x}[{idx}]: x = {cur}, se esperaba {old_jp} (¿overlay distinto?)')
        struct.pack_into('<h', data, o, new)
        log.append(f'{ovl} {pos_tbl:#x}[{idx}] x {old_jp} → {new}: {what}')

    def centered(pos_tbl, txt_tbl, idx, what):
        o = pos_tbl - base + 4 * idx
        x = struct.unpack_from('<h', jp, o)[0]
        t_jp = cstr(jp, base, u32(jp, txt_tbl - base + 4 * idx))
        t_en = cstr(data, base, u32(data, txt_tbl - base + 4 * idx))
        if t_en == t_jp:
            raise SystemExit(f'ERROR {ovl}: «{what}» sigue en japonés (¿corrió la etapa menus?)')
        setx(pos_tbl, idx, x + (px_jp(t_jp) - px(t_en)) // 2, f'{what} centrado ({px(t_en)} px; jp {px_jp(t_jp)})')

    pos, txt = PROFILE[ovl]
    setx(pos, P_BIRTHDAY, 102, 'Birthday alineado con los otros rótulos')
    setx(pos, P_BLOOD, 102, 'Blood alineado con los otros rótulos')
    centered(pos, txt, P_FACE, 'rótulo bajo la cara')
    centered(pos, txt, P_TITLE, 'título de la ficha')
    for i in P_VALUES:
        setx(pos, i, VALUE_X, 'columna de valores')
    for i in C_OCT_DEC:
        setx(CALENDAR[ovl], i, 52, 'Oct/Nov/Dec en la columna de Jul/Aug/Sep')
    if ovl == 'TITL':
        setx(CALENDAR[ovl], C_CONFIRM, CONFIRM_X, '"Confirm" del calendario dentro de su recuadro')
    if ovl == 'SNDM':
        # Menú Options del título (#284): layout de 6 textos (título + 5 opciones) con la x del japonés (centro 56–58 px,
        # distinto por opción); en inglés cada opción quedaba corrida. Todas centradas en la columna (centro 56).
        pos_o, txt_o = OPTIONS_LAYOUT
        for i in range(6):
            t_en = cstr(data, base, u32(data, txt_o - base + 4 * i))
            setx(pos_o, i, OPTIONS_CX - px(t_en) // 2, f'Options: «{t_en.decode("ascii", "replace")}» centrado ({px(t_en)} px)')


def patch_defaults(data: bytearray, log: list, csv_path=CSV):
    cur = read_table(data)
    with open(csv_path, encoding='utf-8') as f:
        rows = list(csv.DictReader(f))
    for row in rows:
        i = int(row['idx'])
        for k, o in FIELDS:
            # la etapa "menus" ya pone en inglés parte de la tabla (menus_en.jsonl): se acepta texto ASCII
            if cur[i][k] != row[f'{k}_jp'] and not cur[i][k].isascii():
                raise SystemExit(f'ERROR registro {i} {k}: el japonés no coincide ({cur[i][k]} ≠ {row[k + "_jp"]})')
            en = row[f'{k}_en']
            b = en.encode('ascii').replace(b' ', EN_SPACE)
            if len(b) > FIELD_MAX:
                raise SystemExit(f'ERROR registro {i} {k}: "{en}" = {len(b)} B > {FIELD_MAX}')
            if len(en) > EDIT_MAX:
                log.append(f'AVISO registro {i} {k}: "{en}" ({len(en)}) supera el tope del editor ({EDIT_MAX}): '
                           f'se ve entero, pero queda "{en[:EDIT_MAX]}" si el jugador lo edita')
            data[table_off(i, o):table_off(i, o + 0x15)] = b.ljust(0x15, b'\0')
    log.append(f'ENTR: {len(rows)} nombres por defecto en inglés ({os.path.relpath(csv_path, WORK)})')


def build(src_dir, dst_dir, csv_path=CSV) -> list:
    log = []
    os.makedirs(dst_dir, exist_ok=True)
    for ovl in OVLS:
        name = f'{ovl}_GRP.BIN'
        src = os.path.join(src_dir, name) if src_dir not in (None, '-') else None
        if not src or not os.path.exists(src):
            src = os.path.join(ISO_OVL, name)
        data = bytearray(open(src, 'rb').read())
        size = len(data)
        patch_code(ovl, data, log)
        if ovl in FORMAT_OVLS:
            patch_format(ovl, data, log)
        if ovl == 'ENTR':
            patch_format2(data, log)
            patch_buttons(data, log)
            patch_defaults(data, log, csv_path)
        if ovl in LAYOUT_BASE:
            patch_layout(ovl, data, log)
        assert len(data) == size
        with open(os.path.join(dst_dir, name), 'wb') as f:
            f.write(data)
    return log


def main(argv):
    if len(argv) == 2 and argv[1] == 'dump':
        for i, r in enumerate(read_table(open(os.path.join(ISO_OVL, 'ENTR_GRP.BIN'), 'rb').read())):
            print(i, r)
    elif len(argv) == 4 and argv[1] == 'build':
        for ln in build(argv[2], argv[3]):
            print(ln)
    else:
        print(__doc__)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
