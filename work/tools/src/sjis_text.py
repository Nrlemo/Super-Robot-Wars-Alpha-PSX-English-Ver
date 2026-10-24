"""Códec reversible entre bytes del juego (SJIS + códigos) y texto editable.

Reglas de decodificación:
  - par SJIS válido (cp932)      → carácter Unicode
  - 0x0A                         → "\n"
  - ASCII imprimible 0x20-0x7E   → tal cual (incluye variables $n $N $F $f)
  - kana medio ancho 0xA1-0xDF   → carácter half-width
  - cualquier otro byte / par    → escape {XX} o {XXXX} en hex

encode(decode(b)) == b para toda entrada (verificado en snmsg.py --check).
Las llaves literales no aparecen en el texto del juego; si hiciera falta, se escapan igual.
"""
import re

_ESC = re.compile(r'\{([0-9A-F]{2}|[0-9A-F]{4})\}')


def _is_lead(b: int) -> bool:
    return 0x81 <= b <= 0x9F or 0xE0 <= b <= 0xFC


def decode(data: bytes) -> str:
    out, i = [], 0
    while i < len(data):
        b = data[i]
        if _is_lead(b) and i + 1 < len(data):
            pair = data[i:i + 2]
            try:
                ch = pair.decode('cp932')
                if ch.encode('cp932') == pair and ch not in '{}':
                    out.append(ch)
                    i += 2
                    continue
            except UnicodeDecodeError:
                pass
            out.append('{%04X}' % int.from_bytes(pair, 'big'))
            i += 2
        elif b == 0x0A:
            out.append('\n')
            i += 1
        elif 0x20 <= b <= 0x7E and chr(b) not in '{}':
            out.append(chr(b))
            i += 1
        elif 0xA1 <= b <= 0xDF:
            out.append(bytes([b]).decode('cp932'))
            i += 1
        else:
            out.append('{%02X}' % b)
            i += 1
    return ''.join(out)


def encode(text: str) -> bytes:
    out, i = bytearray(), 0
    while i < len(text):
        m = _ESC.match(text, i)
        if m:
            out += bytes.fromhex(m.group(1))
            i = m.end()
            continue
        ch = text[i]
        if ch == '\n':
            out.append(0x0A)
        else:
            out += ch.encode('cp932')  # lanza UnicodeEncodeError si el carácter no existe en SJIS
        i += 1
    return bytes(out)
