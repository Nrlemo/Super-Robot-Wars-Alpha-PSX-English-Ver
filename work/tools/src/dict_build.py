"""Construye work/translation/{dc,dr}_en.jsonl desde work/translation/dict_src/*.txt.

Formato fuente: "#id Nombre | Corto | Seiyuu" (dc) o "#id Nombre" (dr), luego un
parrafo por linea. Re-flow a 46 columnas; si no entra, se funden parrafos; si
aun no entra, las filas sobrantes van a "en_overflow".
Uso: python3 work/tools/src/dict_build.py dc dr
"""
import json,re,sys,glob,textwrap
import os
R=os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','..')+'/'
SRC=R+'translation/dict_src/'
W=46  # tope de bytes de una línea (option_dict.LINE_MAX); en pantalla 46 letras ≈ 210 px de ~270
SERIES={
'機動戦士Ｚガンダム':'Mobile Suit Zeta Gundam',
'機動戦士Ｖガンダム':'Mobile Suit Victory Gundam',
'聖戦士ダンバイン':'Aura Battler Dunbine',
'新機動戦記ガンダムＷ':'Mobile Suit Gundam Wing',
'機動戦士ガンダムＺＺ':'Mobile Suit Gundam ZZ',
'超時空要塞マクロス　愛・おぼえていますか':'Macross: Do You Remember Love?',
'超時空要塞マクロス　愛・おぼえていますか　':'Macross: Do You Remember Love?',
'超時空要塞マクロス \n愛・おぼえていますか':'Super Dimension Fortress Macross:\nDo You Remember Love?',
'新世紀エヴァンゲリオン':'Neon Genesis Evangelion',
'THE END OF EVANGELION':'The End of Evangelion',
'マジンガーＺ':'Mazinger Z',
'超機大戦ＳＲＸ':'Super War Machine SRX',
'機動戦士ガンダム':'Mobile Suit Gundam',
'超獣機神ダンクーガ':'Super Beast Machine God Dancouga',
'機動戦士ガンダム　逆襲のシャア':"Mobile Suit Gundam: Char's Counterattack",
'ゲッターロボ':'Getter Robo',
'ゲッターロボＧ':'Getter Robo G',
'真・ゲッターロボ':'Shin Getter Robo',
'真・ゲッターロボ（原作漫画版）':'Shin Getter Robo (Original Manga)',
'トップをねらえ！':'Aim for the Top! Gunbuster',
'勇者ライディーン':'Brave Raideen',
'ジャイアント・ロボ \nTHE ANIMATION～地球が静止する日':'Giant Robo THE ANIMATION:\nThe Day the Earth Stood Still',
'ジャイアント・ロボ THE ANIMATION～地球が静止する日':'Giant Robo: The Day the Earth Stood Still',
'機動戦士ガンダム００８３～スターダストメモリー':'Mobile Suit Gundam 0083: Stardust Memory',
'機動戦士ガンダム００８３ \n～スターダストメモリー':'Mobile Suit Gundam 0083:\nStardust Memory',
'機動戦士ガンダム００８０～ポケットの中の戦争':'Mobile Suit Gundam 0080: War in the Pocket',
'機動戦士ガンダム００８０ \n～ポケットの中の戦争':'Mobile Suit Gundam 0080:\nWar in the Pocket',
'機動戦士ガンダムＦ９１':'Mobile Suit Gundam F91',
'機動戦士ガンダムＦ９０':'Mobile Suit Gundam F90',
'超電磁マシーン　ボルテスﾖﾟ':'Super Electromagnetic Machine Voltes V',
'超電磁マシーン  ボルテスﾖﾟ':'Super Electromagnetic Machine Voltes V',
'超電磁ロボ　コン・バトラーＶ':'Super Electromagnetic Robo Combattler V',
'超電磁ロボ  コン・バトラーＶ':'Super Electromagnetic Robo Combattler V',
'グレートマジンガー':'Great Mazinger',
'オリジナル':'Banpresto Original',
'超時空要塞マクロス':'The Super Dimension Fortress Macross',
'超時空要塞マクロス　':'The Super Dimension Fortress Macross',
'無敵鋼人ダイターン３':'Invincible Steel Man Daitarn 3',
'マクロスプラス':'Macross Plus',
'劇場版マジンガーシリーズ':'Mazinger Movie Series',
'魔装機神 \nTHE LORD OF ELEMENTAL':'Masou Kishin:\nThe Lord of Elemental',
'魔装機神　THE LORD OF ELEMENTAL':'Masou Kishin: The Lord of Elemental',
'新機動戦記ガンダムＷ ～Endless Waltz':'Gundam Wing: Endless Waltz',
}
def unit(t):
    import unicodedata
    t=unicodedata.normalize('NFKC',t)
    t=t.replace('メット','met').replace('ルフトン','lufton').replace('～','+').replace('~','+').replace('17.4mm','17.4m')
    m=re.fullmatch(r'(?:(\d+)億)?(?:(\d+)万)?t',t.replace(' ','')) if ('億' in t or '万' in t) else None
    if m:
        v=int(m.group(1) or 0)*10**8+int(m.group(2) or 0)*10**4
        t=f'{v:,}t'
    return t
INDEX_EXTRA={}
def parse(kind):
    T={}
    for fn in sorted(glob.glob(SRC+f'{kind}_*.txt')):
        cur=None
        for line in open(fn):
            line=line.rstrip('\n')
            if not line.strip() or line.startswith('//'): continue
            if line.startswith('#'):
                m=re.match(r'#(\d+)\s+(.*)',line)
                cur=int(m.group(1)); T[cur]={'head':[s.strip().replace('\\n','\n') for s in m.group(2).split('|')],'paras':[]}  # '\\n' = salto en el campo
            else: T[cur]['paras'].append(line.strip())
    return T
def _rows(paras):
    return sum(len(textwrap.wrap(p,W,break_on_hyphens=False)) for p in paras)
def wrap(paras,n):
    paras=list(paras); merged=False
    # drop paragraph breaks one at a time (the one saving most rows) until it fits
    while _rows(paras)>n and len(paras)>1:
        best=None
        for k in range(len(paras)-1):
            t=paras[:k]+[paras[k]+' '+paras[k+1]]+paras[k+2:]
            r=_rows(t)
            if best is None or r<best[0]: best=(r,t)
        paras=best[1]; merged=True
    out=[]
    for p in paras: out+=textwrap.wrap(p,W,break_on_hyphens=False)
    return out,merged
def build(kind):
    T=parse(kind); body0=156 if kind=='dc' else 180
    res=[];issues=[]
    for l in open(R+f'dump/{kind}.jsonl'):
        e=json.loads(l); i=e['id']
        o={'id':i,'size':e['size'],'fields':e['fields']}
        if i==0 or not e['fields']:
            o['en']=[]
            if i==0:  # index table of names: fill from entries later
                o['_index']=True
            res.append(o); continue
        if i not in T: issues.append(f'{kind} #{i} MISSING'); o['en']=None; res.append(o); continue
        t=T[i]; h=t['head']
        body=[x for x in e['fields'] if x['off']>=body0]
        rows,merged=wrap(t['paras'],len(body))
        en=[]
        for x in e['fields']:
            off=x['off']
            if off>=body0: continue
            if off==0: en.append(h[0])
            elif kind=='dc' and off==48: en.append(h[1])
            elif kind=='dc' and off==132: en.append(h[2])
            elif kind=='dr' and off in(48,80): en.append(unit(x['text']))
            else:
                s=SERIES.get(x['text'])
                if s is None: issues.append(f'{kind} #{i} series? {x["text"]!r}'); s='??'
                en.append(s)
        flags=[]
        en+=rows[:len(body)]+['']*(len(body)-len(rows))
        if len(rows)>len(body):
            o['en_overflow']=rows[len(body):]; flags.append(f'overflow+{len(rows)-len(body)}')
        if merged: flags.append('paragraphs_merged')
        o['en']=en
        if flags: o['flags']=flags
        # checks
        lim={0:47,48:19 if kind=='dc' else 31,68:63,132:19,80:31,112:63}  # campos reales: option_dict.LAYOUT
        for x,s in zip(e['fields'],en):
            if any(ord(c)>126 for c in s.replace('\n','')): issues.append(f'{kind} #{i} nonascii {s!r}')
            L=lim.get(x['off'])
            if L and x['off']<body0 and len(s)>L: issues.append(f'{kind} #{i} long@{x["off"]} {len(s)} {s!r}')
        if flags: issues.append(f'{kind} #{i} {flags} rows {len(rows)}/{len(body)}')
        res.append(o)
    # index table (id 0): match each JP name to an entry's name field
    import unicodedata
    def nk(t):
        t=unicodedata.normalize('NFKC',t)
        t=re.sub(r'[（(].*?[）)]','',t)
        return t.replace('-','ー').replace('=','・').replace('＝','・').replace(' ','')
    names={}
    for r in res[1:]:
        if r.get('en') and r['fields'] and r['fields'][0]['off']==0:
            names.setdefault(nk(r['fields'][0]['text']),r['en'][0])
    idx=res[0]; idx['en']=[]
    for x in idx['fields']:
        v=names.get(nk(x['text'])) or INDEX_EXTRA.get(nk(x['text']))
        if v is None: issues.append(f'{kind} index? {x["text"]!r}')
        idx['en'].append(v)
    del idx['_index']
    issues+=weapon_check(kind,res)
    return res,issues
# armas del glosario citadas en la ficha JP cuyo nombre inglés (en_final o en_short) no aparece en el EN (#47)
WEAPON_OK={  # menciones descriptivas, no el nombre del arma: no avisar
('dc',208,'破壊光線'),('dr',13,'メガ粒子砲'),('dr',77,'ビーム砲'),('dr',79,'サイコミュ式ビームソード'),('dr',100,'ビーム砲'),
('dr',169,'バルカン砲'),('dr',227,'体当たり'),('dr',232,'溶解液'),('dr',291,'天空剣Vの字斬り'),('dr',308,'体当たり'),
('dr',347,'加粒子砲'),('dr',352,'溶解液'),('dr',417,'リミッター解除')}
def weapon_check(kind,res):
    import csv,unicodedata
    nf=lambda t:unicodedata.normalize('NFKC',t)
    simp=lambda s:re.sub(r'[^a-z0-9]','',s.lower())
    W={}
    for g in csv.DictReader(open(R+'glossary/glossary.csv',encoding='utf-8')):
        j=nf(re.sub(r'\s*\(.*?\)','',g['jp']))
        if g['category']=='weapon' and len(j)>=3 and j!='クロー':  # クロー: falsos positivos (クローディア…)
            W.setdefault(j,set()).update(x for x in (g['en_final'],g['en_short']) if x)
    out=[]
    for r in res[1:]:
        if not r.get('en'): continue
        jp=nf(''.join(x['text'] for x in r['fields'])); en=simp(' '.join(r['en']+r.get('en_overflow',[])))
        hit=[w for w in W if w in jp]
        for w in hit:
            if any(w!=o and w in o for o in hit) or (kind,r['id'],w) in WEAPON_OK: continue
            if not any(simp(e) in en for e in W[w]): out.append(f'{kind} #{r["id"]} arma? {w} → {" / ".join(sorted(W[w]))}')
    return out
if __name__=='__main__':
    for kind in sys.argv[1:]:
        res,iss=build(kind)
        with open(R+f'translation/{kind}_en.jsonl','w') as f:
            for o in res: f.write(json.dumps(o,ensure_ascii=False)+'\n')
        print('\n'.join(iss)); print(kind,'done',sum(1 for r in res if r.get('en')))
