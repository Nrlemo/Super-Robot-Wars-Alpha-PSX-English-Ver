"""Control de las capturas de una ruta de regresión (salida de drive.sh / regresion.sh).

Uso: shots_check.py <dir> [--expect N] [--ref <dir_ref>] [--out <diff.png>]
  - Cuenta las capturas f*.png y marca las uniformes (un solo color: pantalla negra, posible cuelgue).
  - Falla (código 1) si faltan capturas (--expect: el emulador se cerró o colgó antes), si todas son uniformes o si
    todas son idénticas entre sí (emulador congelado).
  - --ref: compara cuadro a cuadro con la misma ruta de otra build (mismo número de cuadro f#####) y arma diff.png con
    [referencia | esta build | píxeles distintos] de los cuadros que cambiaron. Los cambios NO son error: el texto
    traducido y el azar del combate cambian píxeles (notes/pilot_bin.md); la hoja es para revisar a ojo.
"""
import argparse
import hashlib
import sys
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageStat

W, H = 320, 240


def frames(d: Path) -> dict:
    """Número de cuadro ('f04900') → PNG. raw2png.py nombra f#####_WxH_BPP.png (la resolución cambia por pantalla)."""
    return {p.name.split('_')[0]: p for p in sorted(d.glob('f[0-9]*.png'))}


def uniform(im: Image.Image) -> bool:
    return max(ImageStat.Stat(im.convert('RGB')).stddev) < 1.0


def check(d: Path, expect: int | None = None) -> tuple[list, dict]:
    fs = frames(d)
    problems = []
    if expect is not None and len(fs) < expect:
        problems.append(f'{len(fs)} capturas de {expect} esperadas (¿el emulador se cerró o colgó antes?)')
    if not fs:
        return problems or ['sin capturas'], {'capturas': 0}
    ims = {k: Image.open(p).convert('RGB') for k, p in fs.items()}
    uni = [k for k, im in ims.items() if uniform(im)]
    if len(uni) == len(ims):
        problems.append('todas las capturas son de un solo color (¿pantalla negra / cuelgue?)')
    if len(ims) > 1 and len({hashlib.sha1(im.tobytes()).hexdigest() for im in ims.values()}) == 1:
        problems.append('todas las capturas son idénticas (¿emulador congelado?)')
    return problems, {'capturas': len(fs), 'uniformes': uni}


def compare(d: Path, ref: Path, out: Path) -> tuple[list, list]:
    """(cuadros que cambiaron con % de píxeles distintos, cuadros que están en una sola de las dos corridas)."""
    a, b = frames(ref), frames(d)
    rows = []
    for k in sorted(set(a) & set(b)):
        ia = Image.open(a[k]).convert('RGB').resize((W, H))
        ib = Image.open(b[k]).convert('RGB').resize((W, H))
        diff = ImageChops.difference(ia, ib)
        if diff.getbbox() is None:
            continue
        mask = diff.convert('L').point(lambda v: 255 if v else 0)
        rows.append((k, 100 * mask.histogram()[255] / (W * H), ia, ib, mask))
    if rows:
        sheet = Image.new('RGB', (3 * W, H * len(rows)))
        draw = ImageDraw.Draw(sheet)
        for i, (k, pct, ia, ib, mask) in enumerate(rows):
            for j, im in enumerate((ia, ib, mask.convert('RGB'))):
                sheet.paste(im, (j * W, i * H))
            draw.text((4, i * H + 4), f'{k} ref', fill=(255, 255, 0))
            draw.text((W + 4, i * H + 4), f'{k} nueva · {pct:.1f}% distinto', fill=(255, 255, 0))
        sheet.save(out)
    return [(k, round(pct, 2)) for k, pct, *_ in rows], sorted(set(a) ^ set(b))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('dir', type=Path)
    ap.add_argument('--expect', type=int, help='cantidad de capturas esperada (SHOT_FRAMES de la ruta)')
    ap.add_argument('--ref', type=Path, help='misma ruta de otra build, para comparar')
    ap.add_argument('--out', type=Path, help='hoja de diferencias (default: <dir>/diff.png)')
    a = ap.parse_args(argv)
    problems, info = check(a.dir, a.expect)
    print(f'{a.dir.name}: {info["capturas"]} capturas, {len(info.get("uniformes", []))} de un solo color')
    if a.ref:
        if a.ref.is_dir():
            changed, only = compare(a.dir, a.ref, a.out or a.dir / 'diff.png')
            print(f'  vs {a.ref}: {len(changed)} cuadros distintos'
                  + (f' → {a.out or a.dir / "diff.png"}' if changed else '')
                  + (f'; en una sola corrida: {", ".join(only)}' if only else ''))
        else:
            print(f'  (sin referencia: no existe {a.ref})')
    for p in problems:
        print('  FALLA:', p)
    return 1 if problems else 0


if __name__ == '__main__':
    sys.exit(main())
