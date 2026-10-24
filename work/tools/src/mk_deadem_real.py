"""ISO de prueba de DEADMESS/EM con el texto real de un build (#28): los reemplazos del build + una frase de derribo real
copiada al piloto 331 (親衛隊兵, el que se derriba en la grabación CP04 y en el original no tiene frase).

Uso (desde work/): python3 tools/src/mk_deadem_real.py <build> <salida.bin> [slot_origen]
  <build> = carpeta de build/ (con manifest.json); slot_origen = slot de DEADMESS cuyo texto se copia (por defecto 398:
  Garuda, 3 renglones, de los más anchos). EM no se toca: la escena la elige el juego.
"""
import json, subprocess, sys
from pathlib import Path

W = Path(__file__).resolve().parents[2]
PILOT = 331


def main():
    build, out = Path(sys.argv[1]), Path(sys.argv[2])
    src_slot = int(sys.argv[3]) if len(sys.argv) > 3 else 398
    man = json.loads((build / 'manifest.json').read_text())['reemplazos']
    dm = bytearray((W.parent / man['SNMAP/DEADMESS.BIN']).read_bytes())
    so = 0x40 + src_slot * 256
    assert dm[so + 4], f'el slot {src_slot} está vacío'
    dm[PILOT >> 3] |= 1 << (PILOT & 7)
    for v in (0, 1):
        o = 0x40 + (2 * PILOT + v) * 256
        dm[o:o + 256] = dm[so:so + 256]
    out.parent.mkdir(parents=True, exist_ok=True)
    dmp = out.with_name('DEADMESS.BIN')
    dmp.write_bytes(dm)
    reps = [f'{rel}=' + (str(dmp) if rel == 'SNMAP/DEADMESS.BIN' else str(W.parent / src)) for rel, src in man.items()]
    print(f'{len(reps)} reemplazos; slot {src_slot} → piloto {PILOT}:', bytes(dm[so + 4:so + 256]).split(b'\0')[0])
    subprocess.run([sys.executable, str(W / 'tools/src/build_iso.py'), str(out), *reps], cwd=W, check=True)


if __name__ == '__main__':
    main()
