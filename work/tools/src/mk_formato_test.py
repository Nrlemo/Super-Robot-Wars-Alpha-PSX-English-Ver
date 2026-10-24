"""PoC del formato de diálogo `Nombre: texto` (issue #23): escribe una copia de dump/script.jsonl con la escena del
escenario 62 (script 234, L0–L26, la que muestra la ruta cp12) traducida en una variante del formato.
Uso: mk_formato_test.py <variante> <salida.jsonl>
  A        `Nombre: texto`, renglones 2–3 sin sangría (recomendada en guia_estilo_personajes.md §1.3)
  A2       ídem con 2 espacios al inicio de los renglones 2–3
  B        `Nombre「texto」` / `Nombre（pensamiento）`, renglones 2–3 con 　 como en japonés
  N        A + `$n` como hablante (L1) y dentro de la frase (L12)
  mapa     copia de dump/snmsg.jsonl con el diálogo del mapa del prólogo (slots 2–30) en formato A
  ancho    estrés de la caja de escena (#31): reglas de dígitos de 208…320 px, 4 y 5 renglones, línea sin saltos
Pensamientos (（…）) → `Nombre: (texto)`; 『』 → comillas dobles."""
import json, os, sys

WORK = os.path.normpath(os.path.join(os.path.dirname(__file__), '..', '..'))

# (línea, hablante, pensamiento, renglones)
LINES = [
    (0, 'Laodicea', False, ["Boddole's Zentradi flagship", 'made peace with the Earthlings?!']),
    (1, 'Euzeth', False, ['Yes...']),
    (2, 'Laodicea', False, ['Their aim... is to win', 'their war against the Meltrandi?']),
    (3, 'Laodicea', False, ["Then Earth's civilization holds", 'power enough to sway the giants.']),
    (4, 'Euzeth', False, ['Indeed. That planet is a singularity', 'of sorts. It surely hides a power', 'we have yet to understand.']),
    (5, 'Euzeth', True, ['After all, ruins of the Protoculture', 'still exist there...']),
    (6, 'Euzeth', True, ['That vast cavern NERV calls the', 'GeoFront... it is the ruins of the', 'Protoculture, the previous civilization...']),
    (7, 'Euzeth', True, ['And the promised land written of in', 'the "Dead Sea Scrolls"... It must be', 'the true "Black Moon"...']),
    (8, 'Euzeth', True, ['Which is why I cannot let the', 'giants destroy that planet...']),
    (9, 'Laodicea', False, ['Peace between the Zentradi and', 'Earth proves they have found a', 'decisive weapon against the Meltrandi.']),
    (10, 'Laodicea', False, ['Then, when the battle ends, one side', 'or the other shall perish... but', "Earth's ruin must be avoided."]),
    (11, 'Laodicea', False, ['That planet is valuable to our fleet', 'as a key base in the future.']),
    (12, 'Euzeth', False, ['It is as you say, Judge...']),
    (13, 'Laodicea', False, ['And what of the', "Meltrandi's movements?"]),
    (14, 'Euzeth', False, ['They seem to be heading to Earth,', 'answering the moves of the', 'Zentradi and the Earthlings.']),
    (15, 'Laodicea', False, ['Hmm... Then it would be unwise', 'for our fleet to cut in there.']),
    (16, 'Euzeth', False, ['Yes... We watch how their battle', 'ends, then settle things with the victor.']),
    (17, 'Euzeth', False, ['Thus our fleet will win this', 'war without suffering any', 'significant losses.']),
    (18, 'Laodicea', False, ['But like planet Tron, which once', 'produced Tronium... the giants', 'may yet destroy the Earth.']),
    (19, 'Euzeth', True, ['.........']),
    (20, 'Euzeth', False, ['Judge, there is no need to worry.']),
    (21, 'Laodicea', False, ['Oh...? If you say so,', 'then it must be true.']),
    (22, 'Laodicea', False, ['Then our fleet will regroup around', 'the flagship Hermoz... and await the', 'chance to invade the Earth Sphere...']),
    (23, 'Euzeth', True, ['If the Earthlings are direct', 'descendants of the Protoculture, the', 'giants will not lay a hand on Earth.']),
    (24, 'Euzeth', True, ['They must be programmed to be wary', 'of planets inhabited by races', 'resembling the Protoculture.']),
    (25, 'Euzeth', True, ['And as proof, they have yet', 'to launch a direct attack', 'on Earth...']),
    (26, 'Euzeth', True, ['Heh, heh heh heh...', 'Everything is going', 'according to my plan...']),
]


# SNMSG: diálogo del mapa del prólogo (slots 2–30, lo primero que se ve en una partida nueva), formato A
MAP_LINES = [
    (2, 'Tashiro', False, ['Vice Captain! How many ships survived?!']),
    (3, 'Vice Captain', False, ['Only ours, sir...']),
    (4, 'Tashiro', False, ['And the machine weapon units?!']),
    (5, 'Ohta', False, ['...Almost completely wiped out.']),
    (6, 'Tashiro', False, ['Grr... Blast it!! Our fleet, built with', 'the very best of EOT, beaten', 'this badly...!!']),
    (7, 'Ohta', False, ['Captain, that enemy is neither the', 'Aerogaters nor the giant aliens.']),
    (8, 'Ohta', False, ['Most likely, the same kind that sank', 'the deep space explorer Luxion', 'seven years ago...']),
    (9, 'Tashiro', False, ['What...!']),
    (10, 'Vice Captain', False, ["Captain, they outnumber us too", 'greatly. We should withdraw.']),
    (11, 'Tashiro', False, ['No! If we do that, they will', "learn where Earth is!!"]),
    (12, 'Tashiro', False, ['We must stop them here,', 'no matter what!!']),
    (13, 'Kazumi', False, ['Noriko, Jung! Listen, if we', "don't stop them here, the", 'Earth Sphere will...!!']),
    (14, 'Jung', False, ["I know that without", 'being told! More importantly,', 'Noriko is...!']),
    (15, 'Kazumi', False, ["Noriko?! What's wrong?!"]),
    (16, 'Noriko', False, ['...O-Onee-sama... I-I...']),
    (17, 'Kazumi', False, ['Noriko?!']),
    (18, 'Noriko', False, ['F-Fighting an enemy like that...!']),
    (19, 'Kazumi', False, ['Noriko, pull yourself together!']),
    (20, 'Ohta', False, ['Takaya! Amano! What are you', "doing?! If you don't fight,", "you'll die too!!"]),
    (21, 'Ohta', False, ['Remember why you went through', 'all that harsh training!']),
    (22, 'Kazumi', False, ["That's right, Noriko! We can't", 'afford to be beaten here!']),
    (23, 'Noriko', False, ['C-Coach... Onee-sama...']),
    (24, 'Kazumi', False, ['If we lose here, Earth...', 'humanity will be in danger...!']),
    (25, 'Noriko', False, ['!!']),
    (26, 'Noriko', True, ['If we lose here... the people', 'of Earth... Kimiko and the others...!']),
    (27, 'Noriko', False, ["I-I understand, Onee-sama!", "I'll do what I can!"]),
    (28, 'Jung', False, ["Let's go, you two!!"]),
    (29, 'Tashiro', False, ['Open all gun ports! Target, the', 'enemy group dead ahead!!']),
    (30, 'Vice Captain', False, ['Roger, all guns ready to fire!']),
]


def fmt(variant, who, thought, rows):
    if variant == 'B':
        o, c = ('（', '）') if thought else ('「', '」')
        return who + o + '\n　'.join(rows) + c
    ind = '  ' if variant == 'A2' else ''
    rows = list(rows)
    if thought:
        rows[0], rows[-1] = '(' + rows[0], rows[-1] + ')'
    return who + ': ' + ('\n' + ind).join(rows)


def main_map(out):
    en = {n: fmt('A', *rest) for n, *rest in MAP_LINES}
    k = 0
    with open(os.path.join(WORK, 'dump', 'snmsg.jsonl'), encoding='utf-8') as src, \
            open(out, 'w', encoding='utf-8') as dst:
        for line in src:
            r = json.loads(line)
            if r['id'] in en:
                r['en'] = en[r['id']]
                k += 1
            dst.write(json.dumps(r, ensure_ascii=False) + '\n')
    print(f'mapa: {k} slots de SNMSG en inglés → {out}')


def ruler(n):
    """n dígitos = n × 8 px exactos (los dígitos no son proporcionales en la fuente VWF): se lee dónde corta."""
    return ''.join(str((i + 1) % 10) for i in range(n))


# ancho (#31): medir la caja de escena. L0–L4: 3 renglones de 26…40 dígitos (208…320 px); L5/L6: 4 y 5 renglones;
# L7: una sola línea larga sin saltos (¿el juego parte solo?); L8: palabras con espacio 0xA0 hasta ~300 px.
STRESS = {k: '\n'.join(ruler(26 + 3 * k + j) for j in range(3)) for k in range(5)}
STRESS.update({
    5: 'Row one\nRow two\nRow three\nRow four',
    6: 'Row one\nRow two\nRow three\nRow four\nRow five',
    7: 'One long line without breaks to see whether the engine wraps it by itself or runs past the edge',
    8: 'Speaker: words spaced with 0xA0 up to three hundred px wide ok\nSecond row',
})


def main():
    variant, out = sys.argv[1], sys.argv[2]
    if variant == 'mapa':
        return main_map(out)
    if variant == 'ancho':
        en = dict(STRESS)
    else:
        en = {n: fmt(variant.rstrip('N') or 'A', *rest) for n, *rest in LINES}
    if variant == 'N':   # $n como hablante y dentro de la frase (el juego pone el nombre del protagonista)
        en[1] = '$n: Yes...'
        en[12] = "Euzeth: It is as you say, Judge...\nUnlike $n's friends, we can wait."
    k = 0
    with open(os.path.join(WORK, 'dump', 'script.jsonl'), encoding='utf-8') as src, \
            open(out, 'w', encoding='utf-8') as dst:
        for line in src:
            r = json.loads(line)
            if r['script'] == 234 and r['line'] in en:
                r['en'] = en[r['line']]
                k += 1
            dst.write(json.dumps(r, ensure_ascii=False) + '\n')
    print(f'{variant}: {k} líneas en inglés → {out}')


if __name__ == '__main__':
    main()
