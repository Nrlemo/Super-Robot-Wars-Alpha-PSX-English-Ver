# Glosario canónico JP→EN — Paso 2 (v1, 2026-09-27)

Archivo: `work/glossary/glossary.csv` (910 términos). Se regenera con:

```bash
cd work && source tools/env.sh
"$SRW_PY" tools/src/glossary_build.py          # --html vuelve a convertir info/*.html
```

## Columnas
| Columna | Qué es |
|---|---|
| `category` | `pilot`, `unit`, `spirit`, `pilot_skill`, `unit_ability`, `part`, `ui` |
| `series` | Serie de origen (36 series, según Akurasu) |
| `jp` | Término japonés tal como lo da la fuente |
| `en_final` | **Nombre a usar en la traducción** |
| `status` | `official` (localización oficial en inglés) · `source` (fuente fan: Akurasu / GameFAQs) · `proposed` (propuesta propia, **revisar**) · `manual` (decisión tomada a mano: nunca se pisa al regenerar) |
| `en_source` / `source` | Qué dice la fuente fan y cuál es |
| `en_official` | Todas las variantes oficiales encontradas, con la entrega entre corchetes |
| `in_pilot_bin` / `jp_game` | `yes` = el nombre está igual en `PILOT.BIN`; `similar` = el juego lo escribe distinto (`jp_game`) |
| `snmsg_hits` | Apariciones del término en los diálogos de mapa (orientativo: los kanji comunes cuentan de más) |

Para fijar una decisión: poner `status = manual` y el valor en `en_final`. El script la respeta.

## Fuentes y prioridad
1. **Localización oficial**, en este orden: **OGs** (Atlus; `CLAUDE.md` §6 pide la terminología OG) → T → 30 → V → X. Páginas de Akurasu descargadas en `glossary/web/` y extraídas a `web/official_terms.json`.
2. **Akurasu (SRW Alpha)**: Character List, Unit List, Spirit, Pilot/Unit Ability, OP Parts (`info/`).
3. **GameFAQs Move List (Chiche)**: términos de interfaz; sus variantes quedan en `notes` como `alt`.
4. **`glossary/manual.csv`**: lo que ninguna fuente trae (45 pilotos genéricos/secundarios de `PILOT.BIN`).

## Cobertura
| Categoría | official | source | proposed |
|---|---:|---:|---:|
| pilot | — | 362 | 45 |
| unit | — | 365 | — |
| spirit | 27 | — | 8 |
| pilot_skill | 5 | 13 | — |
| unit_ability | 1 | 30 | 1 |
| part | 16 | 11 | — |
| ui | — | — | 26 |

- **Los 469 pilotos de `PILOT.BIN` tienen entrada.** 339 coinciden exactos; el resto por similitud o alias (`ブリタイ7018`, `サスガ・ミオ`…).
- `PILOT.BIN`: nombres en **katakana de medio ancho**, campo de hasta **20 bytes** (registro de 0x70 bytes, nombre en +4). Hoy **13 nombres** superan los 20 bytes (Quatre Raberba Winner, Great General of Darkness, Raidiese F. Branstein, Laodicea Judecca Gozzo, los genéricos "… Cyber Soldier"…): habrá que abreviarlos en ese campo, salvo que el Paso 3 muestre que se puede ampliar.

## Decisiones tomadas (2026-09-27) — `glossary/decisiones.csv`, status `manual`
| Tema | Decisión |
|---|---|
| Terminología de espíritus | **SRW OG**: 加速 **Accel** (OG1/OG2 de Atlus; OGs usa Accelerate), 幸運 **Luck**, 期待 **Hope** |
| 気力 | **Will** (no Morale) |
| 激闘 | **Fury** |
| ムッターマ・ズガン | **Mutterma Sugan** (grafía oficial) |
| 帝国監察軍兵 | **Aerogater Soldier** |
| 親衛隊兵 | **Imperial Guard** |
| 人工知能改 | **A.I. Kai** |

Además: `proposed_review.csv` (revisión de todos los términos propuestos, con fuentes) se aplica como propuesta
(status `proposed`), y `weapons_en.csv` da nombre a las **686 armas** (224 oficiales, 435 del fandom, 27 propuestas).
Pendientes menores de la revisión: ver `notes/glosario_revision.md`.

Desde 2026-09-28 `glossary_build.py` también lee `units_en.csv` (486 unidades del juego; agrega las que no estaban en la
wiki) y `weapons_review.csv` (prioridad sobre `weapons_en.csv`). Columna nueva `en_short`: forma corta para campos fijos.

## Qué falta
- ~~Nombres de armas~~: hechos (`weapons_en.csv`); revisar las 27 propuestas y los nombres largos (`en_bytes`) contra el campo de largo fijo.
- 45 pilotos con `proposed`; 7 marcados `DUDOSO` en `manual.csv`.
