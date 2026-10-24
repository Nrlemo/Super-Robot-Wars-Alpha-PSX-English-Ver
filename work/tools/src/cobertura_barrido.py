"""Barrido de cobertura (#220/#221): busca cadenas Shift-JIS japonesas (>=4 caracteres) en los archivos de work/iso_jp y
marca las que no aparecen en los volcados (dump/, translation/, glossary/). Comparación aproximada por 4-gramas.
Correr desde la raíz del repo: python3 work/tools/src/cobertura_barrido.py > work/logs/cobertura.tsv
Salida: archivo, cadenas japonesas halladas, cadenas sin cubrir, ejemplos.
OJO: los archivos comprimidos (OPTION/DC.BIN, DR.BIN, ROBOT.RAF) y los gráficos dan ruido; ver notes/mdata.md y la auditoría (#223).
Resultado 2026-10-01: lo único con texto real sin mapear era SNMAP/MDATA.BIN, TEST/MDATA.BIN (hecho, #221) y OPTION/S.BIN (mapeado, #222).
"""
import os, re, json, glob, collections
R = 'work/iso_jp'
corpus = []
for p in glob.glob('work/dump/*.jsonl') + glob.glob('work/translation/*') + glob.glob('work/glossary/*.csv'):
    try:
        corpus.append(open(p, encoding='utf-8', errors='ignore').read())
    except Exception:
        pass
corpus = '\n'.join(corpus)
# escapes JSON: \n literal
corpus = corpus.replace('\\n', '\n')
G = {corpus[i:i + 4] for i in range(len(corpus) - 3)}
# run SJIS: pares lead(81-9f,e0-ef)+trail(40-fc) o half-width kana a1-df, ASCII imprimible dentro
pair = rb'(?:[\x81-\x9f\xe0-\xef][\x40-\x7e\x80-\xfc])'
rx = re.compile(rb'(?:' + pair + rb'|[\xa1-\xdf]){4,}')
res = collections.defaultdict(lambda: [0, 0, []])
for r, _, fs in os.walk(R):
    for f in fs:
        p = os.path.join(r, f)
        if os.path.getsize(p) > 40_000_000 or f.endswith(('.TIM', '.XA', '.STR', '.VAB', '.SEQ', '.dat')):
            continue
        d = open(p, 'rb').read()
        for m in rx.finditer(d):
            try:
                t = m.group().decode('cp932')
            except UnicodeDecodeError:
                continue
            if not re.search(r'[ぁ-んァ-ヴ一-龥ｦ-ﾟ]', t):
                continue
            k = os.path.relpath(p, R)
            res[k][0] += 1
            if not (t[:4] in G and t[-4:] in G):
                res[k][1] += 1
                if len(res[k][2]) < 4:
                    res[k][2].append(t[:30])
for k, (n, u, ex) in sorted(res.items(), key=lambda x: -x[1][1]):
    if u:
        print(f'{k}\t{n}\t{u}\t{ex}')
