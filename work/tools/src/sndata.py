"""SNMAP/SNDATA.BIN (bytecode de eventos de mapa): parser y mapa mensaje de SNMSG → bloque → escenario.

Formato (2.305.888 bytes; verificado 2026-09-28 por análisis estático, todos los bytes contabilizados):
  0x000  141 × u32: offset de cada bloque (0x800 + k·0x4048); el último = tamaño del archivo. Relleno 00 hasta 0x800.
  bloque (0x4048 bytes, uno por mapa/escenario):
    0x00  18 × i32: [0] = 16 (casilleros de evento), [1] = 4 (¿?), [2..12] = offset (en u16) de los eventos 0..10,
          [13..17] = -1. Los 11 eventos existen en los 140 bloques y cada uno empieza con `00 02 <n>` (etiqueta n).
    0x48  código: instrucciones alineadas a u16 = u8 opcode · u8 largo (en u16, incluida la cabecera) · args u16.
          El largo de cada opcode es fijo (salvo 0xB9: 9/13/21/25). 0xFF = fin; relleno FF hasta el final del bloque.
          Después del evento 10 vienen subrutinas terminadas en 0x0A (acá: "S1", "S2", …).
  Opcodes con mensaje de SNMSG (índice global de slot; cobertura 32.288/32.288, cada slot una sola vez):
    17 <piloto> <ventana<<8> <msg>             línea normal
    18 <piloto> <ventana<<8> <msg>             8 variantes msg..msg+7 (piloto 2000 = $n protagonista, 2001 = $N pareja)
    1B <piloto> <ventana<<8> <msg>             ídem 18 (solo en los bloques finales 125/129)
    19 <cond> <piloto> <ventana<<8> <msg>      línea condicionada (¿según piloto/unidad presente?; cond sin decodificar)
    1C <piloto> <ventana<<8> <msg> <x>         línea (4 casos)
    1D <piloto> <ventana<<8> <msg>             línea (2 casos)
    1E 0 <msg victoria> 0 <msg derrota>        condiciones de victoria/derrota (una por fase del mapa)
    1F <piloto> 0 <msg>                        elección de 2 opciones (「…選択」)
  <piloto> = ID de UNITPRAM/PILOT.BIN (retrato); 2000/2001 = protagonista/pareja.
  Otros opcodes: 08 <off> = salto a otro offset del bloque (902/902 caen en inicio de instrucción);
  04/06 (4.878 c/u) parecen abrir/cerrar un bloque condicional; 09 <n> NO es un mensaje (probable flag/variable).
  Slots 32.288..32.543 de SNMSG = "Dummy String" (sin referencia).

El mapa bloque → escenario (tabla ESCENARIOS abajo) cruza, por bloque, hablantes, condiciones de victoria/derrota y
elecciones con info/…Complete Chart, …Timetable (Akurasu Wiki), la guía de Cyath (GameFAQs) e info/s-rpg-navi.com,
y el orden de los bloques con la tabla oficial de títulos del juego (TITULOS, overlay IMIS).

Uso:
  sndata.py map      [SNDATA.BIN] [snmsg.jsonl] [dir_salida]  → dump/sndata_map.csv y dump/sndata_bloques.csv
  sndata.py disasm   <bloque> [SNDATA.BIN] [snmsg.jsonl]       → listado del bytecode con vista previa de mensajes
  sndata.py selftest [SNDATA.BIN] [snmsg.jsonl]                → verifica estructura, largos y cobertura
Por defecto SNDATA.BIN = work/iso_jp/SNMAP/SNDATA.BIN y snmsg.jsonl = work/dump/snmsg.jsonl.
"""
import collections
import csv
import json
import os
import struct
import sys
import unicodedata

WORK = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
DEF_BIN = os.path.join(WORK, 'iso_jp', 'SNMAP', 'SNDATA.BIN')
DEF_MSG = os.path.join(WORK, 'dump', 'snmsg.jsonl')
DEF_PILOT = os.path.join(WORK, 'dump', 'pilot.jsonl')
DUMP = os.path.join(WORK, 'dump')

FILE_SIZE = 2305888
N_BLOCKS = 140
BLOCK_SIZE = 0x4048
BLOCK_HDR = 0x48
N_EVENTS = 11
N_SLOTS = 32288          # slots referenciados; 32288..32543 = "Dummy String"
PC_FACE = {2000: '$n', 2001: '$N'}

# Largo (en u16) de cada opcode, medido sobre los 140 bloques (0xB9 es variable).
OPLEN = {
    0x00: 2, 0x01: 1, 0x02: 2, 0x03: 2, 0x04: 2, 0x05: 2, 0x06: 2, 0x08: 2, 0x09: 2, 0x0A: 1, 0x0B: 4, 0x0C: 2,
    0x0D: 2, 0x0E: 3, 0x0F: 3, 0x10: 3, 0x11: 3, 0x12: 4, 0x13: 4, 0x14: 1, 0x15: 1, 0x16: 1, 0x17: 4, 0x18: 4,
    0x19: 5, 0x1A: 9, 0x1B: 4, 0x1C: 5, 0x1D: 4, 0x1E: 5, 0x1F: 4, 0x21: 2, 0x22: 2, 0x23: 1, 0x24: 2, 0x25: 3,
    0x26: 4, 0x27: 2, 0x28: 1, 0x29: 2, 0x2A: 2, 0x2B: 2, 0x2C: 4, 0x2D: 5, 0x2F: 4, 0x30: 1, 0x31: 1, 0x32: 3,
    0x33: 2, 0x34: 2, 0x35: 2, 0x36: 3, 0x37: 3, 0x38: 2, 0x39: 2, 0x3A: 2, 0x3B: 3, 0x3C: 2, 0x3D: 5, 0x3E: 2,
    0x3F: 2, 0x40: 2, 0x41: 2, 0x42: 2, 0x43: 3, 0x44: 2, 0x45: 2, 0x46: 2, 0x47: 2, 0x48: 3, 0x49: 2, 0x4A: 2,
    0x4B: 2, 0x4E: 2, 0x4F: 1, 0x50: 1, 0x51: 4, 0x52: 5, 0x54: 4, 0x55: 5, 0x57: 3, 0x58: 4, 0x5A: 4, 0x5B: 4,
    0x5C: 3, 0x5D: 3, 0x5E: 3, 0x5F: 2, 0x60: 3, 0x61: 2, 0x62: 3, 0x63: 2, 0x64: 3, 0x65: 2, 0x66: 2, 0x67: 4,
    0x68: 5, 0x69: 5, 0x6A: 3, 0x6B: 4, 0x6C: 4, 0x6E: 2, 0x6F: 2, 0x70: 2, 0x71: 2, 0x72: 2, 0x73: 2, 0x74: 6,
    0x75: 3, 0x77: 3, 0x78: 2, 0x79: 4, 0x7A: 4, 0x7B: 4, 0x7C: 6, 0x7D: 6, 0x7E: 6, 0x80: 6, 0x81: 6, 0x82: 4,
    0x83: 4, 0x84: 3, 0x85: 3, 0x86: 3, 0x87: 1, 0x88: 3, 0x89: 3, 0x8B: 3, 0x8C: 4, 0x8D: 3, 0x8E: 2, 0x8F: 2,
    0x90: 4, 0x91: 4, 0x92: 6, 0x93: 6, 0x94: 6, 0x96: 11, 0x97: 11, 0x98: 11, 0x99: 1, 0x9A: 3, 0x9B: 3,
    0x9C: 3, 0x9D: 3, 0x9E: 3, 0x9F: 2, 0xA0: 2, 0xA1: 2, 0xA2: 2, 0xA3: 2, 0xA4: 2, 0xA5: 3, 0xA6: 2, 0xA7: 2,
    0xA8: 5, 0xA9: 3, 0xAA: 2, 0xAB: 3, 0xAC: 3, 0xAD: 3, 0xAE: 3, 0xAF: 3, 0xB0: 3, 0xB1: 2, 0xB2: 2, 0xB3: 2,
    0xB4: 2, 0xB5: 2, 0xB6: 3, 0xB7: 2, 0xB8: 2, 0xB9: None, 0xBA: 4, 0xBB: 5,
}

# Títulos oficiales de los escenarios: tabla de punteros del overlay OVL/IMIS_GRP.BIN (ptr@0x1FB74, índice 1..129;
# idéntica en TITL_GRP ptr@0x13BCC). Ver dump/ovl_strings.jsonl. El índice 0 (prólogo) no tiene título en la tabla.
TITULOS = [None,
    '鋼鉄のコクピット',  # 1
    'マジンガーＺ絶体絶命',  # 2
    'ゲッターチーム出撃せよ！',  # 3
    'ジオン再臨',  # 4
    'シークレット・ナンバーズ',  # 5
    'アーガマ撃墜命令',  # 6
    'バニシング・トルーパー',  # 7
    '黒いガンダム',  # 8
    'ホワイトベース救出',  # 9
    '死神と呼ばれたＧ',  # 10
    'ジオンの亡霊',  # 11
    '対決、極東基地',  # 12
    'レッツ!コンバイン',  # 13
    '出撃！その名はジャイアント・ロボ',  # 14
    '風を呼ぶ者',  # 15
    '未知なる災い',  # 16
    'アムロ再び',  # 17
    '白いモビルスーツ',  # 18
    '戦いは誰のために',  # 19
    '翼を持ったガンダム',  # 20
    '目覚めよ、勇者',  # 21
    'ガンダム強奪',  # 22
    '野望の男',  # 23
    '少女が見た流星',  # 24
    '父との約束',  # 25
    '使徒、襲来',  # 26
    '咆哮、ＥＶＡ初号機',  # 27
    'ＧＲ対ＧＲ２',  # 28
    'ゼータの鼓動',  # 29
    '第二次直上会戦',  # 30
    '紅い稲妻 空飛ぶマジンガー',  # 31
    '激突！ゲッターロボＶＳゲッターロボＧ',  # 32
    '決戦、第２新東京市',  # 33
    '聖戦士たち',  # 34
    'エレの霊力',  # 35
    'ナの国の女王',  # 36
    'オーラロード',  # 37
    '東京上空',  # 38
    '獣を超え、人を超え、いでよ神の戦士',  # 39
    '戦いの海へ',  # 40
    'マジンガーＺ対暗黒大将軍',  # 41
    'ボルテス起死回生',  # 42
    'シャーキン悪魔の戦い',  # 43
    'ホンコン・シティ',  # 44
    'ガンダム、星の海へ',  # 45
    '始動ダブルゼータ',  # 46
    'ソロモンの悪夢',  # 47
    'クロスボーン・バンガード',  # 48
    '紅いエヴァンゲリオン',  # 49
    '海からのマレビト',  # 50
    'マシン展開',  # 51
    '瞬間、心かさねて',  # 52
    'ブービー・トラップ',  # 53
    'カウント・ダウン',  # 54
    'トランス・フォーメーション',  # 55
    '隠された殺意',  # 56
    'サタン・ファイト',  # 57
    'リン・ミンメイ',  # 58
    'ジュピトリアン',  # 59
    '帝国の女王',  # 60
    '終末への前奏曲',  # 61
    '奇跡の価値は',  # 62
    'スペース・フォールド',  # 63
    'アームド・アタック',  # 64
    '天敵との遭遇',  # 65
    'イングラムの真意',  # 66
    'ミス・マクロス',  # 67
    '木星からの逃亡者',  # 68
    '人類を導く者',  # 69
    'ファースト・コンタクト',  # 70
    'ビッグ・エスケープ',  # 71
    'バイバイ・マルス',  # 72
    'アクシズからの使者',  # 73
    'プルとアクシズと',  # 74
    'リィナの血',  # 75
    '漆黒の天使来たりて',  # 76
    'ジュピター・ゴースト',  # 77
    '宇宙に咲く妖花',  # 78
    'ゼロと呼ばれたガンダム',  # 79
    '強襲、阻止限界点',  # 80
    '父よ地球は近い',  # 81
    '静止した闇の中で',  # 82
    '赤い髪の女',  # 83
    '神か、悪魔か…',  # 84
    '第三の力',  # 85
    '龍と虎',  # 86
    '男の戰い',  # 87
    'ヴァリアブル・フォーメーション',  # 88
    'ガラスの王国',  # 89
    'ダカールの日',  # 90
    '王国崩壊',  # 91
    'バイブレーション',  # 92
    '思い出を未来へ',  # 93
    'ソロモン攻略戦',  # 94
    '女たちの戦場',  # 95
    '駆け抜ける嵐',  # 96
    'あしゅら男爵、散る',  # 97
    '魔神皇帝',  # 98
    'クロス・ファイト',  # 99
    '異邦人たちの帰還',  # 100
    '地球を賭けた一騎討ち',  # 101
    'ジオンの幻像',  # 102
    '父の胸の中で泣け！',  # 103
    '女王リリーナ',  # 104
    '天使の輪の上で',  # 105
    '神の国への誘惑',  # 106
    'クロス・ターゲット',  # 107
    '戦士、再び…',  # 108
    '勝者と敗者に祝福を',  # 109
    'せめて、人間らしく',  # 110
    '最後のシ者',  # 111
    '運命の矢',  # 112
    '愛・おぼえていますか',  # 113
    'Ａｉｒ',  # 114
    'ギア・オブ・デスティニー',  # 115
    '絶望の宴は今から始まる',  # 116
    'この星の明日のために',  # 117
    '終わりの始まり',  # 118
    '人類に逃げ場なし',  # 119
    '鋼の魂',  # 120
    '欠番',  # 121
    '全能なる調停者',  # 122
    'シト新生',  # 123
    'ＥＯＴの島',  # 124
    '心に念じる見えない刃',  # 125
    '黒い超闘士',  # 126
    '誰がために鐘は踊る',  # 127
    '進路に光明、退路に絶望',  # 128
    '精霊憑依',  # 129
]

# Bloque → (escenario, ruta, id de título en TITULOS, título EN (wiki), confianza, nota).
# El orden de los bloques sigue el de TITULOS; los escenarios con más de un mapa (evento previo o partes) ocupan
# bloques consecutivos. Rutas: columnas de info/…Timetable y del diagrama de JL Lee en la guía de Cyath.
# Fuentes: info/…Complete Chart, …Timetable (Akurasu), guía de Cyath (GameFAQs) e info/s-rpg-navi.com (walkthrough JP
# por escenario: ruta, condiciones por parte, unidades que llegan, siguiente escenario).
# Confianza: alta = contenido (condiciones, elecciones, elenco, texto) y orden de TITULOS coinciden;
# baja = bloque vacío ubicado solo por orden.
ESCENARIOS = {
    0: ('0', '', 0, 'Prologue', 'alta', ''),
    1: ('1', 'super', 1, 'Cockpit of Steel', 'alta', ''),
    2: ('2', 'super', 2, 'Desperate Situation For Mazinger Z', 'alta', ''),
    3: ('3', 'super', 3, 'Getter Team, Launch!', 'alta', ''),
    4: ('4', 'super', 4, "Zeon's Second Coming", 'alta', ''),
    5: ('5', 'super', 5, 'Secret Numbers', 'alta', ''),
    6: ('6', 'super', 6, 'The Order To Shoot Down The Argama', 'alta', ''),
    7: ('1', 'real', 7, 'Vanishing Trooper', 'alta', ''),
    8: ('2', 'real', 8, 'Black Gundam', 'alta', ''),
    9: ('3', 'real', 9, 'Rescue The White Base', 'alta', ''),
    10: ('4', 'real', 10, 'The Gundam Called the God of Death', 'alta', ''),
    11: ('5', 'real', 11, 'The Ghosts Of Zeon', 'alta', ''),
    12: ('6', 'real', 12, 'Showdown At The Far East Base', 'alta', ''),
    13: ('7', '', 13, "Let's Combine!", 'alta', ''),
    14: ('8', '', 14, 'Launch! Its Name Is Giant Robo', 'alta', ''),
    15: ('9', 'super', 15, 'He Who Summons The Winds', 'alta', 's-rpg-navi: en la super solo llega R-GUN (Ingram) en el 2PP; sin líneas de Ryusei'),
    16: ('9', 'real', 16, 'The Unknown Calamity', 'alta', 's-rpg-navi: en la real llegan R-GUN, R-1 y R-2 en el 2PP; Ryusei y Rai hablan'),
    17: ('10', 'Jaburo', 17, 'Amuro Again', 'alta', ''),
    18: ('11', 'Jaburo', 18, 'The White Mobile Suit', 'alta', ''),
    19: ('12', 'Jaburo', 19, 'For Whom We Fight', 'alta', ''),
    20: ('13', 'Jaburo', 20, 'The Gundam That Had Wings', 'alta', ''),
    21: ('10', 'Atalia Sur', 21, 'Awaken, Brave One', 'alta', ''),
    22: ('11', 'Atalia Sur', 22, 'Gundamjack', 'alta', ''),
    23: ('12', 'Atalia Sur', 23, 'A Man Of Ambitions', 'alta', ''),
    24: ('13', 'Atalia Sur', 24, 'The Shooting Star She Saw', 'alta', ''),
    25: ('14', '', 25, 'A Promise With Father', 'alta', ''),
    26: ('15', '', 26, 'Angel Attack', 'alta', ''),
    27: ('16', '', 27, 'Roar, EVA Unit-01', 'alta', ''),
    28: ('17', '', 28, 'GR vs. GR2', 'alta', ''),
    29: ('18', 'real', 29, 'The Sign Of Zeta', 'alta', ''),
    30: ('19', 'real', 30, 'His Second Engagement', 'alta', ''),
    31: ('18', 'super', 31, 'With A Red Flash, Fly To The Sky, Mazinger', 'alta', 'título oficial 紅い稲妻 (la wiki dice 紅の稲妻)'),
    32: ('19', 'super', 32, 'Clash! Getter Robo vs. Getter Robo G', 'alta', ''),
    33: ('20', '', 33, 'A Decisive Battle In New Tokyo 2', 'alta', 'evento previo: Ramiel derriba a la EVA-01 al salir (Cyath); el disparo del 4PP es dentro del bloque 34'),
    34: ('20', '', 33, 'A Decisive Battle In New Tokyo 2', 'alta', ''),
    35: ('21', 'EVA-02 (Aura)', 34, 'Aura Battlers', 'alta', 'evento previo: Drake y Shot observan a la Argama y deciden contactarla (Cyath)'),
    36: ('21', 'EVA-02 (Aura)', 34, 'Aura Battlers', 'alta', ''),
    37: ('22', 'EVA-02 (Aura)', 35, "Elle's Aura", 'alta', ''),
    38: ('23', 'EVA-02 (Aura)', 36, "The Land Of Na's Queen", 'alta', ''),
    39: ('24', 'EVA-02 (Aura)', 37, 'The Aura Road', 'alta', ''),
    40: ('25', 'EVA-02 (Aura)', 38, 'The Skies Of Tokyo', 'alta', ''),
    41: ('21', 'Lejano Oriente', 39, "Beyond Beast, Beyond Man, Become God's Warrior", 'alta', ''),
    42: ('22', 'Lejano Oriente', 40, 'Into The Sea Of Battle', 'alta', ''),
    43: ('23', 'Lejano Oriente', 41, 'Mazinger Z vs. The Great General of Darkness', 'alta', 'parte 1: Koji contra Dante, que se retira (Cyath: "Dante in first part")'),
    44: ('23', 'Lejano Oriente', 41, 'Mazinger Z vs. The Great General of Darkness', 'alta', 'parte 2: Gorgon, Dark General y Tetsuya'),
    45: ('24', 'Lejano Oriente', 42, 'Voltes, Back From The Ashes', 'alta', ''),
    46: ('25', 'Lejano Oriente', 43, "The Devil Sharkin's Battle", 'alta', ''),
    47: ('21', 'Liga Militar', 44, 'Hong Kong City', 'alta', ''),
    48: ('22', 'Liga Militar', 45, 'Gundam, Go To The Sea Of Stars', 'alta', ''),
    49: ('23', 'Liga Militar', 46, 'Startup, Double Zeta', 'alta', ''),
    50: ('24', 'Liga Militar', 47, 'The Nightmare Of Solomon', 'alta', ''),
    51: ('25', 'Liga Militar', 48, 'Crossbone Vanguard', 'alta', ''),
    52: ('26', 'EVA-02 / Lejano Oriente', 49, 'The Red Evangelion', 'alta', 's-rpg-navi: derrota "アスカの撃墜・母艦の撃墜"; se llega desde 東京上空 y シャーキン悪魔の戦い'),
    53: ('26', 'Liga Militar', 50, 'Terror From The Sea', 'alta', 's-rpg-navi: derrota "母艦の撃墜"; se llega desde クロスボーン・バンガード'),
    54: ('27', '', 51, 'Machine Development', 'alta', ''),
    55: ('30', '2 EVAs', 52, 'Moment And Heart Together', 'alta', ''),
    56: ('31', 'derribo (Shoot Down)', 53, 'Booby Trap', 'alta', 'empieza con el plan de derribar el proyectil de la mass driver'),
    57: ('32', 'derribo (Shoot Down)', 54, 'Count Down', 'alta', ''),
    58: ('33', 'derribo (Shoot Down)', 55, 'Trans-Formation', 'alta', ''),
    59: ('34', 'derribo (Shoot Down)', 56, 'Hidden Bloodlust', 'alta', ''),
    60: ('35', 'derribo (Shoot Down)', 57, 'Saturn Fight', 'alta', ''),
    61: ('36', 'derribo (Shoot Down)', 58, 'Lynn Minmay', 'alta', ''),
    62: ('37', 'derribo (Shoot Down)', 59, 'The Jupitorians', 'alta', ''),
    63: ('38', 'derribo (Shoot Down)', 60, 'The Queen Of The Empire', 'alta', ''),
    64: ('39', 'derribo (Shoot Down)', 61, 'Prelude To The End', 'alta', ''),
    65: ('31', 'atrapar con EVA', 62, 'The Value Of A Miracle', 'alta', 'empieza con "ＥＶＡ各機、配置に付きました" (las EVA atajan el proyectil)'),
    66: ('32', 'atrapar con EVA', 63, 'Space Fold', 'alta', ''),
    67: ('33', 'atrapar con EVA', 64, 'ARMD Attack', 'alta', ''),
    68: ('34', 'atrapar con EVA', 65, 'An Encounter With Our Natural Enemies', 'alta', ''),
    69: ('35', 'atrapar con EVA', 66, "Ingram's True Intentions", 'alta', 'título oficial イングラムの真意 (la Complete Chart dice 殺意)'),
    70: ('36', 'atrapar con EVA', 67, 'Miss Macross', 'alta', ''),
    71: ('37', 'atrapar con EVA', 68, 'Fugitive From Jupiter', 'alta', ''),
    72: ('38', 'atrapar con EVA', 69, 'The One Who Will Guide Humanity', 'alta', ''),
    73: ('39', 'atrapar con EVA', 70, 'First Contact', 'alta', ''),
    74: ('40', '', 71, 'The Big Escape', 'alta', ''),
    75: ('41', '', 72, 'Bye Bye Mars', 'alta', ''),
    76: ('42', 'Reinforce Jr.', 73, 'A Messenger From Axis', 'alta', ''),
    77: ('43', 'Reinforce Jr.', 74, 'Ple, Axis and...', 'alta', ''),
    78: ('44', 'Reinforce Jr.', 75, "Leina's Blood", 'alta', ''),
    79: ('45', 'Reinforce Jr.', 76, 'The Coming Of The Black Angel', 'alta', ''),
    80: ('42', 'Gran Garan', 77, 'The Jupiter Ghost', 'alta', ''),
    81: ('43', 'Gran Garan', 78, 'The Terrible Flower Blooming In Space', 'alta', ''),
    82: ('44', 'Gran Garan', 79, 'The Gundam Called Zero', 'alta', ''),
    83: ('45', 'Gran Garan', 80, 'Assault On The Point Of No Return', 'alta', ''),
    84: ('42', 'Goraon', 81, 'Father, The Earth Is Near', 'alta', ''),
    85: ('43', 'Goraon', 82, 'Within The Paralyzing Darkness', 'alta', ''),
    86: ('44', 'Goraon', 83, 'The Red Haired Woman', 'alta', ''),
    87: ('45', 'Goraon', 84, 'A God, Or A Devil', 'alta', ''),
    88: ('46', 'real', 85, "The Third's Power", 'alta', ''),
    89: ('46', 'super', 86, 'The Dragon And The Tiger', 'alta', ''),
    90: ('47', '', 87, "A Man's Fight", 'alta', ''),
    91: ('50', '', 88, 'Variable Formation', 'alta', ''),
    92: ('51', 'Gran Garan', 89, 'The Glass Kingdom', 'alta', ''),
    93: ('51', 'Ra Cailum', 90, 'Day Of Dakar', 'alta', ''),
    94: ('52', 'Gran Garan', 91, "Kingdom's Fall", 'alta', ''),
    95: ('52', 'Ra Cailum', 92, 'Vibration', 'alta', ''),
    96: ('54', 'Goraon', 93, 'Memories Taken To The Future', 'alta', ''),
    97: ('53', 'Ra Cailum', 94, 'The Capture Of Solomon', 'alta', ''),
    98: ('54', 'Ra Cailum', 95, "The Womens' Battlefield", 'alta', ''),
    99: ('55', 'Ra Cailum', 96, 'A Storm Raging Through', 'alta', ''),
    100: ('51', 'Goraon', 97, 'The Fall Of Baron Ashura', 'alta', ''),
    101: ('52', 'Goraon', 98, 'The Demon Emperor', 'alta', ''),
    102: ('53', 'Gran Garan', 99, 'Cross Fight', 'alta', ''),
    103: ('54', 'Gran Garan', 100, "Foreigners' Return", 'alta', ''),
    104: ('53', 'Goraon', 101, 'Duel For The Earth', 'alta', ''),
    105: ('56', '', 102, 'The Ghost Of Zeon', 'alta', ''),
    106: ('55', 'Goraon', 103, "The Cry Within Father's Breast!", 'alta', ''),
    107: ('55', 'Gran Garan', 104, 'Queen Relena', 'alta', ''),
    108: ('57', '', 105, "Above The Angel's Halo", 'alta', 'evento previo: prueba de la Angel Halo contra Side 3 (Kagachi, Maria)'),
    109: ('57', '', 105, "Above The Angel's Halo", 'alta', ''),
    110: ('58', 'Axis', 106, 'The Temptation Of The Land Of God', 'alta', 'Shapiro; derrota "cualquier aliado" = 58 Axis (el 58 Angel Halo es "nave nodriza")'),
    111: ('59', 'Axis', 107, 'Cross Target', 'alta', ''),
    112: ('60', 'Axis', 108, 'Warrior, Once More...', 'alta', 'Haman; derrota "Judau" (Complete Chart)'),
    113: ('58', 'Angel Halo', 109, 'Blessings Upon The Winner And Loser', 'alta', ''),
    114: ('59', 'Angel Halo', 110, 'At Least, To Be Human', 'alta', ''),
    115: ('60', 'Angel Halo', 111, 'The Final Messenger', 'alta', ''),
    116: ('61', '', 112, 'The Arrow Of Destiny', 'alta', ''),
    117: ('62', '', 113, 'Do You Remember Love?', 'alta', 'parte 1 (línea de defensa 10 turnos)'),
    118: ('62', '', 113, 'Do You Remember Love?', 'alta', 'parte 2 (nave de Boddole)'),
    119: ('64', '', 114, 'Air', 'alta', 'parte 1 (Asuka sola contra los Titans)'),
    120: ('64', '', 114, 'Air', 'alta', 'parte 2 (EVA serie)'),
    121: ('65', '', 115, 'The Gear Of Destiny', 'alta', ''),
    122: ('66', 'final ≥45 puntos', 116, 'The Banquet Of Despair Begins Now', 'alta', '熟練度45以上 (s-rpg-navi); Haman, Gato y Heinel como NPC'),
    123: ('67', 'final ≥45 puntos', 117, "For This Planet's Tomorrow", 'alta', 'parte 1 de 3 (Complete Chart: enemigos / Exelion al punto)'),
    124: ('67', 'final ≥45 puntos', 117, "For This Planet's Tomorrow", 'alta', 'parte 2 de 3 (Exelion al punto / todos al borde)'),
    125: ('67', 'final ≥45 puntos', 117, "For This Planet's Tomorrow", 'alta', 'parte 3 de 3 (batalla final)'),
    126: ('63', '', 118, 'The Beginning Of The End', 'alta', 'sin mapa ni mensajes: el 63 es solo historia (confirmado jugando por el mantenedor); el bloque es un stub'),
    127: ('66', 'final <45 puntos', 119, 'No Escape For Humanity', 'alta', '熟練度44以下 (s-rpg-navi); sin Haman/Gato/Heinel; Cyath: Scirocco, 3 Dancouga, Raodekiya'),
    128: ('67', 'final <45 puntos', 120, 'Spirits Of Steel', 'alta', 'parte 1 de 2 (enemigos / Exelion al punto / todos al borde)'),
    129: ('67', 'final <45 puntos', 120, 'Spirits Of Steel', 'alta', 'parte 2 de 2 (batalla final)'),
    130: ('', '', 121, '', 'baja', 'sin mensajes; título 欠番 ("número vacante") por orden (4 bloques vacíos para 3 títulos)'),
    131: ('', '', 122, '', 'baja', 'sin mensajes; título 全能なる調停者: escenario no incluido en la wiki (¿cortado?)'),
    132: ('', '', 123, '', 'baja', 'sin mensajes; título シト新生: escenario no incluido en la wiki (¿cortado?)'),
    133: ('', '', None, '', 'baja', 'sin mensajes; bloque vacío sin título'),
    134: ('28', '', 124, 'The Island Of EOT', 'alta', ''),
    135: ('29', 'super', 125, 'Within The Soul Lies An Unseen Blade', 'alta', 's-rpg-navi: se agrega 計都瞬獄剣 al Grungust Type-2; Ryusei pregunta por el arma nueva del Grungust de $n'),
    136: ('29', 'real', 126, 'The Black Super Warrior', 'alta', 's-rpg-navi: se agrega Gインパクトキャノン al Hückebein Mk-II; Ryusei pregunta por el arma nueva del Hückebein de $n'),
    137: ('48', '', 127, 'For Whom The Bell Tolls', 'alta', ''),
    138: ('49', '', 128, 'The Path Of Hope, The Path Of Despair', 'alta', ''),
    139: ('30', 'a la fuerza', 129, 'Spirit Possession', 'alta', ''),
}


def titulo_jp(b):
    t = ESCENARIOS[b][2]
    return 'プロローグ' if t == 0 else TITULOS[t] if t else ''


def load_blocks(data: bytes):
    """Devuelve la lista de 140 bloques: (cabecera de 18 i32, [(offset_u16, opcode, args)], offset de 0xFF)."""
    assert len(data) == FILE_SIZE, f'tamaño inesperado: {len(data)}'
    offs = struct.unpack_from('<141I', data, 0)
    assert offs[-1] == len(data) and all(b - a == BLOCK_SIZE for a, b in zip(offs, offs[1:]))
    blocks = []
    for k in range(N_BLOCKS):
        blk = data[offs[k]:offs[k + 1]]
        hdr = struct.unpack_from('<18i', blk, 0)
        code = blk[BLOCK_HDR:]
        ins, i = [], 0
        while code[2 * i] != 0xFF:
            op, ln = code[2 * i], code[2 * i + 1]
            assert op in OPLEN and (OPLEN[op] is None or OPLEN[op] == ln), f'bloque {k} +{i:#x}: op {op:02X} largo {ln}'
            ins.append((i, op, struct.unpack_from(f'<{ln - 1}H', code, 2 * i + 2)))
            i += ln
        assert set(code[2 * i:]) == {0xFF}, f'bloque {k}: basura después del fin'
        blocks.append((hdr, ins, i))
    return blocks


def msg_refs(op, a):
    """Mensajes de SNMSG que usa una instrucción: [(slot, tipo, piloto, ventana, variante, extra)]."""
    if op == 0x17:
        return [(a[2], 'linea', a[0], a[1] >> 8, '', '')]
    if op in (0x18, 0x1B):
        kind = 'protagonista' if a[0] == 2000 else 'pareja' if a[0] == 2001 else 'variantes'
        return [(a[2] + v, kind, a[0], a[1] >> 8, v + 1, '') for v in range(8)]
    if op == 0x19:
        return [(a[3], 'linea_cond', a[1], a[2] >> 8, '', f'cond={a[0]:#x}')]
    if op in (0x1C, 0x1D):
        return [(a[2], 'linea', a[0], a[1] >> 8, '', f'x={a[3]:#x}' if op == 0x1C else '')]
    if op == 0x1E:
        return [(a[1], 'victoria', '', '', '', ''), (a[3], 'derrota', '', '', '', '')]
    if op == 0x1F:
        return [(a[2], 'eleccion', a[0], '', '', '')]
    return []


def contexts(hdr, ins):
    """Nombre del evento o subrutina que contiene cada instrucción: E0..E10, S1, S2…"""
    starts = {hdr[2 + e]: f'E{e}' for e in range(N_EVENTS)}
    last_ev = hdr[2 + N_EVENTS - 1]
    names, cur, sub, in_tail = [], 'E0', 0, False
    for i, op, _ in ins:
        if i in starts:
            cur = starts[i]
        elif in_tail and cur == '':
            sub += 1
            cur = f'S{sub}'
        names.append(cur)
        if i >= last_ev and op == 0x01 and not in_tail:
            in_tail, cur = True, ''
        elif in_tail and op == 0x0A:
            cur = ''
    return names


def load_msgs(path):
    with open(path, encoding='utf-8') as f:
        return [json.loads(line) for line in f if line.strip()]


def load_pilots(path=DEF_PILOT):
    if not os.path.exists(path):
        return {}
    with open(path, encoding='utf-8') as f:
        return {r['id']: unicodedata.normalize('NFKC', r['short']) for r in map(json.loads, f)}


def pilot_name(pid, pilots):
    if pid == '':
        return ''
    return PC_FACE.get(pid) or pilots.get(pid, f'#{pid}')


def build_map(data, msgs):
    """[(slot, bloque, contexto, orden, ref)] ordenado por slot."""
    out = []
    for b, (hdr, ins, _) in enumerate(load_blocks(data)):
        order = 0
        for ctx, (i, op, a) in zip(contexts(hdr, ins), ins):
            refs = msg_refs(op, a)
            if refs:
                order += 1
            for r in refs:
                out.append((r[0], b, ctx, order, op, r))
    out.sort()
    return out


def cmd_map(bin_path=DEF_BIN, msg_path=DEF_MSG, out_dir=DUMP):
    data = open(bin_path, 'rb').read()
    msgs = load_msgs(msg_path)
    pilots = load_pilots()
    rows = build_map(data, msgs)
    by_slot = {r[0]: r for r in rows}
    with open(os.path.join(out_dir, 'sndata_map.csv'), 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['slot', 'bloque', 'escenario', 'ruta', 'titulo_jp', 'evento', 'orden', 'op', 'tipo', 'variante',
                    'piloto_id', 'piloto', 'ventana', 'extra', 'speaker'])
        for s, m in enumerate(msgs):
            if s not in by_slot:
                w.writerow([s, '', '', '', '', '', '', '', 'sin_uso', '', '', '', '', '', m['speaker']])
                continue
            _, b, ctx, order, op, (_, kind, pid, win, var, extra) = by_slot[s]
            esc = ESCENARIOS[b]
            w.writerow([s, b, esc[0], esc[1], titulo_jp(b), ctx, order, f'{op:02X}', kind, var, pid, pilot_name(pid, pilots),
                        win, extra, m['speaker']])
    per_block = collections.defaultdict(list)
    for s, b, *_ in rows:
        per_block[b].append(s)
    with open(os.path.join(out_dir, 'sndata_bloques.csv'), 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['bloque', 'escenario', 'ruta', 'titulo_id', 'titulo_jp', 'titulo_en', 'confianza', 'nota', 'slot_desde',
                    'slot_hasta', 'mensajes', 'hablantes'])
        for b in range(N_BLOCKS):
            ss = per_block.get(b, [])
            sp = collections.Counter(msgs[s]['speaker'] for s in ss if msgs[s]['speaker'])
            esc = ESCENARIOS[b]
            w.writerow([b, esc[0], esc[1], esc[2], titulo_jp(b), *esc[3:], min(ss, default=''), max(ss, default=''), len(ss),
                        ' '.join(f'{k}({v})' for k, v in sp.most_common(6))])
    print(f'{len(rows)} referencias en {len(per_block)} bloques → {out_dir}/sndata_map.csv, sndata_bloques.csv')


def cmd_disasm(block, bin_path=DEF_BIN, msg_path=DEF_MSG):
    data = open(bin_path, 'rb').read()
    msgs = load_msgs(msg_path)
    pilots = load_pilots()
    hdr, ins, end = load_blocks(data)[block]
    esc = ESCENARIOS[block]
    print(f'# bloque {block}: escenario {esc[0]} {esc[1]} {titulo_jp(block)} ({esc[4]})  cabecera={hdr[:13]}  fin={end:#x}')
    prev = None
    for ctx, (i, op, a) in zip(contexts(hdr, ins), ins):
        if ctx != prev:
            print(f'--- {ctx}')
            prev = ctx
        line = f'{i:5x}  {op:02X} ' + ' '.join(f'{x:04x}' for x in a)
        for s, kind, pid, win, var, extra in msg_refs(op, a)[:1]:
            who = pilot_name(pid, pilots)
            txt = msgs[s]['jp'].replace('\n', '/')
            more = ' (+7 variantes)' if var else ''
            line += f'    ; [{kind} {who}] #{s}{more} {txt[:60]}'
        print(line)


def cmd_selftest(bin_path=DEF_BIN, msg_path=DEF_MSG):
    data = open(bin_path, 'rb').read()
    msgs = load_msgs(msg_path)
    blocks = load_blocks(data)
    # 1) cabecera de eventos
    for b, (hdr, ins, _) in enumerate(blocks):
        assert hdr[:2] == (16, 4) and hdr[13:] == (-1,) * 5, f'bloque {b}: cabecera {hdr}'
        pos = {i: (op, a) for i, op, a in ins}
        for e in range(N_EVENTS):
            assert pos[hdr[2 + e]] == (0x00, (e,)), f'bloque {b}: evento {e} no empieza con 00 02 {e}'
        # 2) saltos 08 caen en inicio de instrucción
        assert all(a[0] in pos for i, op, a in ins if op == 0x08), f'bloque {b}: salto 08 fuera de instrucción'
    # 3) cobertura: cada slot referenciado exactamente una vez, rangos contiguos por bloque
    cnt = collections.Counter()
    rng = collections.defaultdict(list)
    for b, (hdr, ins, _) in enumerate(blocks):
        for i, op, a in ins:
            for r in msg_refs(op, a):
                cnt[r[0]] += 1
                rng[b].append(r[0])
    assert set(cnt) == set(range(N_SLOTS)), f'faltan {sorted(set(range(N_SLOTS)) - set(cnt))[:10]}'
    assert all(v == 1 for v in cnt.values()), 'slot referenciado más de una vez'
    prev = -1
    for b in sorted(rng):
        s = sorted(rng[b])
        assert s == list(range(s[0], s[-1] + 1)), f'bloque {b}: rango no contiguo'
        assert s[0] > prev, f'bloque {b}: rangos desordenados'
        prev = s[-1]
    assert all(m['jp'] == 'Dummy String' for m in msgs[N_SLOTS:]), 'slots finales no son Dummy String'
    # 4) las variantes de 18/1B son del protagonista/pareja, y las condiciones empiezan con "１．"
    for b, (hdr, ins, _) in enumerate(blocks):
        for i, op, a in ins:
            for s, kind, pid, *_ in msg_refs(op, a):
                if kind in ('victoria', 'derrota'):
                    assert msgs[s]['jp'].lstrip('/\n').startswith('１．'), f'#{s} no parece condición'
                if kind == 'eleccion':
                    assert '選択' in msgs[s]['jp'], f'#{s} no parece elección'
    assert set(ESCENARIOS) == set(range(N_BLOCKS))
    # 5) los bloques siguen el orden de la tabla oficial de títulos y la cubren entera
    ids = [ESCENARIOS[b][2] for b in range(N_BLOCKS) if ESCENARIOS[b][2] is not None]
    assert ids == sorted(ids) and set(ids) == set(range(len(TITULOS))), 'orden de títulos roto'
    for b in range(N_BLOCKS):  # un bloque con mensajes nunca queda sin título
        assert ESCENARIOS[b][2] is not None or not rng.get(b), f'bloque {b} sin título'
    ovl = os.path.join(DUMP, 'ovl_strings.jsonl')
    if os.path.exists(ovl):
        with open(ovl, encoding='utf-8') as f:
            tabla = {}
            for r in map(json.loads, f):
                for ref in r['refs'] if r['file'] == 'IMIS' else []:
                    if ref.startswith('ptr@'):
                        p = int(ref[4:], 16)
                        if 0x1FB74 <= p <= 0x1FD74:
                            tabla[(p - 0x1FB70) // 4] = r['jp']
        assert [tabla[i] for i in range(1, len(TITULOS))] == TITULOS[1:], 'TITULOS no coincide con IMIS'
    n_ins = sum(len(ins) for _, ins, _ in blocks)
    print(f'OK: {N_BLOCKS} bloques, {n_ins} instrucciones, {len(cnt)} slots referenciados una vez cada uno, '
          f'{len(msgs) - N_SLOTS} Dummy String')


if __name__ == '__main__':
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        sys.exit(1)
    cmd, rest = args[0], args[1:]
    if cmd == 'map':
        cmd_map(*rest)
    elif cmd == 'disasm':
        cmd_disasm(int(rest[0], 0), *rest[1:])
    elif cmd == 'selftest':
        cmd_selftest(*rest)
    else:
        print(__doc__)
        sys.exit(1)
