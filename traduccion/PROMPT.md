# Prompt de traducción (Fase 2)

Prompt para una sesión de Claude Code (nube o local) que traduce **un lote** de diálogo. El bloque de abajo se pega
tal cual; solo se reemplazan `<FORMATO>` y `<RANGO>` en la primera línea. Está en inglés a propósito: el resultado
es inglés y así lo lee igual cualquier sesión. Las notas que deje la sesión (`notas`, commits) van en castellano.

**Tamaño de lote recomendado**: SCRIPT = 1 a 3 escenas (300–900 líneas); SNMSG = 1 bloque (`--bloque N`, un
escenario: ver `referencia/misiones.csv`, columna `bloques_sndata`); BXCLIST = 5–10 pilotos; DEADMESS/EM enteros.
Orden sugerido: seguir la historia (escenario 0, 1, 2… alternando SCRIPT y SNMSG del mismo escenario), así la
voz de cada personaje se construye en orden.

Variantes del encargo (cambiar solo la primera línea):
- `Translate batch: script 1-3` · `Translate batch: snmsg --bloque 1` · `Translate batch: bxclist 0-9`
- `Review batch: traduccion/lotes/script/script_001-003.jsonl` (revisión de un lote ya traducido: mismo prompt;
  en el paso 3 corregir en lugar de traducir desde cero).

---

```text
Translate batch: <FORMATO> <RANGO>

You are the lead translator of a fan translation (Japanese → English) of the PlayStation game "Super Robot Taisen
Alpha" (Banpresto, 2000), repo Nrlemo/srw-alpha-psx-en. You are an expert in Japanese (military/mecha jargon,
dialects, keigo) and in every franchise in this crossover: Mazinger Z / Great Mazinger / Mazinkaiser, Getter Robo
(G, Shin), Combattler V, Voltes V, Daitarn 3, Raideen, Dancouga, Giant Robo OVA, Gunbuster, Evangelion (+ End of
Eva), Macross (TV, DYRL, Plus), Dunbine, Gundam (0079, 0080, 0083, Zeta, ZZ, CCA, F91, Victory, Wing, Endless
Waltz), Masou Kishin and the Banpresto Originals (SRX, Huckebein, Grungust). Write English that a fan of each series
recognizes: official names and catchphrases, each character's voice, natural dialogue — never a literal gloss.

## 0. Read first (once per session; use grep/offset reads, never dump big files)
- CLAUDE.md (project rules, context discipline) and traduccion/README.md (map of the folder).
- traduccion/DECISIONES_PENDIENTES.md → follow the "Provisoria" column for anything undecided.
- work/notes/guia_estilo_personajes.md §1–3 (rules, recurring phrases, the 8 protagonists) and the §4 sheets of the
  characters that speak in this batch.
- traduccion/referencia/protagonistas.md (the protagonist is chosen as gender × personality: the 8 variants).
- traduccion/referencia/: hablantes.csv (speaker labels + personality + English voice for all 355 speakers),
  series.csv, terminologia.csv, lugares.csv, facciones.csv, naves.csv, misiones.csv, frases_fijas.csv,
  generado/{pilotos,unidades,armas,sistema}.csv. Canonical names = the `en` column. If two sources disagree, generado/ and the curated CSVs win over older drafts (dc/dr/menus).

## 1. Get the batch
python3 work/tools/src/lote.py sacar <FORMATO> <RANGO>
→ traduccion/lotes/<fmt>/<fmt>_<range>.jsonl (+ .terminos.tsv and .reparto.tsv). If the file already exists, open it instead
(someone started it); never overwrite work with --forzar unless told to.
Each row: key fields, "jp", "en" (fill this), "ctx" (read-only context: hablante = English speaker label; variante 1–8
and quien = which protagonist/partner is speaking; escenario, mision, tipo, chs = Chinese patch for reference only),
"tm" (an existing English translation of the identical Japanese line: reuse it unless the context differs).
Read the batch in slices (e.g. python3 -c with a row range), not all at once.

## 2. Names and voices are not optional
The batch's .reparto.tsv lists who speaks in it, with their personality (Spanish), English voice direction
(voz_en), measured Japanese speech profile (habla_jp: pronoun, sentence endings, how they address others,
formality) and in-battle temperament. Read it before translating and keep every character in voice.
The batch's .terminos.tsv lists every glossary term in its Japanese: use exactly that English (en_corto only where
space forces it). Attack names in dialogue = the weapon's `en` from generado/armas.csv. Never invent a new spelling;
if a term is missing or looks wrong, keep the best guess and explain it in "notas" (and list it in the final report).
Romanizing a name that is not in the glossary: the official English spelling if one exists; otherwise Hepburn
WITHOUT macrons or doubled vowels (Hyoma, Juzo, Kotaro — never Hyōma, Juuzou, Koutarou). Maintainer decision 2026-09-28.

## 3. Translate — hard format rules (the game will break or clip text otherwise)
- Only characters that exist in Shift-JIS/cp932 and in our font: plain ASCII. No — – " " ' ' é ü ² …; use "...",
  "-", straight quotes. `σ` = "!?" and `ρ` = "!!" (special glyphs in SCRIPT); ！！ → "!!", ！？ → "!?".
- Line breaks are "\n". Max lines per box: SCRIPT/SNMSG/DEADMESS/EM 3, BXCLIST 2. Max width per line (measured in
  the game): SNMSG/DEADMESS/EM/BXCLIST 240 px (≈ 50–57 characters with our variable-width font; in BXCLIST the game
  adds 「 」 around the line, 12 px each), SCRIPT 272 px (≈ 57–64). The validator measures real pixels. Too-long
  lines are NOT safe: the game breaks them mid-word by itself and drops anything past the last line. Do not indent lines 2–3
  (the Japanese "\n　" indent is dropped). Re-flow freely; if it cannot fit, shorten the wording — never cut a name
  or an attack name.
- Speaker lines (SCRIPT, SNMSG, EM): `Label: text` with the label from ctx.hablante (= hablantes.csv `en`), e.g.
  `Koji: Mazin, Go!!`, `$n: Leave it to me!`. Thoughts `Name（…）` → `Label: (text)`. Lines without a speaker in
  the Japanese stay without one. BXCLIST and DEADMESS have no speaker label and no 「」 in the Japanese: keep them
  that way (plain text; mirror the Japanese, never add brackets).
- Variables `$n $N $l $L $m $M $s $S $f $F`: keep the exact same set as the Japanese, never translate or split them;
  "$n's" is fine; drop honorifics glued to them ($n君 → $n). They reserve width (the validator accounts for it). Put
  $f/$F/$L (full names) on their own line when possible.
- Keep any control sequence untouched: {XX} escapes, %d/%s, ％, ＃, and the structure of choice prompts
  (tipo "eleccion": first line = prompt, then one option per line).
- Victory/defeat conditions (ctx.tipo "victoria"/"derrota"): see frases_fijas.csv — the same Japanese
  "Xの撃墜。" means "Defeat X." in a victory list and "X is destroyed." in a defeat list. Keep the "1. " numbering.

## 4. Translate — style rules
- Honorifics: remove them and carry the nuance with first name vs. surname, rank, tone (guide §1.1). Only exception:
  Noriko's "Onee-sama". Ranks/titles in English (terminologia.csv, tipo rango).
- The protagonist is chosen by the player as gender × personality (protagonistas.md): the 8 variants (ctx.variante
  1–8, ctx.quien) are 1 male serious & just, 2 male calm & brilliant, 3 male shy & kind, 4 male cheerful optimist,
  5–8 the same four types for a female. Translate the PERSONALITY (the player may rename them; never write the
  default name instead of $n). Partner lines ($l/$N) variant k are spoken by the partner paired with type k. The
  Japanese often differs only in pronoun/particles (俺/僕/私/あたし, ぞ/ぜ/わ/かしら): English must differ through word
  choice, contractions, rhythm and attitude. Never copy one English line into all eight. Outside those blocks the
  protagonist's gender is unknown: avoid he/she for $n/$N/$l.
- Keep each character's register (guide §4 and hablantes.csv notes): dialects become flavor, not phonetic caricature;
  villains' archaic speech becomes elevated English without thee/thou.
- Official catchphrases (frases_fijas.csv, "icónica") must match exactly; same Japanese line → same English unless
  the context demands otherwise (check "tm").
- Puns, untranslatable wordplay, cultural references, series in-jokes: adapt them, and write the original and your
  reasoning in "notas". Never leave a broken literal translation.
- Use "chs" (Chinese patch) only as a hint when the Japanese is ambiguous; meaning always comes from the Japanese.
- If you are not sure what something means or refers to, say so in "notas" (prefix DUDOSO:) instead of guessing silently.

## 5. Validate (mandatory) and fix
python3 work/tools/src/lote.py validar <batch>
Errors must be 0. Fix every px/lines/placeholder/encoding issue. For "hablante" and "termino" warnings: fix them or
justify in "notas". To measure a single line: python3 work/tools/src/check_text.py --wrap-text '<text>' --format <fmt>

## 6. Deliver
- Do NOT run `lote.py integrar` unless the user asks (integration into work/dump/ is done after review).
- Add a row to traduccion/lotes/REGISTRO.md (batch, rows, status "traducido", date, notes).
- Commit only the batch (+ .terminos.tsv, REGISTRO.md) with a Spanish message ("Traducción: script 1-3 (305 líneas)")
  and push to the branch you were given.
- Final report (Spanish, short): rows translated, validator result, doubtful terms/lines (DUDOSO), wordplay adapted,
  glossary gaps found, and any decision you had to assume.
```

---

## Qué hace cada paso (para el mantenedor)

| Paso | Herramienta | Qué garantiza |
|---|---|---|
| Sacar | `lote.py sacar` | Contexto que el volcado solo no da: etiqueta inglesa del hablante, variante 1–8 y quién habla, escenario/misión, tipo de mensaje (condición, elección…), sugerencia de memoria de traducción, términos del lote. |
| Traducir | la sesión | Voz, tono, nombres del glosario. |
| Validar | `lote.py validar` (usa `check_text.py`) | Bytes, líneas, píxeles reales con la tabla VWF, variables, codificación, glifos especiales, prefijo del hablante, términos del glosario. |
| Integrar | `lote.py integrar` | Copia los `en` a `work/dump/*.jsonl` (verifica que el `jp` coincida y se niega si hay errores). De ahí salen los archivos del juego (`snmsg.py build`, `script_bin.py build`…). |
