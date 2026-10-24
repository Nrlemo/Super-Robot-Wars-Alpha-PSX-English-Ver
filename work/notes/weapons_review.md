# Revisión de armas: dudosas, "proposed" y nombres largos

Entrada: `work/glossary/weapons_en.csv` (686 armas). Salida: `work/glossary/weapons_review.csv`
(119 filas: 27 "proposed", 82 con `en` de más de 19 bytes —2 están en los dos grupos— y 12 que se agregaron
o corrigieron con las páginas de Akurasu OGs).
Script reproducible: `work/tools/src/weapons_review_build.py` (se corre desde la raíz del repo).

**Límite técnico**: el nombre del arma vive en el registro de arma de `ROBOT.RAF` (+8, 20 bytes con NUL),
así que el máximo es **19 bytes ASCII**. El script verifica que todos los `en_short` entren en ese
límite y que ninguno coincida con el `en` de **otra** arma (por ejemplo, "Double Tomahawk", "Buster Tomahawk"
y "Rocket Bazooka" ya existen como armas aparte).

## Columnas

| Columna | Contenido |
|---|---|
| `en` | Nombre completo recomendado; si cambió respecto de `weapons_en.csv`, la justificación empieza con `[en changed: was "…"]` |
| `en_short` | Lo que se inserta en el juego (≤19 bytes; igual a `en` si ya entra) |
| `status` | `official` / `fan-standard` / `resolved` (se verificó con fuentes) / `decided` (lo decidió el mantenedor) / `accepted-literal` (era "proposed"; queda literal porque no hay otra traducción al inglés) / `needs-decision` (ya no queda ninguna) |

## 1. Las 4 armas dudosas

| JP | Antes | Recomendado | Estado | Fuente / razón |
|---|---|---|---|---|
| ハイドボンブレイヤー (Zaku III Kai) | Hide Bomb Layer | **Hide Bomb Dispenser** (19 B) | resolved | El mantenedor confirmó ハイドボンブ = "Hide Bomb". ハイド・ボンブ = mina espacial que suelta la caja del hombro izquierdo; レイヤー = sembrador de minas. La Gundam Wiki en inglés lo llama "hide bomb dispenser". |
| ハンドソルト (Zen II, Hyakki) | Hand Salt | **Hand Sold** | decided | Decisión del mantenedor. Es un cortador de tornillo en el brazo derecho; en el anime se pronuncia "ハンドソルド". |
| ドスブレッシャー (Battle Jet) | Dos Pressure | **Dos Pressure** | decided | Decisión del mantenedor: se usa el nombre del diseño original (ドスプレッシャー). Son las cuchillas giratorias de 4 hojas en las puntas de las alas. |
| ギスト・ブロー (Zechariah) | Gist Blow | **Gist Blow** | decided | Decisión del mantenedor. Ojo: **no** puede ser "Geist Blow", porque ese nombre ya lo tiene la ガイスト・ブロー de la Ezekiel. |

## 2. Ex-"proposed" con cambio de nombre

| JP | Antes | Ahora | Fuente |
|---|---|---|---|
| 爆導索 (GP03) | Explosive Cable | **Demolition Chain Mine** → corto "Demolition Chain" | Gundam Wiki: "Demolition Chain Mines" |
| 偏向メガ粒子砲 (Neue Ziel) | corto "Bent Mega Cannon" | corto **Deflect Mega Cannon** | Gundam Wiki: "Deflection Type Mega Particle Cannon" |
| ナルマグネ光線 (Oreana) | Narumagne Ray | **Null Magne Ray** | El propio DC del juego dice "ナルマグネ光線で強制分離": anula el magnetismo que mantiene unida a Combattler V |
| マグマ・ヴァサール (Ryukooh) | Magma Vasal | **Magma Vassal** | Akurasu OGs Mech Database (sección 3) |

Confirmadas sin cambios: **Mack Riot** (riot gun = escopeta: los dos revólveres de Texas Mack se unen en escopeta o en rifle,
y el rifle es "Mack Rifle"), **Ald Laser** y **ARMD Attack**. Las otras 15 quedan como `accepted-literal`.

## 3. Estilo OG en inglés (Akurasu OGs)

**Decisión del mantenedor (2026-09-27): se usa el estilo OG en inglés** para los originales de Banpresto que tengan
nombre oficial en OGs, siguiendo la prioridad de `work/notes/glosario.md` (OGs primero).

Fuentes:
- **Pares JP↔EN directos** (lo más confiable): `info/…OGs_ALL Weapon List…`, `…Barrier Piercing Weapon List…` y
  `…Map Weapon List…`. Traen 82 pares japonés/inglés.
- **Por unidad** (solo inglés): `info/…OGs_Mech Database_*…` y `work/glossary/web/ogs_Mech_Database_R_Series.html`.
  `work/glossary/web/ogs_Weapon_List.html` es la lista de armas intercambiables (Photon Rifle, Roche Saber…).

| JP | Antes | OGs | Menú (≤19 B) | Cómo se confirmó |
|---|---|---|---|---|
| 天上天下無敵剣 (SRX) | Tenjo Tenka Muteki-ken | **Unstoppable Supreme Sword** | Supreme Sword | por unidad |
| 天上天下念動爆砕剣 (SRX) | Tenjo Tenka Nendo Bakusai-ken | **Unstoppable TK Burst Slash** | TK Burst Slash | par JP↔EN |
| 天上天下一撃必殺砲 (SRX) | Tenjo Tenka Ichigeki Hissatsu-ho | **Unstoppable HTB Cannon** | Unstop. HTB Cannon | decisión del mantenedor |
| 天上天下念動破砕剣 (R-1) | Tenjo Tenka Nendo Hasai-ken | **Unstoppable TK Sword** | TK Sword | par JP↔EN (*) |
| 念動集束式レーザーキャノン (R-3) | TK Focused Laser Cannon | **TK Laser Cannon** | — | par JP↔EN |
| 龍王破山剣 (Ryukooh) | Ryuoh Hazanken | **Dragoon Blade** | — | por unidad |
| 龍王破山剣・逆鱗断 (Ryukooh) | Ryuoh Hazanken Gekirindan | **Wrathcleaver** | — | par JP↔EN |
| マグマ・ヴァサール (Ryukooh) | Magma Vasal | **Magma Vassal** | — | por unidad |
| 計都瞬獄剣 (Grungust Type-2) | Keito Shungoku-ken | **Torment Blade** | — | par JP↔EN |
| 計都羅喉剣 (Grunguest Kai) | Keito Rako-ken | **Eclipse Slash** | — | por unidad (**) |
| アイソリッド・レーザー | Isolid Laser | **Eye-Solid Laser** | — | por unidad |
| マルチトレースミサイル | Multi-Trace Missile | **Multi-Trace Missiles** | Multi-Trace Missile | par JP↔EN |
| リープミサイル | Leap Missile | **Leap Missiles** | — | par JP↔EN |
| フルインパクト・キャノン / Gインパクトキャノン | Full Impact / G Impact Cannon | **Full-Impact / G-Impact Cannon** | — | por unidad |
| クロスマッシャー (Valsione R) | Crossmasher | **Cross Smasher** | — | por unidad |
| G・リボルヴァー (R-1) | G Revolver | **G-Revolver** | — | lista de armas |
| ガウンジェノサイダー / T-LINKブーメラン | (fan-standard) | sin cambios de nombre | — | pasan a official |

(*) La Mech Database de OGs llama "T-Link Sword" a la misma arma del R-1 (mismos stats), pero la lista con par
JP↔EN dice "Unstoppable TK Sword" = 天上天下念動破砕剣. Se toma el par, que además mantiene la familia "Unstoppable".
(**) El Grungust de OGs tiene "Eclipse Slash" y "Calamity Slash", y esta última es 計都羅睺剣・暗剣殺 según el par
JP↔EN, así que el 計都羅睺剣 simple es la Eclipse Slash. El juego escribe 喉 en lugar de 睺.

- **Familia "Unstoppable"**: en el menú se saca "Unstoppable" (no entra en 19 bytes) y el nombre completo va en el
  grito de batalla (BXCLIST). La excepción es 一撃必殺砲, que queda "Unstop. HTB Cannon" porque el SRX también tiene
  la HTBキャノン ("HTB Cannon").
- **Cuando hay dos grafías en Akurasu**, gana la del par JP↔EN: Thunderbolt Charm (no "Bakuraifu"), Maxi Blaster,
  Psycho Blaster y Tyrant Over Break.
- **Para revisar aparte** (sin par JP↔EN seguro; no están en el CSV):
  - 頭部バルカン砲 "Head Vulcan": las R usan "Vulcan Cannon" en OGs, pero ese nombre ya lo tiene バルカン砲.
  - ビームカタールソード "Beam Katar Sword": en OGs el R-Gun tiene "Beam Katars".
  - 有線式ビームチャクラム / ラウンド・チャクラム: en OGs el R-2 tiene "Beam Chakram".
  - R-コンビネーション probablemente **no** es la "Formation R" de OGs: aquí es un arma propia del R-1 con potencia 1700, mientras que Formation R es un ataque combinado de R-1 + R-2P + R-3P.

## 4. Convenciones para acortar (aplicadas en todo el CSV)

| Patrón JP | Forma corta | Ejemplo |
|---|---|---|
| ○○メガ粒子砲 (compuesto) | "○○ Mega Cannon" | Main/Sub/Twin/Large/AA/Hyper/Scatter Mega Cannon |
| メガ粒子砲 (solo) | "Mega Particle Gun" (también se usa en fuentes Gundam) | así no se confunde con la メガカノン砲 "Mega Cannon" de la Neue Ziel |
| ハイメガ粒子砲 | "High Mega Particle" | evita chocar con "High Mega Cannon" de la ZZ |
| ○○ミリ機関砲 | "○○mm Autocannon" | 120mm Autocannon (término militar estándar) |
| 対空… | "AA …" | AA Machine Gun, AA Autocannon |
| N連(装)ミサイルランチャー | "N-Tube Missiles" | 12-Tube Missiles (4連 → "Quad Missiles") |
| ○○ミサイルランチャー | "○○ Missiles" | Chest / Spray / Micro / Anti-Ship Missiles |
| Nombre de ataque + sustantivo genérico | se saca el sustantivo | Rolling Buster, Southern Cross, Drill Pressure, Giacobini Meteor |
| ダブル… (cuando el nombre sin "Double" ya es otra arma) | "Dbl …" | Dbl Buster Collider |

## 5. Decisiones del mantenedor (2026-09-27)

- Hand Sold, Dos Pressure, Gist Blow, Dbl Tomahawk Boomer, Sieben Gebaut (literal), Unstop. HTB Cannon.
- Estilo OG en inglés para los originales de Banpresto (sección 3).
- 縮退砲 = "Degeneration Cannon" (Shukutai Hō) → 試作型縮退砲 = "Prototype Degeneration Cannon", corto "Proto Degen Cannon".

**No quedan pendientes de traducción en este CSV.** Queda un punto técnico, opcional: si alguna forma corta no
convence, se puede ver si la rutina que dibuja el nombre del arma lee un campo más largo o si se puede redirigir a
una tabla externa. No lo investigué.

## 6. Limitaciones

- Desde la nube no pude abrir srw.wiki.cre.jp, ja.wikipedia ni las wikis de Fandom (el proxy las bloquea).
  Las fuentes citadas salen de los resúmenes de búsqueda web, no de leer las páginas completas.
  Las 4 dudosas ya quedaron decididas por el mantenedor.
- `weapons_en.csv` no se modificó. Falta pasar `en` y `en_short` de este CSV al glosario principal.
