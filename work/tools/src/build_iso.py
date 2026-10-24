"""Construye una imagen .bin/.cue a partir del FS JP extraído + archivos reemplazados.

Uso: build_iso.py <salida.bin> [RUTA_EN_ISO=archivo_local ...]
  ej: build_iso.py build/poc.bin SNMAP/SNMSG.BIN=build/poc/SNMSG.BIN

No copia el FS: genera un layout.xml con rutas absolutas (base work/iso_jp) y
reemplaza el atributo source de los archivos indicados. Nunca escribe sobre la ISO original.
"""
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

WORK = Path(__file__).resolve().parents[2]
BASE = WORK / 'iso_jp'
MKPSXISO = WORK / 'tools' / 'bin' / 'mkpsxiso'


def make_layout(out_bin: Path, overrides: dict[str, Path]) -> Path:
    tree = ET.parse(BASE / 'layout.xml')
    root = tree.getroot()
    root.set('image_name', str(out_bin))
    root.set('cue_sheet', str(out_bin.with_suffix('.cue')))
    track = root.find('track')
    track.find('license').set('file', str(BASE / 'license_data.dat'))
    dtree = track.find('directory_tree')
    dtree.set('source', str(BASE))
    pending = dict(overrides)

    def walk(node, prefix):
        for child in node:
            if child.tag == 'dir':
                walk(child, f"{prefix}{child.get('name')}/")
            elif child.tag == 'file':
                path = prefix + child.get('name')
                if path in pending:
                    child.set('source', str(pending.pop(path).resolve()))
    walk(dtree, '')
    if pending:
        sys.exit(f'rutas no encontradas en el layout: {list(pending)}')
    xml_path = out_bin.with_suffix('.xml')
    tree.write(xml_path, encoding='utf-8', xml_declaration=True)
    return xml_path


def main(out: str, *pairs: str) -> None:
    out_bin = Path(out).resolve()
    if out_bin.parent == WORK.parent:
        sys.exit('me niego a escribir en la raíz del proyecto (donde vive la ISO original)')
    overrides = {}
    for p in pairs:
        iso_path, local = p.split('=', 1)
        overrides[iso_path] = Path(local)
    xml_path = make_layout(out_bin, overrides)
    subprocess.run([str(MKPSXISO), '-y', '-q', str(xml_path)], check=True)
    print(f'OK → {out_bin} (+ .cue, layout {xml_path.name})')


if __name__ == '__main__':
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    main(*sys.argv[1:])
