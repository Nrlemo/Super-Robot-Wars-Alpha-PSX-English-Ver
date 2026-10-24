"""Lectura mínima de ISO9660 sobre imágenes MODE2/2352 (solo archivos de datos Form1).

Uso como script:
  isofs.py list    <imagen.bin>
  isofs.py extract <imagen.bin> <dir_salida> [--layout-from <imagen_ref.bin>]

--layout-from toma LBA/tamaños del directorio de otra imagen (útil para la imagen china,
cuyo parche corrompe los sectores de directorio de ANMTST/ y BATTLE/).
Los archivos XA/STR (Form2 entrelazado) se omiten: no contienen texto.
"""
import struct
import sys
from dataclasses import dataclass
from pathlib import Path

SECTOR = 2352
USER_OFF = 24          # sync(12) + header(4) + subheader(8)
USER_SIZE = 2048
FORM2_EXT = ('.STR', '.XA')


@dataclass
class Entry:
    path: str          # p.ej. "SNMAP/SNMSG.BIN" (sin ";1")
    lba: int
    size: int

    @property
    def sectors(self) -> int:
        return (self.size + USER_SIZE - 1) // USER_SIZE


class Image:
    def __init__(self, path):
        self.f = open(path, 'rb')

    def read_sectors(self, lba: int, count: int) -> bytes:
        out = bytearray()
        for i in range(count):
            self.f.seek((lba + i) * SECTOR + USER_OFF)
            out += self.f.read(USER_SIZE)
        return bytes(out)

    def read_file(self, e: Entry) -> bytes:
        return self.read_sectors(e.lba, e.sectors)[:e.size]

    def entries(self) -> list[Entry]:
        pvd = self.read_sectors(16, 1)
        assert pvd[1:6] == b'CD001', 'no es ISO9660'
        root = pvd[156:190]
        out: list[Entry] = []
        self._walk(struct.unpack_from('<I', root, 2)[0], struct.unpack_from('<I', root, 10)[0], '', out)
        return sorted(out, key=lambda e: e.lba)

    def _walk(self, lba, size, prefix, out):
        data = self.read_sectors(lba, (size + USER_SIZE - 1) // USER_SIZE)
        o = 0
        while o < len(data):
            ln = data[o]
            if ln == 0:  # los registros no cruzan sectores: saltar al siguiente
                o = (o // USER_SIZE + 1) * USER_SIZE
                continue
            rec = data[o:o + ln]
            name = rec[33:33 + rec[32]]
            if name not in (b'\x00', b'\x01'):
                n = name.decode('latin1').split(';')[0]
                elba, esz = struct.unpack_from('<I', rec, 2)[0], struct.unpack_from('<I', rec, 10)[0]
                if rec[25] & 2:
                    self._walk(elba, esz, f'{prefix}{n}/', out)
                else:
                    out.append(Entry(prefix + n, elba, esz))
            o += ln


def extract(img_path, out_dir, layout_from=None) -> list[Entry]:
    img = Image(img_path)
    entries = Image(layout_from).entries() if layout_from else img.entries()
    out = Path(out_dir)
    for e in entries:
        if e.path.upper().endswith(FORM2_EXT):
            continue
        dst = out / e.path
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_bytes(img.read_file(e))
    return entries


if __name__ == '__main__':
    cmd = sys.argv[1] if len(sys.argv) > 1 else ''
    if cmd == 'list':
        for e in Image(sys.argv[2]).entries():
            print(f'{e.path:28s} lba={e.lba:7d} size={e.size:10d}')
    elif cmd == 'extract':
        ref = sys.argv[sys.argv.index('--layout-from') + 1] if '--layout-from' in sys.argv else None
        es = extract(sys.argv[2], sys.argv[3], ref)
        print(f'{len(es)} entradas (XA/STR omitidos)')
    else:
        sys.exit(__doc__)
