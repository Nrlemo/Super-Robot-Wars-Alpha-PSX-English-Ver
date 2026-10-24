"""Busca en código MIPS (EXE + overlays) instrucciones que armen direcciones dentro de un rango.

Uso: find_addr_refs.py <inicio_hex> <fin_hex> <archivo> [...]
Detecta el patrón lui rX,HI + (addiu|ori|lw|sw|lh|sh|lb|lbu|sb|lhu...) rY,LO(rX) en las 16 instrucciones siguientes.
También reporta palabras de datos de 32 bits dentro del rango (punteros en tablas).
"""
import struct
import sys
from pathlib import Path

MEM_OPS = {0x20, 0x21, 0x23, 0x24, 0x25, 0x28, 0x29, 0x2B, 0x22, 0x26, 0x2A, 0x2E, 0x32, 0x3A}  # loads/stores (+lwc2/swc2)
ALU_OPS = {0x08, 0x09, 0x0D}  # addi, addiu, ori


def scan(path: Path, lo: int, hi: int):
    data = path.read_bytes()
    start = 0x800 if data[:8] == b'PS-X EXE' else 0
    words = struct.unpack_from(f'<{(len(data) - start) // 4}I', data, start)
    hits = []
    for i, w in enumerate(words):
        if w >> 26 == 0x0F:  # lui
            rt, imm = (w >> 16) & 31, w & 0xFFFF
            for j in range(i + 1, min(i + 17, len(words))):
                x = words[j]
                op, rs = x >> 26, (x >> 21) & 31
                if rs == rt and (op in MEM_OPS or op in ALU_OPS):
                    lo16 = x & 0xFFFF
                    addr = ((imm << 16) + (lo16 if op == 0x0D else (lo16 - 0x10000 if lo16 & 0x8000 else lo16))) & 0xFFFFFFFF
                    if lo <= addr <= hi:
                        hits.append((start + j * 4, f'lui+op{op:#04x} → {addr:#010x}'))
                if (x >> 16) & 31 == rt and op not in MEM_OPS and x != 0:  # rt reescrito: cortar
                    if op in ALU_OPS or op == 0x0F:
                        break
        if lo <= w <= hi:
            hits.append((start + i * 4, f'palabra de datos {w:#010x}'))
    return hits


if __name__ == '__main__':
    lo, hi = int(sys.argv[1], 16), int(sys.argv[2], 16)
    total = 0
    for f in sys.argv[3:]:
        for off, desc in scan(Path(f), lo, hi):
            print(f'{f}: +{off:#07x} {desc}')
            total += 1
    print(f'total: {total}')
