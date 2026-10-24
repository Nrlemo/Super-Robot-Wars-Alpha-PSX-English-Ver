# SNMAP/SNDATA.BIN — bytecode de eventos de mapa y mapa mensaje → escenario (2026-09-28)

Herramienta: `work/tools/src/sndata.py` (sin dependencias; solo lee, no reconstruye).

```bash
source work/tools/env.sh; cd work/tools/src
$SRW_PY sndata.py selftest            # estructura, largos de opcode y cobertura de SNMSG
$SRW_PY sndata.py map                 # → dump/sndata_map.csv y dump/sndata_bloques.csv
$SRW_PY sndata.py disasm 7            # listado del bloque 7 con vista previa de los mensajes
```
Por defecto lee `work/iso_jp/SNMAP/SNDATA.BIN` y `work/dump/snmsg.jsonl` (se pueden pasar otras rutas).
Archivo analizado: 2.305.888 bytes, MD5 `5a6998de597fde27e6ee78f4bc7f10d8`.

## Formato (verificado por análisis estático, todos los bytes contabilizados)

| Offset | Contenido |
|---|---|
| `0x000` | 141 × u32: offset de cada bloque (`0x800 + k·0x4048`); el último = tamaño del archivo. Relleno 00 hasta `0x800`. |
| bloque `+0x00` | 18 × i32: `[0] = 16`, `[1] = 4` (iguales en los 140 bloques), `[2..12]` = offset (en u16) de los **eventos 0..10**, `[13..17] = -1`. |
| bloque `+0x48` | código (0x4000 bytes): instrucciones alineadas a u16 = `u8 opcode · u8 largo (en u16, con la cabecera) · args u16`. `0xFF` = fin, relleno `FF`. |

- Los 11 eventos existen en los 140 bloques y cada uno empieza con `00 02 <n>` (etiqueta n) y termina con `01`.
  Después del evento 10 vienen subrutinas terminadas en `0A` (en el CSV: `S1`, `S2`…). Casi todo el diálogo está en
  las subrutinas; los eventos las llaman.
- **Cada opcode tiene largo fijo** (163 opcodes; solo `B9` es variable: 9/13/21/25). El recorrido lineal de los 140
  bloques termina exacto en el `FF`, sin basura: 81.297 instrucciones.
- `08 <off>` = salto a un offset (en u16) del bloque: los 902 destinos caen en inicio de instrucción.
- `04`/`06` (4.878 cada uno) parecen abrir/cerrar un bloque condicional. El resto de los opcodes (despliegue de
  unidades, BGM, flags, cámara…) **sin decodificar**: no hace falta para el mapa de mensajes.
- **Corrección**: la nota anterior (`poc_snmsg.md`) decía que `09 02 <id>` referencia mensajes. **No**: `09 <n>` toma
  valores hasta 6.545 y los repite entre bloques; es otra cosa (probable flag/variable). Coincidía por casualidad.
- Espacio libre: el bloque más lleno (109) usa 13.946 de 16.384 bytes → **≥ 2.436 bytes libres en todos**.

## Opcodes que usan mensajes de SNMSG (índice global de slot)

| Op | Args (u16) | Qué es | Casos |
|---|---|---|---:|
| `17` | piloto, ventana<<8, msg | línea normal | 21.778 |
| `18` | piloto, ventana<<8, msg | **8 variantes** `msg..msg+7` (piloto 2000 = `$n` protagonista, 2001 = `$N` pareja) | 1.137 |
| `1B` | piloto, ventana<<8, msg | ídem `18` (solo en los bloques finales 125/129) | 4 |
| `19` | cond, piloto, ventana<<8, msg | línea condicionada (cond sin decodificar; ¿según quién está en el mapa?) | 696 |
| `1C` | piloto, ventana<<8, msg, x | línea | 2 |
| `1D` | piloto, ventana<<8, msg | línea | 2 |
| `1E` | 0, msg victoria, 0, msg derrota | condiciones de victoria/derrota (una por fase del mapa) | 330 |
| `1F` | piloto, 0, msg | elección de 2 opciones (`…選択`) | 22 |

- **piloto = ID de `UNITPRAM/PILOT.BIN`** (el retrato): 0xB1 = 甲児, 0xEE = タシロ, 0x1AB = 副長… (verificado con
  `dump/pilot.jsonl`). 2000/2001 = protagonista/pareja.
- ventana = 0..5 (probable posición/estilo de la ventana; sin verificar en pantalla).
- **Cobertura: los slots 0..32.287 están referenciados exactamente una vez**; 32.288..32.543 son `Dummy String`.
  Cada bloque usa un rango **contiguo** de slots y los rangos van en orden de bloque (lo comprueba `selftest`).

## Salidas

- `dump/sndata_map.csv` — una fila por slot de SNMSG: `slot, bloque, escenario, ruta, titulo_jp, evento, orden, op,
  tipo, variante, piloto_id, piloto, ventana, extra, speaker`. Se cruza con `dump/snmsg.jsonl` por `slot` = `id`.
  - `tipo`: `linea`, `linea_cond`, `protagonista`/`pareja` (con `variante` 1–8, la numeración de la guía de estilo §3),
    `victoria`, `derrota`, `eleccion`, `sin_uso`.
  - `evento`: `E0..E10` o `S1..Sn`; `orden` = orden de la instrucción dentro del bloque (orden del código, que en
    general es el orden en que se ve, pero con saltos y condiciones puede no serlo).
  - `piloto`: nombre corto de PILOT.BIN, útil cuando la línea no trae el hablante en el texto.
- `dump/sndata_bloques.csv` — una fila por bloque: escenario, ruta, id de título (tabla del juego), títulos JP/EN,
  **confianza**, nota (con la fuente), rango de slots, cantidad de mensajes y hablantes principales.

## Bloque → escenario

La tabla `ESCENARIOS` de `sndata.py` cruza, bloque por bloque, cuatro fuentes:

1. **Tabla oficial de títulos del juego** (`TITULOS` en `sndata.py`): 129 punteros a títulos en el overlay
   `OVL/IMIS_GRP.BIN` (`ptr@0x1FB74`, índice 1..129; idéntica en `TITL_GRP` `ptr@0x13BCC`; ver
   `dump/ovl_strings.jsonl`). **Los bloques siguen exactamente ese orden**: los escenarios con más de un mapa (evento
   previo o partes) ocupan bloques consecutivos. `selftest` comprueba que el orden no se rompa y que cubra la tabla
   entera. Es la fuente de los títulos en japonés (`titulo_jp`).
2. `info/…Complete Chart…` (Akurasu): títulos, condiciones de victoria/derrota por fase, elecciones con su texto JP.
   Comparé **todas** las condiciones del op `1E` de cada bloque con las de la wiki.
3. `info/…Timetable…` (Akurasu): qué columna es cada ruta y qué unidades se suman en cada una.
4. `info/…Guide and Walkthrough… By Cyath` (GameFAQs): diagrama de rutas de JL Lee (títulos en JP), puntos de
   experiencia por elección y el walkthrough de la ruta real (partes de mapa, eventos). Ojo: el japonés de esa página
   está en Shift-JIS crudo dentro del HTML "UTF-8"; hay que leerlo como cp932.
5. `info/s-rpg-navi.com/` (128 páginas, una por escenario y ruta, en japonés, Shift-JIS): la ruta de cada página
   (`スーパー系ルート`, `撃ち落としルート`…), las condiciones de victoria/derrota **por parte** (前半/後半), las unidades
   que llegan en cada fase, los eventos y el "siguiente escenario". Las 128 páginas caen en su bloque con la ruta
   correcta; no hay páginas para el 63 ni para 欠番/全能なる調停者/シト新生 (consistente con sus bloques sin mensajes).

| Confianza | Bloques | Criterio |
|---:|---:|---|
| alta | 136 | contenido (condiciones, elecciones, elenco o texto), orden de la tabla de títulos y página de s-rpg-navi coinciden |
| baja | 4 | bloques vacíos 130–133: 4 bloques para 3 títulos (欠番, 全能なる調停者, シト新生), ubicados solo por orden |

Orden de los bloques: 0 prólogo · 1–6 super 1–6 · 7–12 real 1–6 · 13–14 esc. 7–8 · 15 = 9 super · 16 = 9 real ·
17–20 ruta Jaburo 10–13 · 21–24 ruta Atalia Sur 10–13 · 25–32 esc. 14–19 · 33–34 esc. 20 (evento + mapa) ·
35–51 las tres rutas 21–25 (EVA-02 = Aura, 35 es el evento previo del 21 / Lejano Oriente, 43–44 = partes 1 y 2
del 23 / Liga Militar) · 52–53 esc. 26 · 54 esc. 27 · 55 esc. 30 (EVAs) · 56–64 ruta derribo 31–39 · 65–73 ruta
atrapar con EVA 31–39 · 74–75 esc. 40–41 · 76–87 las tres rutas 42–45 (Reinforce Jr. / Gran Garan / Goraon) ·
88–89 esc. 46 · 90 esc. 47 · 91 esc. 50 · 92–104 las tres rutas 51–54 · 105–107 esc. 56 y 55 · 108–109 esc. 57
(evento + mapa) · 110–112 ruta Axis 58–60 · 113–115 ruta Angel Halo 58–60 · 116–121 esc. 61–65 (62 y 64 en dos
partes) · 122–125 final ≥45 puntos (66 + 67 en 3 partes) · 126 esc. 63 · 127–129 final <45 puntos (66 + 67 en 2
partes) · 130–133 vacíos · 134 esc. 28 · 135–136 esc. 29 · 137 esc. 48 · 138 esc. 49 · 139 esc. 30 (a la fuerza).
Los esc. 28–30, 48 y 49 están al final del archivo y de la tabla de títulos (agregados tarde en el desarrollo).

Títulos que existen en la tabla del juego pero no en la wiki: **欠番** ("número vacante"), **全能なる調停者** y
**シト新生** (título de la película de Evangelion). Sus bloques están vacíos: probablemente escenarios cortados. El 63 (solo historia, sin mapa; confirmado jugando) también
tiene bloque propio (126) sin mensajes: **el juego reserva un bloque por título aunque no haya mapa**, lo que apoya que
130–133 sean esos títulos sin mapa (siguen en confianza baja porque son 4 bloques para 3 títulos).

### Correcciones acumuladas

| Bloque | Primera versión | Ahora | Fuente |
|---|---|---|---|
| 15 / 16 | 9 real / 9 super | **9 super / 9 real** | Timetable + Complete Chart + s-rpg-navi (en el 2PP de la real llegan R-GUN, R-1 y R-2; en la super solo R-GUN) + Cyath + tabla de títulos |
| 52 / 53 | 26 sin determinar | **紅いエヴァンゲリオン / 海からのマレビト** | Timetable, diagrama de JL Lee, elección de la Complete Chart; s-rpg-navi: derrota アスカ・母艦 (52) / 母艦 (53) |
| 56–73 | rutas real / super | **derribo / atrapar con EVA** | Timetable y diagrama de JL Lee; el 65 empieza con las EVA en posición |
| 110 ↔ 112 | 60 / 58 | **58 神の国への誘惑 / 60 戦士、再び…** (Axis) | condiciones de derrota de la Complete Chart + tabla de títulos |
| 122–129 | final A/B sin título | **≥45: 66 絶望の宴… + 67 この星の明日のために (3 partes) · <45: 66 人類に逃げ場なし + 67 鋼の魂 (2 partes)** | condiciones por parte de la Complete Chart; walkthrough de Cyath (<40) |
| 135 / 136 | 29 real / 29 super | **29 super / 29 real** | tabla de títulos + texto (en el 135 Ryusei pregunta por el arma nueva del Grungust Type-2 de `$n`; el conteo de palabras había contado la máquina del rival) + s-rpg-navi (29 super: 計都瞬獄剣 para el Grungust) |
| 43 | ¿parte 1 del 23? | **parte 1 del 23** | Cyath: "Destroy Dante in first part of scenario" |
| 33, 35, 108 | ¿evento previo? | **evento previo** del 20, 21 y 57 | texto de los bloques + Cyath: Ramiel derriba a la EVA-01 al salir (el disparo del 4PP que cita s-rpg-navi es dentro del bloque 34); Drake observa a la Argama; prueba de la Angel Halo contra Side 3 |
| 126 | sin asignar | **63 終わりの始まり**: solo historia, sin mapa | tabla de títulos + Complete Chart + confirmado jugando (mantenedor) |

Discrepancias entre fuentes (manda la tabla del juego): esc. 35 = **イングラムの真意** (la Complete Chart dice
殺意; JL Lee y s-rpg-navi dicen 真意); esc. 18 super = **紅い稲妻** (Akurasu: 紅の稲妻; s-rpg-navi coincide con el
juego); umbral del final = **熟練度45以上** (Akurasu y s-rpg-navi; JL Lee decía 40). Erratas de s-rpg-navi frente al
juego: 誰がために鐘は「鳴る」 (juego: 踊る), 第二次直上「会議」 (juego: 会戦), 瞬間、心「重ねて」 (juego: かさねて).

## Implicancias para la traducción

- Ya se puede dar contexto a cada línea de SNMSG: escenario, ruta, quién habla (aunque el texto no lo diga) y si es
  una variante del protagonista.
- Las 8 variantes del protagonista y de la pareja en SNMSG están confirmadas por el código (op `18`/`1B`), igual que
  la regla de la guía de estilo.
- **Partir un mensaje largo en dos es posible en principio**: hay ≥ 2.436 bytes libres por bloque y 256 slots
  `Dummy String` al final de SNMSG. Requiere insertar una instrucción `17` y **corregir los saltos `08`** posteriores
  del bloque. Sin probar en el juego.

## Pendiente / incertidumbres

- Confirmar en el emulador los bloques 130–133 (vacíos) y, si se quiere, uno o dos de los eventos previos (33, 35, 108).
  Una forma rápida: breakpoint de lectura en el buffer de SNDATA al entrar a un mapa y anotar el índice de bloque.
- Buscar en `SLPS_026.36` / overlays el código que pasa del id de título al índice de bloque (explicaría los mapas extra).
- Significado de `ventana`, del `cond` del op `19` y del arg extra del op `1C`.
