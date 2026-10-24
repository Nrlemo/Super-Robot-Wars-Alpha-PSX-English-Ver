# Borrador en inglés de menús (overlays) — 2026-09-28 (rev. 2: decisiones 1–3)

Encargo `cloud_tasks/04_menus_borrador.md`. Traducción al inglés de los textos de interfaz de los overlays
**IMIS, PRM, SNMP, BTL, SNDU, TITL, COMM y ENTR**, con presupuesto de bytes. **No está insertado en la ISO**: es el
texto que va a usar `ovl_patch.py` (o el reempaquetado de PRM/SNMP/TITL) cuando se integre.

## Archivos
| Archivo | Qué es |
|---|---|
| `work/translation/menus_map.txt` | **Fuente editable**: una línea por texto japonés único → `jp \|\| en \|\| en_short \|\| notas`. Acá se corrige la traducción. |
| `work/tools/src/menus_draft.py` | Cruza el mapa con `dump/ovl_strings.jsonl`, mide bytes (cp932) y escribe el JSONL. Valida especificadores de formato. |
| `work/translation/menus_en.jsonl` | **Salida**: una fila por string del volcado (`file, addr, jp, en, en_short, room, fits, fits_short, refs, plan, notes`). |

```bash
# Regenerar el JSONL después de editar el mapa (--report lista lo que no entra)
cd work && python3 tools/src/menus_draft.py --report
```

### Semántica de las columnas
- `fits`: `len(en) + 1 (NUL) <= room`, con el largo **en bytes** (ASCII = 1 byte; `　`, `「」`, `％` = 2).
- `en_short`: solo aparece cuando `en` no entra. `fits_short` dice si la forma corta entra **en ese lugar** (el mismo texto
  puede tener lugares distintos en cada overlay).
- `refs`: copiado del volcado (`ptr@` = palabra de 32 bits; `code@` = par `lui/addiu`).
- `plan` — **criterio decidido (2026-09-28): primero reubicar con el texto completo; acortar solo si no se puede.**

| `plan` | Cuándo | Qué se inserta |
|---|---|---|
| `in situ` | `en` entra en su lugar | `en` |
| `reubicar` | no entra y hay puntero (`ptr`) | `en`, movido; se corrige la palabra. En PRM/SNMP/TITL (zonas llenas) = reempaquetar el bloque |
| `reubicar (código)` | solo referencias `lui/addiu` | `en`, cuando `ovl_patch.py` sepa reubicar referencias por código (**pendiente técnico**). Mientras tanto, `en_short` |
| `corta` | sin referencia directa: no se puede mover | `en_short` in situ |
| `sin solución` | sin referencia y ni la forma corta entra | — (hoy: 0) |

- `notes`: contexto, fragmentos, dudas y avisos automáticos ("dirección corregida").

## Resultado
| Overlay | Filas | in situ | reubicar | reubicar (código) | corta |
|---|---:|---:|---:|---:|---:|
| IMIS | 398 | 241 | 133 | 21 | 3 |
| PRM | 423 | 240 | 155 | 8 | 20 |
| SNMP | 88 | 61 | 27 | 0 | 0 |
| BTL | 16 | 14 | 0 | 0 | 2 |
| SNDU | 11 | 8 | 0 | 1 | 2 |
| TITL | 198 | 95 | 100 | 3 | 0 |
| COMM | 17 | 14 | 0 | 3 | 0 |
| ENTR | 101 | 85 | 11 | 5 | 0 |
| **Total** | **1.252** (889 únicos) | **758** | **426** | **41** | **27** |

- **Menú de intermisión** (IMIS+0x7F40…, tabla de punteros): `Unit Upgrade`, `Weapon Upgrade`, `Pilot Stats`, `PocketStation`
  van **completos reubicados** (IMIS tiene ~21 KB libres en su zona). Los mismos rótulos usados como **encabezado de
  pantalla** (IMIS+0x644C, +0x6458) se referencian por código: completos cuando se implemente la reubicación `lui/addiu`.
  Falta confirmar en pantalla que el ancho de la columna del menú admite el texto largo.
- `corta` (27 filas): tablas sin puntero (efectos de partes en PRM, fondos, nombres de BTL, `地中`). Ahí se usa `en_short`
  salvo que se encuentre la rutina que las indexa y se pueda cambiar.
- Los 3 "Haro" (lugar de 3 bytes) quedan como `reubicar`.

## Qué quedó afuera (a propósito)
| Qué | Cuántos | Por qué |
|---|---:|---|
| Ruido de código que parece SJIS (`ﾂD湖P`, `ｳｯ!丐`…) | ~6.700 (de 8.198 candidatos) | No es texto. Filtro: caracteres que no aparecen en el texto real del juego + patrones típicos de instrucciones. |
| Pares kana+`ﾟ` (`ｶﾟｷﾟ`, `ﾆﾟﾇﾟ`, `ｱﾞｲﾞ`, `ﾒﾟﾓﾟ`, `ｵﾟ 0`, `%d~ﾄﾟﾅﾟ`) | ~20 (con repeticiones) | **Glifos especiales** (íconos/abreviaturas dibujadas), no texto: no tocar. |
| Letras de canciones en TITL (`0x800FF36E`–`0x80101BDA`) | 190 | Letras de los temas de las series (algunas con puntero): probablemente la pantalla de BGM. Son letras con copyright y no son UI: **decisión pendiente** (dejar en japonés, romaji u ocultar). |
| `魂`, `愛` (espíritus de 1 carácter) | 2 | El inventario pide ≥ 2 caracteres, así que no están en el volcado. Están en la tabla de punteros de espíritus (PRM+0x267CC): agregarlos a mano (Soul / Love). |
| `x使わないで`, `ｱ術`, `ﾈﾚ` | 3 | Ruido o marcadores de desarrollo sin uso. |

**Direcciones corregidas** (`MISALIGNED` en el script): el volcado leyó mal el inicio de 4 strings porque el byte
anterior formó un par SJIS. Se derivó la dirección real: `熱血` (PRM 0x800A8E48), `ｲﾝﾀｰﾐｯｼｮﾝ` (IMIS 0x800D7F34),
`壮絶！台湾大地震ｽﾍﾟｼｬﾙ！` (IMIS 0x800D68C8), `A型` (ENTR 0x80114D98). **Verificar en hex** antes de insertar.

## Convenciones
| Tema | Criterio |
|---|---|
| Fuente de verdad | `glossary.csv` → `en_final`; `decisiones.csv` manda: **Will, Accel, Luck, Hope, Fury** (OG). |
| Estilo de rótulos | Vocabulario de SRW OG/T/30: Unit Stats, Pilot Stats, Weapon Stats, Upgrade, Parts, Re-Equip, Sortie, Objectives, Spirit Commands, End Turn, Counter/Defend/Evade. |
| Estadísticas de piloto | Melee, Ranged, **Reaction** (反応, stat propio de Alpha), Skill, Evade, **Hit** (glosario). |
| Estadísticas de unidad | Mobility, Armor, Limit (限界/限界反応), Move, Type, Size, Repair Cost, Abilities, Terrain. |
| Rangos de terreno | `Air/Land/Sea/Space Rank`; en descripciones "terrain rank". |
| Mayúsculas | *Title Case* en rótulos y títulos; oración normal en mensajes. Memory Card y PocketStation con mayúscula (nombres de producto). |
| Mensajes de 2 líneas | Se tradujo cada línea por separado para que la frase inglesa se reparta igual (marcado "línea 1 de 2"). |
| Formato | `%d %2d %3d %s %c` idénticos en `jp`/`en`/`en_short` (el script lo valida). `%3d％` queda igual: el `％` de ancho completo evita que un `sprintf` lo lea como formato. |
| Fechas | `%d月%d日` → `%d/%d` (mes/día, orden EE.UU.); meses `Jan…Dec` (forma corta numérica donde hay 3 bytes). |
| Comillas de batalla | `「%s」` sin cambio, igual que en BXCLIST (ver `fuente_en.md`). |
| Huecos de ícono | Los `　` (ancho completo) y espacios iniciales que reservan lugar para el ícono de un botón se conservan. |
| Haro | Habla en katakana → mayúsculas en inglés ("CAN EQUIP! WHAT NOW?"). |
| Títulos de escenario | Traducción propia, idiomática. Se respetan títulos oficiales cuando el escenario reutiliza el de un episodio/película (Zeta "Black Gundam", Wing "The Shooting Star She Saw", EVA "Angel Attack", "Death and Rebirth", "Air", Macross "Booby Trap"…"Bye-Bye Mars", "Do You Remember Love?", película "Mazinger Z vs. the Great General of Darkness"). Zeon (no Jion). |
| Fondos de batalla y registro de daño (PRM, `背景:%s`, `基本ダメージ/%d`) | Parecen de una **pantalla de depuración**; se tradujeron igual, en estilo telegráfico. |

## Decisiones tomadas (2026-09-28)
| # | Tema | Decisión |
|---|---|---|
| 1 | Rótulos que no entran (intermisión y resto) | **Primero reubicar con el texto completo; acortar solo si no es posible** → columna `plan`. |
| 2 | 必要気力 | `Will` (confirmado). |
| 3 | Contradicciones del glosario | **Lynn Minmay** (parte → `Minmay Doll`), **Sword Cut** (no Sword Sweep), **Telekinesis Field** (no TK Field). Cargadas en `glossary/decisiones.csv` y en `glossary.csv` como `manual`. |

## Pendientes
- [x] **P4 — Fragmentos de descripciones** (issue #9) ✅ 2026-09-29. El "byte que corta" es **`0x0A`** (salto de línea): las
  líneas 1..n-1 de una descripción terminan en `0x0A` y solo la última en NUL; `ovl_strings.py` (regex que exige NUL al final
  y no admitía `0x0A`) solo capturaba la última. Ahora admite `0x0A` dentro del string: 497 filas multilínea completas (con
  su puntero), 374 direcciones de fragmento desaparecen. `menus_map.txt` acepta `\n` (escape) en jp/en/short; 52 descripciones
  completas traducidas (PRM 41, ENTR 8, IMIS 3) y 18 con forma corta in situ como plan B (PRM es zona llena). Falta probar
  el ancho de renglón en el juego (`tools/menus_test.sh`).
- [ ] **P5 — Íconos de botón con VWF** (issue #10). `方向キー左右でキャラクターを選択、　ボタンで決定。`, `　入力 　　削除 　　空白 　　もどる`
  (teclado de nombre) y `  ボタンで全員の命令を一斉変更`: los `　`/espacios son huecos para el ícono. Si el ícono se dibuja
  en una x fija, el inglés (ancho variable) lo va a pisar o dejar lejos. Probar en pantalla.
- [x] Reubicación de referencias por código (`lui/addiu`) en `ovl_patch.py` (41 filas `reubicar (código)`): hecha
  2026-09-28 (e1c32de, `menus.md`); quedan las tablas por índice (issue #7).
- [x] Agregar `魂` / `愛` a mano y verificar en hex las 4 direcciones corregidas: hecho 2026-09-28 (strings de un
  carácter en `ovl_strings.py`; issue #8 cerrado).

## Contradicciones del glosario que quedan abiertas
Revisé el glosario completo (mismo japonés con distinto `en_final`, y variantes de un mismo término). Además de las 3
decididas, quedan estas:

| Término | Variantes | Usado en el borrador |
|---|---|---|
| ~~ピンポイントバリア~~ | ✅ 2026-09-28 (#40): **`Pinpoint Barrier`** en parte y habilidad | `Pinpoint Barrier` |
| ~~Iフィールド~~ | ✅ 2026-09-28 (#40): **`I-Field`** (oficial de Gundam) en todo | `I-Field` |
| HP/EN回復 | `HP Regen (small)` / `HP Recovery` / `EN Recovery` (los dos tamaños iguales) | `HP Regen (S)/(L)`, `EN Regen (S)/(L)` |
| ~~シャーキン~~ | ✅ 2026-09-28 (#40): **`Prince Sharkin`** / `Giant Sharkin` | `Sharkin` |
| 渚カヲル | piloto `Kaworu Nagisa` / unidad `Nagisa Kaworu` | — (no aparece en menús) |
| ~~龍王機 / 虎王機~~ | ✅ ya unificado en el glosario: `RyuOhKi` / `KoOhKi` (y `RyuKoOh` / `KoRyuOh`; DR 001 corregido 2026-09-28) | — |
| 宇宙怪獣… (5 tipos) | piloto en inglés (`Space Monster Troop`…) / unidad en romaji (`Uchuu Kaijuu Heitai`…); uno sin traducir | — |

## Otras dudas (menores)
1. **恋人** → `Partner` (neutro). Alternativa fan: `Lover`.
2. **Tipos de movimiento** con 7 bytes: `水中` → `Underwater`/`Sea`, `地中` → `Underground`/`Dig`, `水上` → `On Water`/`Water`.
   `地中` aparece en tablas sin puntero (plan `corta`).
3. **Contexto no confirmado**: `防御攻撃` (`Defend+Attack`), `回復` (`Recover`), `ファラ` (¿Fuala Griffon?), `副長`
   (`Vice Captain`/`XO`), `宇宙ローズ`, `雷王星＋てんこもり宇宙`.
4. **Juegos de palabras**: `最後のシ者` (シ = 使 "mensajero" / 死 "muerte", ep. 24 de EVA) → `The Final Messenger` pierde el
   doble sentido. `イナーシャル喜屋武セラー` es una errata del original → `Inertial Canceller`.
5. `壮絶！台湾大地震ｽﾍﾟｼｬﾙ！` (terremoto de Taiwán, 1999) en la lista de títulos: verificar si se ve alguna vez.
6. Teclado de ingreso de nombre (`ひらがな/ｶﾀｶﾅ/漢字/英数`): traducido literal; para inglés hay que rediseñarlo
   (pendiente técnico #8 de `README.md` (estado) §8).

## Siguiente paso sugerido
- Pasar `menus_en.jsonl` a la entrada de `ovl_patch.py` (hoy usa `{'file', 'texts'}`) y probar IMIS completo en el juego.
- Para PRM/SNMP/TITL (zonas llenas): reempaquetado del bloque de strings usando `en` (no `en_short`).
