"""Imágenes TIM de PSX (4/8/16 bpp): lectura, búsqueda en contenedores y PNG indexado ida y vuelta (#17).

Uso:
  tim.py <archivo.TIM> <salida.png> [clut_idx]      vista RGBA (compatibilidad)
  tim.py scan <archivo>...                          lista los TIM (offset, bpp, CLUT, VRAM)
  tim.py export <salida_dir> <ruta_en_iso>...       PNG indexado editable + vistas por CLUT + manifest.json
  tim.py import <manifest.json> <png_dir> <out_dir> reinyecta los PNG editados (misma CLUT y tamaño)
  tim.py selftest <ruta_en_iso>...                  export → import sin cambios = byte-idéntico

El PNG editable conserva los índices: al importar solo se escriben los píxeles; la CLUT del archivo
no se toca. Por eso el PNG debe seguir en modo indexado con la paleta intacta.
"""
import json
import os
import struct
import sys

import numpy as np
from PIL import Image

WORK = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
ISO = os.path.join(WORK, 'iso_jp')


def bgr555(c):
    c = np.asarray(c, dtype=np.uint16)
    rgb = np.stack([(c & 31) << 3, ((c >> 5) & 31) << 3, ((c >> 10) & 31) << 3], -1).astype(np.uint8)
    alpha = np.where(c == 0, 0, 255).astype(np.uint8)  # 0x0000 = transparente en PSX
    return np.concatenate([rgb, alpha[..., None]], -1)


def parse(data: bytes, off: int = 0):
    """Cabecera de un TIM en data[off:] → dict, o None si no es un TIM coherente."""
    if off + 20 > len(data) or data[off:off + 4] != b'\x10\0\0\0':
        return None
    flags = struct.unpack_from('<I', data, off + 4)[0]
    if flags not in (0, 1, 2, 3, 8, 9):
        return None
    o = off + 8
    t = {'off': off, 'bpp': {0: 4, 1: 8, 2: 16, 3: 24}[flags & 3], 'clut': None}
    if flags & 8:
        blen, cx, cy, cw, ch = struct.unpack_from('<IHHHH', data, o)
        if blen != 12 + cw * ch * 2 or not cw or not ch or cw > 256:
            return None
        t['clut'] = {'off': o + 12, 'xy': (cx, cy), 'wh': (cw, ch)}
        o += blen
    if o + 12 > len(data):
        return None
    blen, ix, iy, iw, ih = struct.unpack_from('<IHHHH', data, o)
    if blen != 12 + iw * ih * 2 or not (0 < iw <= 1024 and 0 < ih <= 512) or o + blen > len(data):
        return None
    if t['bpp'] in (4, 8) and not t['clut']:
        return None
    t.update(pix_off=o + 12, vram_xy=(ix, iy), vram_w=iw, h=ih, size=o + blen - off,
             w=iw * {4: 4, 8: 2, 16: 1, 24: 1}[t['bpp']])
    return t


def scan(data: bytes):
    out, i = [], 0
    while i + 20 <= len(data):
        t = parse(data, i)
        if t and t['bpp'] != 24:
            out.append(t)
            i += t['size']
        else:
            i += 4
    return out


def cluts(data, t):
    cw, ch = t['clut']['wh']
    return np.frombuffer(data, '<u2', cw * ch, t['clut']['off']).reshape(ch, cw)


def indices(data, t):
    pix = np.frombuffer(data, np.uint8, t['vram_w'] * 2 * t['h'], t['pix_off']).reshape(t['h'], -1)
    if t['bpp'] == 4:
        return np.stack([pix & 15, pix >> 4], -1).reshape(t['h'], t['w'])
    return pix


def read_tim(data: bytes, clut_idx: int = 0):
    t = parse(data)
    assert t, 'no es TIM'
    info = {'bpp': t['bpp'], 'img_xy': t['vram_xy'], 'vram_w': t['vram_w'], 'h': t['h']}
    if t['bpp'] == 16:
        c = np.frombuffer(data, '<u2', t['w'] * t['h'], t['pix_off']).reshape(t['h'], t['w'])
        return Image.fromarray(bgr555(c), 'RGBA'), info, None
    idx = indices(data, t)
    info.update(clut_xy=t['clut']['xy'], clut_wh=t['clut']['wh'])
    return Image.fromarray(bgr555(cluts(data, t)[clut_idx][idx]), 'RGBA'), info, (idx if t['bpp'] == 4 else None)


def indexed_png(idx, clut_row):
    rgba = bgr555(clut_row)
    im = Image.fromarray(idx.astype(np.uint8), 'P')
    im.putpalette(rgba[:, :3].flatten().tolist())
    if (rgba[:, 3] == 0).any():
        im.info['transparency'] = bytes(rgba[:, 3].tolist())
    return im


def save_png(im, path):
    kw = {'transparency': im.info['transparency']} if 'transparency' in im.info else {}
    im.save(path, optimize=False, **kw)


def stem(relpath, n, t):
    return f"{relpath.replace('/', '_').replace('.', '_')}__{n:02d}_{t['off']:06X}"


def export(outdir, relpaths):
    os.makedirs(os.path.join(outdir, 'editar'), exist_ok=True)
    os.makedirs(os.path.join(outdir, 'vistas'), exist_ok=True)
    man = []
    for rel in relpaths:
        data = open(os.path.join(ISO, rel), 'rb').read()
        for n, t in enumerate(scan(data)):
            s = stem(rel, n, t)
            e = {'file': rel, 'n': n, 'off': t['off'], 'bpp': t['bpp'], 'w': t['w'], 'h': t['h'],
                 'vram_xy': t['vram_xy'], 'png': f'editar/{s}.png', 'vistas': []}
            if t['bpp'] == 16:
                c = np.frombuffer(data, '<u2', t['w'] * t['h'], t['pix_off']).reshape(t['h'], t['w'])
                Image.fromarray(bgr555(c), 'RGBA').save(os.path.join(outdir, e['png']))
            else:
                cl, idx = cluts(data, t), indices(data, t)
                e.update(clut_xy=t['clut']['xy'], clut_wh=t['clut']['wh'], colors=int(t['clut']['wh'][0]),
                         used=sorted(int(i) for i in np.unique(idx)))
                save_png(indexed_png(idx, cl[0]), os.path.join(outdir, e['png']))
                for k in range(1, cl.shape[0]):
                    v = f'vistas/{s}_clut{k:02d}.png'
                    save_png(indexed_png(idx, cl[k]), os.path.join(outdir, v))
                    e['vistas'].append(v)
            man.append(e)
    json.dump(man, open(os.path.join(outdir, 'manifest.json'), 'w'), indent=1, ensure_ascii=False)
    return man


def png_to_bytes(data, t, png):
    """PNG editado → bytes de píxeles del TIM; ValueError con el motivo si no cumple."""
    im = Image.open(png)
    if im.size != (t['w'], t['h']):
        raise ValueError(f"tamaño {im.size} ≠ {(t['w'], t['h'])}")
    if t['bpp'] == 16:
        a = np.array(im.convert('RGBA')).astype(np.uint16)
        c = (a[..., 0] >> 3) | ((a[..., 1] >> 3) << 5) | ((a[..., 2] >> 3) << 10)
        orig = np.frombuffer(data, '<u2', t['w'] * t['h'], t['pix_off']).reshape(t['h'], t['w'])
        c = np.where(a[..., 3] == 0, 0, np.where(c == 0, 0x8000, c) | (orig & 0x8000)).astype('<u2')
        return c.tobytes()
    if im.mode != 'P':
        raise ValueError(f'modo {im.mode}: tiene que ser indexado (P)')
    n = t['clut']['wh'][0]
    want = bgr555(cluts(data, t)[0])[:, :3].flatten().tolist()
    pal = (im.getpalette() or [])[:3 * n]
    k = len(pal) // 3  # algunos editores recortan las entradas finales sin usar: se acepta
    if pal != want[:3 * k]:
        bad = [i for i in range(k) if pal[3 * i:3 * i + 3] != want[3 * i:3 * i + 3]]
        raise ValueError(f'paleta cambiada (entradas {bad[:8]})')
    idx = np.array(im)
    if idx.max() >= k:
        raise ValueError(f'índice {int(idx.max())} fuera de la paleta de {k} colores')
    idx = idx.astype(np.uint8)
    if t['bpp'] == 4:
        idx = idx.reshape(t['h'], -1, 2)
        return (idx[..., 0] | (idx[..., 1] << 4)).astype(np.uint8).tobytes()
    return idx.tobytes()


def import_(manifest, pngdir, outdir):
    man = json.load(open(manifest))
    files, errors, done = {}, [], 0
    for e in man:
        png = os.path.join(pngdir, os.path.basename(e['png']))
        if not os.path.exists(png):
            continue
        if e['file'] not in files:
            files[e['file']] = bytearray(open(os.path.join(ISO, e['file']), 'rb').read())
        data = files[e['file']]
        t = parse(bytes(data), e['off'])
        try:
            b = png_to_bytes(bytes(data), t, png)
        except ValueError as x:
            errors.append(f"{os.path.basename(png)}: {x}")
            continue
        data[t['pix_off']:t['pix_off'] + len(b)] = b
        done += 1
    for rel, data in files.items():
        p = os.path.join(outdir, rel)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        open(p, 'wb').write(data)
    return done, errors


def selftest(relpaths):
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        export(d, relpaths)
        n, err = import_(os.path.join(d, 'manifest.json'), os.path.join(d, 'editar'), os.path.join(d, 'out'))
        assert not err, err
        for rel in relpaths:
            a = open(os.path.join(ISO, rel), 'rb').read()
            b = open(os.path.join(d, 'out', rel), 'rb').read()
            print(f"{rel}: {'OK' if a == b else 'DISTINTO'}")
            assert a == b
        print(f'{n} imágenes ida y vuelta byte-idénticas')


if __name__ == '__main__':
    cmd = sys.argv[1] if len(sys.argv) > 1 else ''
    if cmd == 'scan':
        for rel in sys.argv[2:]:
            for n, t in enumerate(scan(open(rel, 'rb').read())):
                print(f"{rel} #{n} off=0x{t['off']:X} {t['bpp']}bpp {t['w']}x{t['h']} vram={t['vram_xy']} "
                      f"clut={t['clut'] and (t['clut']['xy'], t['clut']['wh'])}")
    elif cmd == 'export':
        print(len(export(sys.argv[2], sys.argv[3:])), 'imágenes')
    elif cmd == 'import':
        n, err = import_(sys.argv[2], sys.argv[3], sys.argv[4])
        print(n, 'importadas')
        for x in err:
            print('ERROR', x)
        sys.exit(1 if err else 0)
    elif cmd == 'selftest':
        selftest(sys.argv[2:])
    else:
        im, info, _ = read_tim(open(sys.argv[1], 'rb').read(), int(sys.argv[3]) if len(sys.argv) > 3 else 0)
        im.save(sys.argv[2])
        print(info, im.size)
