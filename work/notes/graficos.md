# Gráficos con texto (#2, #17–#21)

_2026-09-28. Herramientas: `work/tools/src/tim.py` (TIM ↔ PNG indexado, búsqueda en contenedores) y
`work/tools/src/gfx_entrega.py` (paquete para edición manual: export / check / import)._

## Herramienta TIM ↔ PNG (#17)
- `tim.py scan <archivo>`: busca TIM (magic 0x10, bloques CLUT/imagen con largo coherente) dentro de cualquier archivo.
- `tim.py export/import`: PNG **indexado** con la CLUT 0 como paleta (tRNS para las entradas 0x0000); la importación
  solo escribe los índices de píxel y **nunca toca la CLUT** → paleta intacta = requisito del PNG devuelto.
  16 bpp: PNG RGBA (el bit STP se conserva del original).
- `tim.py selftest`: 54 imágenes de 12 archivos, export → import **byte-idéntico**.
- Tolerancia: si el editor recorta las entradas finales sin usar de la paleta, se acepta.

## Inventario (escaneo de toda la ISO: 37 archivos con TIM)
**Con texto japonés, exportadas** (paquete `work/gfx/entrega_jp/`, piezas G01–G21, detalle en su `ACEPTACION.md`):

| Pieza | Archivo | Qué | Formato |
|---|---|---|---|
| G01 | `TITLE/SUBTITLE.BIN` #1 | celdas `0123456789第話` (dígitos 16 px, 第/話 24 px) | 4 bpp 208×24 |
| G02–G13 | `TITLE/SUBTITLE.BIN` #2–#13 | 12 hojas de títulos de escenario, renglones de 24 px | 4 bpp 256×256 |
| G14–G17 | `TEST/TXT30–33.TIM` | prólogo en rollo continuo: 4 páginas × 21 renglones de 12 px, 240 px de ancho | 4 bpp 256×256 |
| G18 | `TEST/PRO_FONT.TIM` | cartel inicial del prólogo (新西暦一八六年… ヱクセリヲン) | 4 bpp 320×240 |
| G19 | `FONTWIN/WINTEX.BIN` #1 | rótulos de interfaz: `ユニット パイロット レベル 気力 命中 武器名 攻撃力 射程 勝利条件 敗北条件 妖精 獲得経験値 命令内容 強化パーツ 主人公 熟練度 シナリオ 修理費 取得経験値` + iconos `反 防 避 攻` | 4 bpp 256×256, 16 CLUT |
| G20 | `TITLE/TITLEDAT.BIN` #2 | copyright de la pantalla de título | 4 bpp 256×240 |
| G21 | `TITLE/TITLEDAT.BIN` #4 | logo スーパーロボット大戦α (opcional) | 8 bpp 256×240 |

- **#58 resuelto en cuanto a origen**: los encabezados `武器名 攻撃力 射程` y `ユニット HP パイロット` son **gráficos**
  de `WINTEX.BIN` #1 (G19), no strings.
- `FONTWIN/WINDOW.TIM` = otra versión de WINTEX #1 (misma VRAM 448,256): 1.321 píxeles y CLUT 13–14 distintos, **solo
  fuera de los rótulos** (medidores e iconos de reproducción). El EXE nombra ambos → `gfx_entrega.py import` trasplanta
  las cajas de rótulos de G19 a WINDOW.TIM.
- Usados por el juego (strings `\…;1`): `\TITLE\TITLEDAT.BIN` (TITL), `\TITLE\SUBTITLE.BIN` (SNMP), `\TITLE\ENTRYDAT.BIN`
  (ENTR, TITL), `\TEST\TXT30–33.TIM` y `\TEST\PRO_FONT.TIM` (PRO), `WINTEX.BIN` (EXE, TITL, ENTR, SNDM), `WINDOW.TIM` (EXE).
  **Nadie nombra** `FONTWIN/TITLEDAT.BIN` (versión con "PRESS START"), `CPYLGT_*`, `ROGO`, `START_1`, `BANPRE*`,
  `TEST/EFE.TIM` → restos de desarrollo, no se editan.

**Sin texto o ya en inglés:** WINTEX #0 (fuente, `font_build.py`), #2 (LOADING), #3 (caras); TITLEDAT #0/#1/#3/#5–#9
(logo Banpresto, fondos, PRESS ANY BUTTON, START/LOAD/CONTINUE/OPTION); `SNMAP/MW.BIN` (efectos), `SPEFE.BIN`,
`UTIM4.BIN` (sprites de mapa), `SNMAP/MTIM.BIN`, `TEST/MTIM.BIN` (tiles), `FONTWIN/IMBG.BIN` (50 ilustraciones),
`OPTION/OPT.TIM`, `REALF/SUPERF.TIM`, `EM.BIN` (fondo), `BUSTUP/H.BIN`, `ANMTST/EFETES.TIM`.

**Especial:** `TITLE/ENTRYDAT.BIN` #1–#8 = grilla de kanji/kana para ingresar el nombre (tabla de caracteres). Pasarla
a A–Z es trabajo técnico junto con la lógica de ENTR, no redibujo.

**Sin TIM planos (no exportables todavía):** `BATTLE/BATTLE.WAC`, `BUSTUP/CHARA.BIN`, `BATTLE/UNIT.BIN`,
`FONTWIN/WINDATA*.DAT` → formato propio o comprimido (#20, #21). `TEST/EFE.TIM` (no usado) tiene rótulos de barreras
(`ピンポイントバリア`, `Iフィールド`, `ATフィールド`, `オーラバリア`…) + HIT/MISS/SHIELD: la versión que usa el juego
debería estar en alguno de esos contenedores.

## Títulos de escenario (SUBTITLE.BIN, #18) — resuelto (2026-09-29)
Rutina de SNMP `0x800D7460` (a0 = número de escenario − 1, a1 = id del título = `titulo_id` de misiones.csv), la única
que nombra `\TITLE\SUBTITLE.BIN`. La tabla no aparecía en la búsqueda estática porque **el alto (24) no está
guardado**: es fijo en el código.
- **Lectura con offsets fijos** (`8001DB00(fp, tamaño, offset, buf)`): 0x800 fondo (TIM #0), 0x13620 celdas
  `0–9 第 話` (TIM #1), hoja = `0x14020 + hoja·0x8040`. La cabecera de offsets del archivo no se usa → se pueden
  **agregar hojas al final**. Las hojas van todas a VRAM (832,256); su CLUT (768,496) es la misma que usan los dígitos.
- **Tablas en SNMP** (dirección fija): `0x800FD180` recortes, 144 × 8 B `u8 u, u8 v, u16 ancho, u16 x, u16 y` (x/y de
  pantalla, 320×240); `0x800FD600` u8 pedazos por título; `0x800FD684` u8 hoja por título. Los pedazos de un título
  empiezan en la suma de los pedazos de los anteriores → **tope global 144**, todos en la misma hoja, cada uno ≤ 256 px
  (u es u8). Sprites de 24 px de alto, tpage 0x3D, CLUT 0x7C30.
- En pantalla: un renglón en y=104; dos renglones en y=93 y 120 (el japonés ya usaba 2–3 renglones: 14, 31, 32, 39,
  88). El empaquetado japonés (un título partido en dos renglones de la hoja) es solo de la hoja: en pantalla van
  seguidos. `愛に時間を` y `サイキック・エナジー` están en las hojas pero **ninguna entrada los usa**; 121 (欠番) y
  130–132: 0 pedazos.
- Encabezado (y=40): 第 (u=160) y 話 (u=184), 24 px; dígitos de 16 px (u = 16·dígito, v=128 del TIM #1); x inmediatas:
  1 dígito 第 128 · dígito 152 · 話 168; 2 dígitos 第 120 · 144, 160 · 話 176. Solo admite números de 1–99.
- **Inglés** (`subtitle.py`, etapa `titles`): `en` de misiones.csv (o `gfx/render/titulos.csv`) en Liberation Serif
  Bold 20 (DejaVu Serif Bold 20 pedía 165 pedazos); > 304 px → dos renglones; > 256 px → dos pedazos; empaquetado
  por mejor ajuste en hojas de 10 renglones. Resultado: 128 títulos, **136/144 pedazos, 11 hojas** (el archivo no
  crece), 3 títulos en dos renglones (32, 39, 41). Encabezado **Stage N**: "Stage" ocupa las celdas 第+話 (48 px
  contiguos de la textura) y el código pone 話 al lado de 第, antes de los dígitos (5 inmediatos); el sprite baja 2 px
  (`0x800D7A2C`, y 40 → 42) para que la "g" entre en la celda con la misma línea de base que los dígitos.

## Segunda tanda (2026-09-28): contenedores comprimidos (`lzpack.py`)
- **Formato común** de `BATTLE/COMMON.BIN` (64 entradas), `BUSTUP/MAP.BIN` (11), `BACK.BIN` (62), `CHARA.BIN` (411) y
  `BATTLE/UNIT.BIN` (973): `u32 offset[n]` absolutos (offset[0] = 4·n), alineados a 4; entrada = `u32 tamaño, u32 0`
  + LZSS (el de ROBOT.RAF) → TIM, o entrada cruda (datos de animación). `lzpack.py` lee/reconstruye: sin cambios =
  byte-idéntico; una entrada editada se recomprime y va **en su lugar** si entra (mismos offsets y tamaño de
  archivo), si no se reubica y avisa (probado: +2.776 B, resto intacto).
- Compresor propio de `lzpack` (copias solapadas + lazy matching): queda a 0–2 % del original (el de `robot_raf`,
  que prohíbe solapar, no entraba en ningún hueco). **Pendiente de probar en el juego** que un archivo que crece no
  rompa la carga (si pasa, apretar el compresor: falta aprovechar el anillo inicial en ceros).
- **Con texto → piezas G22–G36:** `COMMON.BIN` entrada 1 = 6 rótulos de efectos (クリティカル, シールド防御, 分身,
  ゲッタービジョン, マッハスペシャル, 真マッハスペシャル); entradas 5–23 impares = 10 rótulos de barrera (franja y 161–174,
  x ≤ 80). `MAP.BIN` entradas 1/3/5(=7)/9 = mapa 「現在位置」 de la intermisión con ~60 nombres de lugares (renglones de
  16 px desde y 33, dos columnas). El parche chino no tocó ninguno (están comprimidos).
- **Sin texto:** `BACK.BIN` (fondos de escena), `CHARA.BIN` (retratos), `UNIT.BIN` (sprites de unidades),
  `COMMON.BIN` resto (efectos), `MAP.BIN` pares (mapas).
- **Descartes confirmados:** lo que el chino "cambió" en `CHARA.BIN` (18 entradas), `UNIT.BIN` (62) y `BATTLE.WAC`
  (desde el byte 0: texto chino de SCRIPT) son **sectores pisados**, no traducciones. `BATTLE.WAC` = tabla de datos;
  `WINDATA*.DAT` = geometría de ventanas (registros de 16 B: id, x, y, ancho, alto). → **#21: no hay nombres de ataque
  dibujados en `UNIT.BIN`.**
- **Recortes de los lugares del mapa (#188, hallado 2026-10-04): no hay tabla en el código; los pone cada escena** en
  `SCRIPT.BIN`, instrucción **op 0x0040 sub 4** (512 instancias en 231 escenas, junto a las sub 1/2/8 del mismo grupo).
  `arg` = mapa (1→entrada 1 = G33, 2→3 = G34, 3→5 y 4→7 = G35, 5→9 = G36); datos ASCII
  `x_pantalla 199 ancho 16 u v mx my` con `x_pantalla = 295 − ancho` (alineado a la derecha en x=295; una sola excepción
  234/63 en 5 instancias) y `mx my` = posición de la marca en el mapa. La hoja es 256×256; los renglones v=32…255 son
  para lugares (v=0…31 = cabecera 現在位置).
  - **Varias escenas muestran solo un prefijo del rótulo** (el recorte es más angosto que la caja): 連邦軍極東支部 (w111 de
    175, 30 usos), アメリカ西海岸 (w95 de 175), 南アタリア島 (w87 de 151), 衛星軌道上 (w79 de 143), ア・バオア・クー (w95 de
    127) y el rótulo ilegible de G33 R07c (w31 de 46). El render actual dibuja el rótulo completo y esas escenas lo cortan.
  - **Hecho (cajas dinámicas, build `lugares188_v01`)**: `mapa_lugares.py` + `gfx/render/lugares_mapa.csv` (70 recortes,
    uno por fila; los 5 prefijos van con su propio inglés). Texto DejaVu Sans Bold 14 `tight` (alto 15 + sombra = 16),
    ancho de caja = texto + 4 redondeado a 8k − 1 (como el japonés), tope 231 px (el marco del juego crece con el ancho;
    el mantenedor pidió ≤ 3/4 de pantalla). Empaquetado desde v=32, más anchos primero. `script_bin.py build` llama a
    `mapa_lugares.patch_script` (las 512 instancias, mismo borde derecho) y `gfx_render.py render G33…G36` delega en
    `mapa_lugares.render` (la cabecera H1 sigue saliendo de Gxx.csv).
  - Cómo se llegó: la rutina que abre `\BUSTUP\MAP.BIN` es `SNDM 0x800DF1B0` (archivo 0xC, llamada desde `0x800E2D5C`), pero
    los recortes no estaban en el overlay; el inventario de ops de `SCRIPT.BIN` mostró `248 199 47 16 0 32 …` = caja 移動中.

## Prólogo desplazable: largo fijado por una tabla de pausas (`OVL/PRO_GRP.BIN`, 2026-09-28)

- Overlay en la zona A (base `0x800D61D8`, 127.248 B; código solo en 0x138–0x2400, el resto son 117 KB de ceros que
  el juego usa como área de trabajo → **no es espacio libre**).
- El texto son 20 sprites de 240×12 (uno por renglón) que suben medio píxel por cuadro. `0x800D62AC` crea el renglón
  `n` (página = n ÷ 21 → TIM `TXT30+página`, fila = n mod 21 × 12) y guarda la espera hasta el siguiente, leída de la
  tabla `0x800D87E8` (offset 0x2610): **s16 por renglón, 40 cuadros normal / 80 al cerrar párrafo, -1 = fin**. El
  japonés trae 67 entradas; detrás hay otros datos (`0100 0200 0300…`), así que no se puede agrandar en su lugar.
  Al llegar a -1 pone `+0x1C84C = 1` y, cuando no queda renglón activo, hace el fundido de salida.
- Parche (`gfx_entrega.py pro_patch`, lo aplica `import` si hay `G14.png`): `0xF8 sll $v0,$v0,1 → nop` y
  `0x100 lhu → lb` → la tabla pasa a s8 y entran **135 renglones** en los mismos 136 B. `gfx_render.py` escribe
  `out/prologo_pausas.json` y ya no dibuja renglones en blanco (el hueco entre párrafos lo da la pausa de 80).
  Tope real = 84 renglones (4 páginas × 21).
- Dónde se ve: **después de la batalla de Gunbuster** (no en la partida nueva: ahí solo sale el cartel `PRO_FONT`).
  El cartel G18 ya se vio en el emulador con el overlay parcheado; el desplazable lo prueba el mantenedor.
- Otras rutinas del overlay: `0x800D6C58` arma los sprites; `0x800D7078` es el bucle por cuadro;
  `0x800D7DB0…` máquina de estados del cartel (tabla de saltos en `0x800D61FC`, 6 renglones con esperas de 0x3C).

## Rótulos de avisos del mapa: `SNMAP/KIEFETIM.BIN` entrada 3 (#271, 2026-10-04)
Con "Animation: OFF" el aviso 「クリティカル」 sale en el **mapa** como un Rectangle de textura 48×8 (cmd 0x64; U=0x90, V=0xE8,
texpage (768,256) 4 bpp, CLUT (880,220); pantalla (112,111) en el escenario de prueba). Hallado con el GPU Logger de Redux
(filtro por píxel) y comprobado con un volcado de VRAM del savestate (`saves/dump/critical.sstate`: gzip + protobuf; la VRAM de
1 MB es el campo de longitud `80 80 40` en el offset 19473917 del descomprimido).
- **Origen**: `SNMAP/KIEFETIM.BIN` — tabla de offsets `[0x800, 0x3204, 0x58D0, 0x78D4, 0x8E64]` (no empieza en 4·n, por eso `lzpack`
  y los barridos de TIM la saltaban). Cada entrada: `u32 tamaño, u32 0, LZSS` (el mismo de ROBOT.RAF; `lzpack.lzss(chunk[8:], size)`).
  Entradas: 0 (0x6E20 B → TIM 4 bpp 256×216 en (832,0)), 1 (640,256) CLUT (848,216), 2 (704,256) CLUT (864,216), **3 (768,256)
  CLUT (880,216) = hoja de rótulos** (paleta fila 4 = verde). Las 3 hojas 256×256 se suben a VRAM a la vez que el mapa carga.
- **Contenido de la hoja 3** (rótulos de 12 px con contorno y degradé; cada rótulo está repetido en 5 renglones que "se revelan"):
  barreras en japonés (イナーシャルキャンセラー, ビームコート, オーラバリア, ピンポイントバリア, I・フィールド, ATフィールド, un rótulo «…フィールド» de 4 kanji sin leer, グラビティ・テリトリー, グラビティ・ウォール), **BARRIER HIT!! y SHIELD MISS! ya en inglés**,
  斬り払い, 分身 y クリティカル. Las hojas 1 y 2 y la entrada 0 no tienen texto en CLUT 4.
- Volcado para trabajar: `work/gfx/kief/kief{1,2,3}_clut4.png` (vista con CLUT 4). La hoja cruda es `emu/kief3.bin` (TIM).
- **Hecho (G37, build v02)**: `kief_labels.py` regenera todas las copias de cada rótulo (modelo: bloque = primeros n renglones del
  rótulo de 8, corrido dy; `selftest` reproduce el japonés con 1 píxel de diferencia) en mayúsculas 3×5 estilo BARRIER HIT!!.
  `lzpack.table/read/build` entienden la tabla con relleno; la entrada 3 recomprimida crece 112 B (el archivo, 36 452 → ~36 560 B;
  es la última entrada, solo se mueve el centinela). Textos en `gfx/render/G37.csv`; capturas antes/después en `gfx/comparativas/i271/`.
- Cómo se llegó (por si hay que repetir con otro aviso del mapa): GPU Logger → *Filter by pixel* sobre una letra → último comando;
  texpage + U,V + CLUT → página de VRAM; render 4 bpp con esa CLUT; el origen en disco se halla con `BP_EXEC=0x8001DB00` (lecturas
  de archivo: a0=fp, a1=tamaño, a2=offset) y comparando RAM con archivos.

## Rótulos de interfaz G19 legibles (#68, 2026-10-04)
- Antes: `outline` con la fuente del juego de 8 px → letras huecas y relleno muestreado de la parte oscura del degradé.
- Ahora: estilo **`solid_orig`** (fuente del juego, sin antialias, sombra +1,+1) con tinta/sombra = índices más claro/oscuro
  **del rótulo japonés** (≥10 % de sus píxeles; en G19, 5 y 1). No usar `solid` en hojas cuya CLUT cambia el juego: toma el
  más claro de la CLUT 0 (índice 8 en G19) y en la CLUT del encabezado de Ally List eso es azul oscuro ("Unit" casi invisible).
- **El juego recorta cada rótulo al ancho de tinta del japonés**: si el inglés empieza antes, se corta (pasó con "Range",
  caja x=94 vs japonés x=96 → "| Range" con la R mutilada). Verificar que el inglés quede dentro del ancho de tinta del japonés.
- Capturas JP / antes / después: `docs/capturas/68-g19/`.

## Pantalla de copyright (G20 + TITL, #74, 2026-10-04)
- Se ve ~3 s después del logo de Banpresto (cuadros ~1740–1860 desde el arranque), sobre el fondo de estrellas, y la
  saltea Start. Cada línea es un **sprite centrado** recortado de la hoja G20: registros de 32 B en TITL_GRP (base
  0x800FF190), 3 tablas (+0xF514, +0xF9F0, +0xFB78; la 1.ª con escala: campos 409/532): `u16 0x605 · u16 n · u16
  0x1000|ancho (+4, ancho de 8 bits: máx. 255) · … · s16 dx, dy (+8/+10, desde el centro) · … · u16 uv (+16) · … ·
  u16 medio ancho (+28, centrado) · u16 8`. El japonés trae su ancho redondeado a 8 → el inglés salía cortado.
- La línea 2 de la hoja (© 1999 Project Cybuster) **no tiene registro**: no se muestra. 「©光プロ/アミューズビデオ/PLEX/
  アトランティス」 son dos sprites a la misma altura (el 2.º en u=176 del renglón de ©ビックウエスト).
- `copyright_patch.py` (etapa `copyright`, encadenada sobre el TITL de `entry`) mide la tinta de `out/G20.png` y pone
  ancho/medio ancho (y pega y centra el par de 光プロ). G20.csv: estilo `solid`, DejaVu Sans Bold 12, cajas desde x=1.
- Máquina de estados de la secuencia (TITL `0x80104600`, estado `0x80112D48`, contador `0x80112D49`): 0 carga → 1
  fundido de entrada (`0x80106020`/`0x80106204`, tabla de sprites `0x8010E690`) → 2 muestra 0xB4 = 180 cuadros
  (`0x80106328`) → 3 fundido de salida → 4 fin: `0x80104888` y siguiente rutina `0x80104980` (video de apertura).

## Pantalla propia después del copyright (#279, investigación 2026-10-05)
- **Overlays en la zona C al arrancar:** TITL (zona B, `0x800FF190`, 81.660 B, su BSS llega a `0x8011308C`) se carga antes del
  cuadro 1200; **`MOVE_GRP` (reproductor de STR, 6.712 B) se carga después en `0x8011308C`** (idéntico en RAM al cuadro 1800) y
  termina en `0x80114AC4`. Los búferes del video van desde `*0x80112FA8` (≈`0x8012A63A`).
- **Agrandar TITL rompe el video en PCSX-Redux:** con TITL +8 sectores (todo lo que sigue en el disco se corre) el video de apertura
  sale negro, pero el título llega a tiempo; con +27 sectores el video arranca tarde, y RC01 (+29 respecto del japonés) anda bien.
  No es por pisar memoria (la marca quedó intacta). Depende de dónde cae `O_OPEN.STR` en el disco; la causa no está resuelta.
  → **No correr los LBA de los STR.**
- **Espacio encontrado sin correr nada:** la cola del último sector de `MOVE_GRP` = **1.480 B** (4 sectores − 6.712). El juego
  ya la carga (como ceros) en `0x80114AC4–0x8011508C` siempre que carga MOVE, y la RAM de ahí está libre de 1700 a 6000 (marca
  `A55A279F` probada: LBA idénticos, video y título iguales a RC01). Alcanza para clonar la máquina de estados del copyright
  (`FUN_801045f4`, ~100 instrucciones) con otra tabla de sprites.
- **Enganche:** en el estado 4 de `FUN_801045f4` (`0x801047e4`: `jal 0x80104888` + `PTR_FUN_80112fd4 = 0x80104980`) poner el
  puntero de cuadro `0x80112FD4` en la rutina nueva; esta hace su fundido de entrada, espera y fundido de salida (`0x80106020`
  tabla, `0x80106204`/`0x80106328` dibujo, `0x8001c0c8`/`0x8001c138` fundidos, Start = bit `0x800`) y al final llama a
  `0x80104888` y deja `0x80104980`, como el original.
- **Imagen:** mismo TIM G20 (ya está en VRAM), reacomodando la hoja: el copyright usa solo los índices 0, 1 y 15 de la paleta
  (los demás se pueden usar para resaltar en color) y quedan libres las filas 200–239, la línea 2 (Cybuster, sin registro)
  y el lado derecho de casi todos los renglones.
- **Hecho (build `dedicatoria279_v01`, etapa `dedicatoria`)**: `tools/src/dedicatoria.py` + `patches/dedicatoria.asm`.
  - La tabla de sprites (`0x8010E690`) son 3 secuencias (entrada `+0xC`, quieto `+0x4E8`, salida `+0x670`) con
    comandos de largo variable; cada sprite = comando `0x605` (24 B: `+4` alto<<8|ancho, `+8/+10` dx/dy, `+14` CLUT,
    `+16` uv, `+20/+22` escala en la entrada) + comando `0x207` (8 B: ancla x/y = `+28/+30`, no siempre la mitad).
    Se reusan los 12 sprites: no hace falta entender el resto del formato.
  - La hoja G20 se reempaqueta (MaxRects): 12 recortes del copyright ajustados a la tinta (el ancla se corrige para
    que caigan en el mismo punto de pantalla) + 12 piezas nuevas (4 renglones, filete, encabezado, 2 QR v3 a 2 px por
    módulo con 2 de borde blanco = 66 px, 2 rótulos, 2 relleno de 1 px). Colores nuevos en la CLUT: 2–8 (dorado,
    celeste, oscuro del QR y los tonos medios del texto suavizado).
  - `ded_next` (en vez de `jal 0x80104888`): 1.ª vez copia los campos de la dedicatoria a los 36 registros y salta a
    `0x80104814` (dibuja el fondo, estado 0 de nuevo); 2.ª vez restaura los del copyright y sigue a `0x80104888`.
    `ded_hold` (en vez de `jal 0x80106328` del estado 2) resta 1 al contador un cuadro de cada dos → 360 cuadros (6 s a
    60 Hz) + fundidos. Start corta cada pantalla por separado. MOVE_GRP queda en 7.272 B (920 libres en su sector).
