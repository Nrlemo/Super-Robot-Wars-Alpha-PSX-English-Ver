"""Auditoría (#223): ¿queda texto japonés sin cubrir en los archivos comprimidos?
Descomprime OPTION/DC.BIN, OPTION/DR.BIN y UNITPRAM/ROBOT.RAF (LZSS, notes/compresion.md) y busca corridas de SJIS
japonés (≥3 caracteres) en los bytes descomprimidos que NO estén dentro de un campo ya volcado/traducible.
  DC/DR: los campos son los de option_dict.fields() (lo que dump/dc.jsonl, dump/dr.jsonl guardan).
  ROBOT.RAF: los campos son los de robot_raf.parse() (nombres de unidad y arma, glossary.csv); el resto de las
             corridas se listan para revisión (suelen ser descripciones o claves).
Uso (desde work/tools/src): python3 auditoria_comprimidos.py [--ejemplos N]
Sale con código 1 si DC/DR tienen texto sin cubrir.
"""
import os
import re
import sys

import option_dict as od
import robot_raf as rr

RUN = re.compile(rb'(?:[\x81-\x9f\xe0-\xef][\x40-\x7e\x80-\xfc]|[\xa1-\xcc\xce-\xdf]){3,}')   # 0xCD = relleno de los campos de DC/DR, no kana
JP = re.compile(r'[ぁ-んァ-ヴ一-龥]')


def runs(raw):
    for m in RUN.finditer(raw):
        try:
            t = m.group().decode('cp932')
        except UnicodeDecodeError:
            continue
        if JP.search(t):
            yield m.start(), m.end(), t


def audit_dict(fmt, ejemplos):
    miss, total = [], 0
    for i, raw in od.entries(od.iso_path(fmt)):
        cov = [(f['off'], f['off'] + len(f['text'].encode('cp932'))) for f in od.fields(raw)]
        for a, b, t in runs(raw):
            total += 1
            if not any(s <= a and b <= e for s, e in cov):
                miss.append((i, a, t))
    print(f'{fmt.upper()}: {total} corridas japonesas, {len(miss)} fuera de los campos volcados')
    for i, a, t in miss[:ejemplos]:
        print(f'   entrada {i} +{a:#x}: {t[:40]}')
    return miss


def audit_robot(ejemplos):
    data = open(os.path.join(rr.WORK, 'iso_jp', 'UNITPRAM', 'ROBOT.RAF'), 'rb').read()
    n = total = 0
    sample = []
    for _, _, raw in rr.entries(data):
        for a, b, t in runs(raw):
            total += 1
            n += 1
            if len(sample) < ejemplos:
                sample.append((a, t))
    print(f'ROBOT.RAF: {total} corridas japonesas en el registro descomprimido (nombres de unidad/arma: ya cubiertos por robot_raf)')
    for a, t in sample:
        print(f'   +{a:#x}: {t[:40]}')


def main():
    ej = int(sys.argv[sys.argv.index('--ejemplos') + 1]) if '--ejemplos' in sys.argv else 8
    miss = audit_dict('dc', ej) + audit_dict('dr', ej)
    audit_robot(ej)
    sys.exit(1 if miss else 0)


if __name__ == '__main__':
    main()
