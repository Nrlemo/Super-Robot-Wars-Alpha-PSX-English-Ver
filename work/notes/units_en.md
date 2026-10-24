# Nombres de unidades en inglés — `glossary/units_en.csv` (2026-09-27)

Encargo en la nube 01 (`cloud_tasks/01_unidades_en.md`). Una fila por registro de `dump/robot.jsonl`
(**486 filas**, `robot_id` 0..485), con el nombre inglés que va al campo del juego (máx. **21 bytes + NUL**).

## Columnas

| Columna | Contenido |
|---|---|
| `robot_id` | índice del registro en ROBOT.RAF (= `id` de `robot.jsonl`) |
| `jp_game` | nombre tal cual en el juego (kana de medio ancho, pares ﾞ/ﾟ incluidos) |
| `jp_norm` | normalizado: NFKC a ancho completo, `-` detrás de katakana → `ー`, `･` → `・`, pares especiales → su glifo (`ﾔﾟﾕﾟ`→`Mk-`, `ﾚﾟ`→Ⅱ, `ﾛﾟ`→Ⅲ, `ﾖﾟ`→Ⅴ, `ﾘﾟ`→β, `ﾙﾟ`→ν, `ﾝﾟ`→α, `ﾏﾟ`→ヱ) |
| `en` | nombre inglés completo (canónico, para diálogos/glosario) |
| `en_short` | solo si `en` pasa de 21 bytes: forma que entra en el campo |
| `en_bytes` | bytes ASCII de lo que se escribe en el juego (`en_short` si existe, si no `en`); máximo 21 en las 486 filas |
| `franchise` | serie, con los mismos nombres que `glossary.csv` (+ *Macross Plus*, que no tenía filas) |
| `status` | `official` / `fan-standard` / `proposed` |
| `source` | ver abajo |
| `notes` | observaciones + `glossary: <jp> = <en_final>` con las filas de `glossary.csv` cruzadas |

## Conteos

| | Filas (486) | Nombres distintos (413) |
|---|---|---|
| official | 344 | 277 |
| fan-standard | 120 | 116 |
| proposed | 22 | 20 |

- **Formas cortas**: 25 filas (23 nombres distintos) necesitan `en_short`.
- **Cruce con `glossary.csv`**: las **365 filas `unit` quedan todas asignadas** al menos a un registro.
  21 registros no tienen fila en el glosario: Z II / Z II (MA), Daifighter, Daitank, SRX, R-1, R-Wing, R-2, R-3,
  YF-19/YF-21 (6 modos), GR2, Top Rim, Bottom Rim.
- **Nombres repetidos** en el juego (mismo texto, registros distintos: variantes por piloto, por escenario o por
  modo): 55 nombres cubren 128 registros. Se traducen igual porque el texto japonés es igual; la nota dice
  "N registros" y, cuando el glosario distingue la variante (Titans/AEUG, Quattro, Tod, Rezin…), el cruce la lista.

### Fuentes (`source`)
| Código | Qué es | Filas |
|---|---|---|
| `Gundam-EN` | grafías oficiales de Sunrise/Bandai (gundam-official, kits, Gundam Wiki) | 174 |
| `akurasu` | Unit List de Akurasu (SRW Alpha); se mantiene donde no hay grafía oficial conocida | 111 |
| `Macross-EN` | terminología oficial de Macross (Fighter/GERWALK/Battroid, naves Zentradi) | 68 |
| `akurasu:OGs Mech Database` | grafía confirmada en las páginas OGs de Akurasu (`info/Super Robot Wars_OGs_*`) | 24 |
| `SRW-OG-EN` | criterio OG sin confirmación directa en esas páginas (Aerogater, R-Wing, R-GUN Powered, "Mass-Produced"…) | 19 |
| `SRW-EN` | SRW en inglés (T/30/V/X) para Mazinger y Combattler | 25 |
| `Eva-EN` | Evangelion en inglés (Unit-0x, nombres de Ángeles) | 22 |
| `Discotek-EN`, `VoltesV-EN`, `Sunrise-EN`, `MediaBlasters-EN` | lanzamientos occidentales de cada serie | 29 |
| `romanization`, `literal`, `fandom` | propuesta propia (Hepburn / traducción literal / uso fan) | 14 |

**Aviso de honestidad**: esta sesión en la nube **no tuvo acceso web** (el proxy devolvió 403 para Gundam Wiki y
Akurasu). Las grafías `official` salen del conocimiento de las localizaciones oficiales, no de una consulta hecha
hoy. Las que no tengo seguras están en `fan-standard`/`proposed` y con `DUDA` en `notes`. Conviene una pasada de
verificación con red antes de congelar la tabla.

## Convenciones

1. **Glifos especiales → ASCII** (no se usan los pares ﾞ/ﾟ en inglés): Gundam Mk-II, Nu Gundam, Zaku III,
   Z II, Voltes V, Alpha Azieru, Gushios Beta III, Exelion. Ningún `en`/`en_short` contiene 0xDE/0xDF ni bytes
   fuera de ASCII (verificado por script).
2. **Lo oficial gana sobre Akurasu** (CLAUDE.md §6). Cambios respecto de `en_final` del glosario, entre otros:
   Zaku II Kai, Char's Zaku II, Gundam NT-1 Alex, Gelgoog Jager / Gelgoog Marine, Gundam GP03S Stamen, Byarlant,
   Bound Doc, The O, Jupitris, Hamma-Hamma, Quin Mantha, Gaza-D, Zaku III Custom, Gundam F90 V-Type,
   Boazanian Saucer, Skull Rook, Guardian God Gordol, Evangelion Unit-0x, Kaworu Nagisa (orden occidental),
   Nupetiet-Vergnitz, SDF-1 Macross.
3. **Se traduce el nombre que muestra el juego**, no el del wiki: si el juego omite el prefijo (戦闘獣オベリウス → ｵﾍﾞﾘｳｽ,
   ザンジバル級 → ｻﾞﾝｼﾞﾊﾞﾙ, 飛行要塞グール → ｸﾞ-ﾙ) el inglés también lo omite (Oberius, Zanzibar, Ghoul).
4. **Modos**: `(MA)` se conserva tal cual (Methuss (MA), Gaza-D (MA)…); バード形態 → "Bird Mode",
   飛行形態 → "Flight Mode"; los sufijos N/H/A de Dancouga y F/G/B de la VF-1J de TV se dejan como letra.
5. **Macross**: Fighter / GERWALK / Battroid (oficial). `(S)` = pack Super (VF-1A, VF-1J) o Strike (VF-1S),
   según el glosario ("Super Valkyrie" de Max/Milia/Hikaru, "Strike Valkyrie" de Focker/Hikaru).
6. **量産型** → "Mass-Produced" (convención OG: *Mass-Produced Huckebein Mk-II*, *MP Huckebein Mk-II*); forma corta "MP …".
   Excepción: EVA量産機 queda "Mass Production Evangelion" (nombre oficial de la franquicia).
7. **Formas cortas**: se quita primero "Gundam" en los Gundam W (Deathscythe Hell, Sandrock Custom, Wing Zero
   Custom), luego se abrevia "Mass-Produced" → "MP" y "Full Armor" → "FA", y se sacan los paréntesis.
8. Typos de Akurasu corregidos: Kaiser *Plider* → Pilder, *Grunguest* → Grungust Kai, *Habbakuk* → Habakkuk,
   *Pikadron* → Pikudron (el juego dice ﾋﾟｸﾄﾞﾛﾝ), *Gazelle* → Giselle (ジゼル).

## Criterio OG (actualización 2026-09-27)

Decisión del mantenedor: **seguir las traducciones de SRW OG**. Fuente: las páginas OGs de Akurasu agregadas en `info/`
(commit "SRW OG mech database": Mech Database Real/Personal Trooper, Super Robot Grungust, Others, Battleships…).
Esas páginas **no traen el japonés**, así que el cruce es por nombre inglés; solo cubren las unidades originales de
Banpresto (nada de Aerogater, Gundam, Mazinger, etc.).

| id | JP | Antes | Ahora (OG) | Evidencia |
|---|---|---|---|---|
| 416, 418 | グルンガスト弐式 | Grungust Type-2 | **Grungust Type 2** | OGs escribe siempre "Type 2" (10 veces, sin guion) |
| 420 | 龍虎王 | Ryukooh | **RyuKoOh** | OGs (15 veces) |
| 421 | 虎龍王 | Koryuoh | **KoRyuOh** | OGs (13 veces) |
| 422/483, 423/484 | 龍王機 / 虎王機 | Ryuohki / Koohki | **RyuOhKi / KoOhKi** | *proposed*: no aparecen en OGs; misma mayúscula interna por coherencia |
| 201, 202, 236, 259 | 量産型… | Mass Production … | **Mass-Produced …** / **MP …** | OGs: "Mass-Produced Huckebein Mk-II", "MP Gespenst Mk-II" |

Confirmadas sin cambio: Huckebein Mk-II, Huckebein Mk-III (OGs alterna "Mk-III" y "Mk. III"; se usa Mk-III como
Mk-II), Huckebein Boxer, Huckebein Gunner (OGs agrega Type L/R, que en Alpha no existe), G-Hawk, Cybuster, Cybird,
Granzon, SRX, R-1, R-2 Powered, R-3 Powered.

No figuran en las páginas OGs (quedan con el criterio anterior): R-Wing, R-2, R-3, R-GUN Powered, Valsione R (OGs
solo tiene Valsione), Huckebein EX, Grungust Kai, y todos los Aerogater (Zfylud, Judecca, Hermodr, Megillot,
Zechariah, Habakkuk, Ezekiel, Antenora, Astranagant). Para estos sigue haciendo falta una fuente OG en inglés
(p. ej. la base de datos de OG2/OGs de Akurasu para los Aerogater, o la de Alpha/OG para el SRX Team).

Top Rim / Bottom Rim: en las páginas nuevas tampoco aparecen. La única pista sigue siendo el arma (Pinpoint Barrier
Punch); la Pin-Point Barrier es tecnología de Macross en Alpha, así que se mantienen en Macross como hipótesis.

## Casos dudosos (revisar)

| id | JP | Propuesta | Duda |
|---|---|---|---|
| 99 | ザクⅢ改 | Zaku III Custom | oficial Bandai "Custom"; SRW/fans usan "Zaku III Kai" |
| 140 | リカール | Recarl | grafía oficial de Victory no verificada |
| 154 | ガンダムデスサイズヘルカスタム | Deathscythe H. Custom | forma corta fea; alternativa "Deathscythe Hell EW" (nombre oficial EW) |
| 165 | ガンダムエピオン・バード形態 | Gundam Epyon (Bird Mode) | el modo oficial es "MA Mode"; se dejó el literal del juego |
| 190, 195, 196 | ブブリィ, ウィル・ウィプス, ゲア・ガリング | Bubury, Will Wips, Gea Garing | Dunbine sin localización oficial consolidada; hay varias grafías fan |
| 234 | 暗黒大将軍 | Great General of Darkness / "Dark Great General" | la forma corta cambia el orden |
| 316–317 | EVA零号機・改 | Evangelion Unit-00 Kai | "Kai" vs "(Modified)" |
| 368 | VF-1Jアーマードバルキリー | VF-1J Armored Valkyrie / "Armored Valkyrie" | la forma corta pierde "VF-1J" |
| 402 | ボドル旗艦 | Bodol Flagship | nombre oficial de la nave no verificado |
| 406–407 | メルトランディ軍標準戦艦 / 中型砲艦 | Meltrandi Standard Battleship / Medium Gunboat | clases oficiales no verificadas |
| 447, 449 | ヘルモーズ, メギロート | Hermodr, Megillot | grafía OG en inglés no verificada (¿Megilot?) |
| 462 | ブルーガー | Bruga | también circulan Blue Garr / Blugar |
| 477 | 空戦ポッド | Aerial Battle Pod | ¿corresponde al Gnerl oficial? |
| 481–482 | トップリム / ボトムリム | Top Rim / Bottom Rim | sin fila en el glosario; su arma es ﾋﾟﾝﾎﾟｲﾝﾄﾊﾞﾘｱﾊﾟﾝﾁ. Asignados a Macross **sin confirmar** |

Otros puntos:
- **Getter**: se mantuvo "Getter 1/2/3" (Akurasu) en vez de "Getter-1"; decidir una sola grafía para todo el
  proyecto (armas y diálogos incluidos).
- **Registros duplicados**: `ﾀﾞﾝｸ-ｶﾞ` (295, 308): uno podría ser el Dancouga falso (偽ダンクーガ) del glosario, pero el
  nombre en el juego es idéntico; no se distinguió. **Revisado (2026-09-28, #13)**: el 308 es una versión más débil
  (5 armas contra 7, potencias menores, sin 断空光牙剣 ni 断空砲ﾌｫ-ﾒ-ｼｮﾝ): encaja con el falso o una versión enemiga.
  Como el japonés muestra el mismo nombre en los dos, en inglés los dos quedan "Dancouga".
- **Nombres truncados**: `pilot_bin.md` mencionaba 23 nombres cortados a 0x10 bytes en `robot.jsonl`; en el dump
  actual los nombres llegan a 21 bytes (`ｳｲﾝｸﾞｶﾞﾝﾀﾞﾑ･ﾊﾞ-ﾄﾞ形態`), así que se trabajó sobre ellos tal cual.

## Inserción (2026-09-28, #13)
`robot_raf.py build salida.RAF [--report informe.csv]` (etapa `robot` de `build.sh`): nombres desde `glossary.csv`
(`en_final` si entra, si no `en_short`; unidad ≤ 21 B en +0x00..+0x15, arma ≤ 19 B en +0x08..+0x1B), espacio → 0xA0,
relleno con NUL hasta el fin del campo, recompresión LZSS y control de que solo cambien los campos de nombre.
Falla si un nombre falta o no entra. Resultado: 486 unidades, 2.635 registros de arma (692 nombres).
- **Bug corregido en `parse()`**: el byte +0 del arma lleva el índice en los 4 bits bajos y **banderas** en los altos
  (`0x16` Fin Funnel, `0x37`, `0x12` Funnel…). El parser exigía `+0 == k` y cortaba ahí: se perdían 46 registros de
  arma (2.589 → 2.635) y 5 nombres que nunca entraron al glosario (Fin Funnel, Hyper Mega Rifle, Reflector Bit, Aura
  Slash, Hyper Aura Slash; agregados a `weapons_en.csv`).
- `ﾀﾞﾐ-` (casilleros de relleno con potencia 0, p. ej. Gundam y Core Fighter) → "Dummy".
- Probado en el juego (CP04): lista de armas, vista previa de batalla (unidad, piloto y arma de los dos bandos).
