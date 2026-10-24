# Largo de los nombres del protagonista y la pareja (`$n`, `$N`, `$l`, `$f`…) — 2026-09-28

> **Estado: APLICADO y probado en el juego (2026-09-28, #16).** Topes finales **8/8/8** (nombre / apellido / apodo;
> §7: el editor no da más sin reescribir sus arreglos; decisión del mantenedor). Apodos por defecto de §2 (incluido
> **"Yuu"**). Etapa `entry` del pipeline (`tools/src/entry_patch.py`, `translation/entry_en.csv`). Reservas de
> `check_text.py`/`snmsg.py` ajustadas a 8/8/8. Las §4–§6 quedan como historia de la decisión.

Objetivo: fijar **nombres por defecto en inglés** y **largos máximos** de nombre/apellido/apodo de los 8 protagonistas
antes de traducir diálogos, porque el apodo (`$n`/`$N`/`$l`) aparece en **~24.800 mensajes** (9.374 de SNMSG + 15.405 de SCRIPT) y cada píxel que se le reserve
se descuenta de la línea.

Fuentes: Akurasu (`info/…Character List`, `…Pilot Database`, `…Birthdays`), valores por defecto del juego
(`dump/ovl_strings.jsonl`: tabla de `ENTR_GRP` en `0x80123180` y copia en el EXE en `0x800522FC`), `dump/pilot.jsonl`
(ids 259–290), `vwf_investigacion.md` (expansor `FUN_800E50F8`) y la tabla VWF (`font/en_8px.txt`, vía `check_text.py`).

## 1. Qué guarda el juego

**Pantalla de ingreso** (`ENTR_GRP`): tres campos, `姓／名／愛称` (apellido / nombre / **apodo**), más cumpleaños, sangre,
personalidad y tipo Super/Real. Los 8 personajes por defecto están en una tabla de registros de **0x48 bytes**:
3 campos de **0x15 bytes (20 + NUL)** + 9 bytes de datos. El orden en la tabla es nombre, apellido, apodo:

| # | Nombre | Apellido | **Apodo (`$n`)** | Akurasu |
|---:|---|---|---|---|
| 1 | ﾌﾞﾙｯｸﾘﾝ | ﾗｯｸﾌｨｰﾙﾄﾞ | **ﾌﾞﾘｯﾄ** | Brooklyn "Bullet" Luckfield |
| 2 | ﾕｳｷ | ｼﾞｪｸﾞﾅﾝ | **ﾕｳ** | Yuuki Jaggar |
| 3 | ﾘｮｳﾄ | ﾋｶﾜ | **ﾘｮｳﾄ** | Ryoto Hikawa |
| 4 | ﾀｽｸ | ｼﾝｸﾞｳｼﾞ | **ﾀｽｸ** | Tasuku Shinguji |
| 5 | ﾘｵ | ﾒｲﾛﾝ | **ﾘｵ** | Rio Mei Long |
| 6 | ﾚｵﾅ | ｶﾞｰｼｭﾀｲﾝ | **ﾚｵﾅ** | Leona Garstein |
| 7 | ｸｽﾊ | ﾐｽﾞﾊ | **ｸｽﾊ** | Kusuha Mizuha |
| 8 | ﾘﾙｶｰﾗ | ﾎﾞｰｸﾞﾅｲﾝ | **ｶｰﾗ** | Ricarla Borgnine |

- **El apodo es lo que se ve en los diálogos**: el expansor lee `$n`/`$N` de `+0x2A` (el 3.er campo). Por eso Yuuki
  aparece como **ユウ** y Ricarla como **カーラ** en todo el texto, y Brooklyn como **ブリット**.
- El nombre corto de batalla de estos ids en `PILOT.BIN` es el mismo apodo (`ﾌﾞﾘｯﾄ`, `ﾕｳ`, `ｶｰﾗ`…), campo de **12 bytes**.
- El nombre completo en `PILOT.BIN` es `nombre=apellido` (máx. usado 17: `ﾌﾞﾙｯｸﾘﾝ=ﾗｯｸﾌｨ-ﾙﾄﾞ`), campo de **20 bytes**.
- El EXE tiene una segunda lista con 諒斗/氷川, 樟葉/水羽 (kanji) y **寺田/貴信/Tﾌﾟﾛﾃﾞｭｰｻｰ** (el productor Takanobu
  Terada): parece una lista de nombres especiales (hay un mensaje `入力された[愛称]は使用できません。`). Sin analizar.

## 2. Nombres por defecto en inglés (propuesta)

| # | First (nombre) | Last (apellido) | **Nick (`$n`)** | Nota |
|---:|---|---|---|---|
| 1 | Brooklyn | Luckfield | **Bullet** | Akurasu y OG usan "Bullet". |
| 2 | Yuuki | Jaggar | **Yuu** | El juego usa ユウ. Alternativa: "Yuuki" (ver §5). |
| 3 | Ryoto | Hikawa | **Ryoto** | |
| 4 | Tasuku | Shinguji | **Tasuku** | |
| 5 | Rio | Mei Long | **Rio** | Apellido con espacio, como Akurasu y OG ("Rio Mei Long"). |
| 6 | Leona | Garstein | **Leona** | |
| 7 | Kusuha | Mizuha | **Kusuha** | |
| 8 | Ricarla | Borgnine | **Carla** | El juego usa カーラ; OG: Ricarla "Carla" Borgnine. |

Ancho con la tabla VWF: apodos **12–31 px** (Rio 12, Yuu 16, Bullet 23, Tasuku 31); nombre completo **51–76 px**
(Brooklyn Luckfield = 18 bytes, 76 px).

## 3. Cuánto pesa el nombre en los diálogos

| Variable | Qué es | SNMSG | SCRIPT | Como hablante |
|---|---|---:|---:|---|
| `$n` | apodo del protagonista | 8.033 | 12.662 | 7.112 + 8.694 |
| `$N` / `$l` | apodo de la pareja | 1.971 | 51 / 3.851 | 1.360 + 2.240 |
| `$f` / `$F` | nombre completo (protagonista / pareja) | 26 / 33 | — | — |
| `$L`, `$m` | ¿nombre completo pareja? / ¿apellido? | — | 11 / 2 | — |

437 líneas de SNMSG y 864 de SCRIPT tienen **dos** variables en la misma línea. El japonés pone `$f`/`$F` **solos en su
renglón** (`レビ「手はず通り、リュウセイ＝ダテと\n　$f\n　がいるようだな」`).

Cada línea mide 240 px (~50 caracteres ingleses). El validador reserva hoy 64 px fijos por variable
(`NAME_VAR_PX`, ~27% de la línea). Con la fuente VWF la letra más ancha mide **6 px** (`w`, `v`, `M`, `W`) y los dígitos
**8 px**; el peor caso de un apodo de N letras es 6·N px.

## 4. Opciones para el largo máximo del apodo

| Tope del apodo | Reserva (peor caso) | % de la línea | Entran los 8 apodos | Pros | Contras |
|---|---:|---:|---|---|---|
| 6 letras | 36 px | 15% | sí, justo (Bullet, Tasuku, Kusuha = 6) | máximo espacio para el diálogo | sin margen para nombres propios del jugador ("Kristina", "Brooklyn") |
| **8 letras** ✅ | **48 px** | **20%** | sí, con 2 de margen | cubre la gran mayoría de nombres de pila ingleses; 16 px menos que hoy en cada línea con nombre | nombres de 9+ letras obligan a abreviar |
| 10 letras | 60 px | 25% | sí | casi cualquier nombre | ≈ la reserva actual: ~2–3 palabras menos en ~24.800 mensajes |
| 12 letras | 72 px | 30% | sí | coincide con el campo de 12 bytes de `PILOT.BIN` (techo físico) | la línea con dos nombres pierde 60% |

**Recomendación:**

| Campo | Tope | Motivo |
|---|---:|---|
| Apodo (`$n`, `$N`, `$l`) | **8 caracteres** | reserva de 48 px; todos los apodos por defecto entran; bajo el campo de 12 bytes de batalla |
| Nombre (first) | **9 caracteres** | entra "Brooklyn" y deja 1 de margen |
| Apellido (last) | **10 caracteres** | entra "Luckfield" (9) |
| Nombre completo (`$f`, `$F`, `$L`) | 9 + espacio + 10 = **20 bytes** | exactamente el campo de 20 bytes (entrada y `PILOT.BIN +0x04`); peor caso 120 px = media línea → **siempre en su propio renglón**, como en japonés |

Cambios (aprobados):
1. ✅ `check_text.py` y `snmsg.py`: `NAME_VAR_PX = 64` reemplazado por `VAR_PX` (reserva por variable): `$n $N $l` = 48,
   `$f $F $L` = 120, `$m $M $s $S` = 60.
2. ✅ Glosario: los 8 apodos como términos `pilot` (Banpresto Originals, `status = manual`). `glossary.csv` se editó a mano
   porque regenerarlo necesita `iso_jp/`; `manual.csv` y `decisiones.csv` llevan las mismas filas, así que el próximo
   `glossary_build.py` en server1 las reproduce.
3. ⏳ Pantalla de ingreso (`ENTR_GRP`, necesita la ISO): limitar los tres campos a 9/10/8 caracteres y dejar el teclado inglés sin
   dígitos en el apodo (así el peor caso es 6 px por letra y no 8).

## 5. Dudas y verificación pendiente

1. **Tope real de la pantalla de ingreso en japonés**: no lo medí (en la nube no están los binarios). En server1:
   buscar en `ENTR_GRP` la comparación del cursor contra el largo máximo (`slti`/`sltiu` con una constante cerca del
   manejo de `入力位置を１文字分進めます`) o probar en el emulador escribiendo hasta que el cursor no avance.
2. **¿El apodo se copia al nombre corto de `PILOT.BIN` (12 bytes)?** Probable (los ids 259–290 traen el apodo), pero sin
   confirmar. Prueba: apodo de 8 letras → volcar la RAM del slot del piloto en batalla y ver el hablante.
3. **Qué expande exactamente `$f`/`$F`** (nombre + apellido, o apellido + sufijo; `vwf_investigacion.md` duda) y `$m`/`$L`.
4. **"Yuu" vs. "Yuuki"**: el juego japonés usa ユウ, pero la serie OG en inglés lo nombra casi siempre "Yuuki" y solo
   Carla le dice "Yuu" (según recuerdo; **no verificado** contra el texto oficial). Como `$n` lo dicen todos los
   personajes, "Yuu" es lo fiel al original; "Yuuki" es lo que reconoce un fan occidental. **Decidido: "Yuu"** (fiel al japonés; la biografía del diccionario puede aclarar "Yuuki \"Yuu\" Jaggar").
5. Orden al mostrar el nombre completo: el juego tiene `日本読み/欧米読み` (orden japonés/occidental). En inglés,
   usar siempre el occidental (First Last) y ocultar o fijar la opción.

## 6. Retomar en server1 / desktop (pendientes que necesitan la ISO)

Hecho en la nube (rama `cloud/protagonist-names`, sin ISO): propuesta aprobada, `VAR_PX` en `check_text.py`/`snmsg.py`,
8 apodos en el glosario. Lo que sigue necesita `work/iso_jp/`, Ghidra o el emulador. Orden sugerido:

| # | Tarea | Máquina | Necesita | Resultado esperado |
|---:|---|---|---|---|
| 1 | Integrar la rama y regenerar el glosario | server1 | `iso_jp/UNITPRAM/PILOT.BIN` | `glossary.csv` igual al editado a mano (solo cambian `snmsg_hits`/`in_pilot_bin`, si acaso) |
| 2 | Medir el **tope real** de cada campo en la pantalla de ingreso japonesa | desktop (a mano) | juego JP, partida nueva | cuántos caracteres admite 姓, 名 y 愛称 en ｶﾀｶﾅ y en 英数 |
| 3 | Ubicar en `ENTR_GRP` el código que usa la tabla por defecto y el tope de largo | server1 | `iso_jp/OVL/ENTR_GRP.BIN`, Ghidra | direcciones de las comparaciones del cursor (`slti`/`sltiu` con la constante del tope) |
| 4 | ¿El apodo se copia al nombre corto de `PILOT.BIN` (12 B) y nombre+apellido al completo (20 B)? | desktop + server1 | card con apodo de prueba, `DUMP_RAM` | define si hace falta tocar también `PILOT.BIN` ids 259–290 |
| 5 | Qué expanden `$f`/`$F`/`$m`/`$L` | server1 | Ghidra: `FUN_800E50F8` (`SNMP_GRP`) | confirmar las reservas de 120/60 px de `VAR_PX` |
| 6 | Aplicar los topes 9/10/8 y los valores por defecto en inglés | server1 | resultado de 2–5, `ovl_patch.py`/armips | ISO de prueba: ingresar nombres de largo máximo y ver escena + mapa + batalla |
| 7 | `PILOT.BIN` ids 259–290: `full_en`/`short_en` de los 8 (y los ids "alternativos" 262, 266, 270…) | server1 | `pilot_bin.py build` | hablante de batalla en inglés con el apodo por defecto |

Datos de partida (de este análisis):
- Tabla por defecto en `ENTR_GRP`: primer nombre en `0x80123184` (archivo `+0x100F8`; el overlay carga en `0x8011308C`,
  zona C), 8 registros cada 0x48 B: nombre `+0x00`, apellido `+0x15`, apodo `+0x2A` (0x15 B c/u, **mismo layout que la
  estructura en RAM**) y 9 B más de datos (probablemente cumpleaños, sangre, personalidad, tipo — sin confirmar;
  no sé aún si van antes o después de los nombres). Último registro termina en ~`0x801233C4`.
- Copia en el EXE: `0x800522FC`, mismo paso de 0x48 (referenciada desde `code@0xf480` según `ovl_strings.jsonl`), con la lista de nombres especiales (寺田/貴信).
- Estructuras en RAM: protagonista `*0x8005C248`, pareja `*0x8005C24C`; `+0x00`/`+0x15`/`+0x2A` (`vwf_investigacion.md`).
- Slots de piloto en RAM (mapa): desde `0x8015B264`, 0xB0 cada uno (`pilot_bin.md`).

### Paso 1 — integrar y regenerar el glosario

Traer la rama de la nube:
```bash
cd ~/srw-alpha-psx-en && git fetch origin && git merge --no-ff origin/cloud/protagonist-names
```

Cargar el entorno (rutas, `$SRW_PY`, armips):
```bash
source work/tools/env.sh
```

Regenerar el glosario con la ISO extraída:
```bash
cd work && $SRW_PY tools/src/glossary_build.py
```

Ver qué cambió respecto de lo editado a mano (debería ser nada o solo columnas de conteo):
```bash
git diff --stat work/glossary/glossary.csv && git diff work/glossary/glossary.csv | grep '^[-+]pilot,Banpresto'
```

Correr las pruebas del validador:
```bash
cd work/tools/src && $SRW_PY -m unittest test_check_text
```

### Paso 2 — tope real de la pantalla de ingreso (desktop, a mano)
Partida nueva → 設定内容の変更 → en cada campo (姓, 名, 愛称) escribir con 英数(大) `W` hasta que el cursor no avance;
repetir en ｶﾀｶﾅ. Anotar los topes en este archivo (§1). Guardar el checkpoint de la card justo después de confirmar,
con un apodo reconocible (p. ej. 姓 `AAAAAAAA`, 名 `BBBBBBBB`, 愛称 `CCCCCCCC`, el máximo que permita) para el paso 4:
```bash
saves/guardar_cp.sh
```

### Paso 3 — código de `ENTR_GRP` (server1)

Buscar quién arma direcciones dentro de la tabla por defecto (lui/addiu y punteros):
```bash
cd work && $SRW_PY tools/src/find_addr_refs.py 0x80123170 0x801233D0 iso_jp/OVL/ENTR_GRP.BIN
```

Lo mismo para la copia del EXE:
```bash
cd work && $SRW_PY tools/src/find_addr_refs.py 0x800522F0 0x80052540 iso_jp/SLPS_026.36
```

En Ghidra, importar `ENTR_GRP.BIN` como binario MIPS LE cargado en `0x8011308C` (el proyecto solo tiene el EXE) y seguir
esas referencias: la rutina de ingreso compara el índice del cursor contra el tope del campo. Anotar dirección y constante.

### Paso 4 — ¿el apodo va a `PILOT.BIN`? (server1)
Con la card del paso 2 (`CARD=`), llegar a un mapa/batalla y volcar la RAM (`DUMP_RAM="frame:ruta"`, en dynarec; ver
`fuente_en.md`). Después buscar el apodo de prueba:
```bash
cd work && $SRW_PY -c "import sys;d=open(sys.argv[1],'rb').read();[print(hex(0x80000000+i)) for i in range(len(d)) if d.startswith(b'CCCC',i)]" analysis/ram/ENTRADA.bin
```
Si aparece dentro de un slot de piloto (`0x8015B264 + k·0xB0`, a `+0x29`) → el juego lo copia al campo de 12 B: el tope
de 8 del apodo entra con margen. Si aparece nombre+apellido en `+0x04` → vale el tope de 20 B del nombre completo.

### Paso 5 — `$f`/`$F`/`$m`/`$L` (server1, Ghidra)
Decompilar `FUN_800E50F8` en `SNMP_GRP` (zona A, `0x800D61D8`) y anotar qué campo y qué sufijo usa cada variable.
Si `$f` resulta ser solo nombre + sufijo, bajar su reserva en `VAR_PX` (`check_text.py` y `snmsg.py`).

### Paso 6–7 — aplicar
- Topes: parchear las constantes del paso 3 a **9 (nombre) / 10 (apellido) / 8 (apodo)**; el teclado inglés del apodo
  sin dígitos (peor caso 6 px por letra).
- Valores por defecto: reemplazar la tabla de `ENTR_GRP` (y la copia del EXE si se usa) con §2, espacios como `0xA0`
  si el campo se dibuja con el maquetador VWF (verificar), relleno NUL.
- `PILOT.BIN`: completar `full_en`/`short_en` de los ids 259–290 y construir:
```bash
cd work/tools/src && $SRW_PY pilot_bin.py build ENTRADA.jsonl ../../build/PILOT.BIN
```
- Prueba: ISO con `build_iso.py`, ingresar nombres de largo máximo (`WWWWWWWW`) y revisar escena del script 1, un mapa
  con `$n` como hablante y la batalla. Si algún tope cambia, actualizar `VAR_PX`, §4 de esta nota y `README.md` (estado).

## 7. Verificado en el emulador y aplicado (2026-09-28, #16)

**Topes reales del japonés** (medidos escribiendo hasta que el cursor salta de campo): 姓 **8**, 名 **8**, 愛称 **4**
caracteres. En ｶﾀｶﾅ cada letra con ﾞ/ﾟ ocupa 2 bytes; en 英数 el juego guarda **ASCII puro** (`k` = 0x6B), con
mayúsculas (英数(大)) y minúsculas (英数(小)): el teclado ya sirve para inglés, no hace falta rediseñarlo.

**Editor de nombre (名前登録)** — `S = *0x8012A41C` (en la partida medida, 0x80123818):

| Qué | Dónde | Notas |
|---|---|---|
| Casilleros (6 B: posición en la grilla, juego de caracteres…) | `S+0x43C4 + campo·0x36` | campo 0 apellido, 1 nombre, 2 apodo; **9 casilleros** (8 + terminador); los tres arreglos están pegados a las variables del cursor (`0x43C4 + 3·0x36 = 0x4466`) |
| Cursor / índice máximo | `S+0x4466 + campo·2` / `S+0x446C + campo·2` | máximos 7 / 7 / 3 |
| Carga texto → casilleros | `0x8011B208` → `0x8011B158(casilleros, texto, tope)` | topes 8 / 8 / **4** (`0x8011B274`) |
| Largo útil de un campo | `0x80119B58(campo)` | tope 4 si campo = 2 (`0x80119B64`), si no 8 |
| Casilleros → texto | `0x8011B294` | al confirmar; búfer `0x8012A4F0` (mismo layout que la estructura) |
| Validación | `0x8011B4E0…` | campos vacíos, nombres reservados (`0x8002141C`) |
| Campo activo | byte `0x801233C5` | |

Pasar de 8 en nombre/apellido exige cambiar el paso ×0x36 (escrito en línea en ~20 lugares) y mover las variables
del cursor (~45 accesos): se descartó. **Decisión (mantenedor): 8/8/8** con recorte seguro. Impacto en los textos:
nulo para `$n` (sigue en 48 px, el que pesa en ~24.800 líneas); `$m/$s/$f` solo aparecen en ~70 líneas y su reserva
**baja** (48 / 54 / 108 px). De los 8 predefinidos solo "Luckfield" (9) pasa el tope.

**Tabla por defecto** (`0x80123184`, 8 × 0x48): 9 bytes finales = `+0x3F` 0 · `+0x40` mes · `+0x41` día ·
`+0x42` sangre (0 A, 1 B, 2 AB, 3 O) · `+0x43` sexo · `+0x44/+0x45` personalidad (0–3) · `+0x46` ? (0/1) ·
`+0x47` **orden del nombre** (0 欧米読み, 1 日本読み). Cumpleaños y sangre coinciden con Akurasu (Birthdays).

**Nombre completo:** los menús usan `"%s%s"` (日本読み) y `"%s=%s"` (欧米読み) en ENTR, IMIS, PRM y TITL (una rutina
por overlay; formatos ASCII, fuera de `ovl_strings`). El expansor del mapa (`SNMP_GRP` `0x800E50F8`, tabla de saltos
`0x800D696C` por letra − 'F'): `$n` apodo, `$s` apellido, `$m` nombre, `$f` completo (protagonista); `$N $S $M $F`
de la pareja; `$f` = nombre + "＝" (`0x800D6950`) + apellido, o apellido + nombre sin separador con `+0x47 = 1`.
`$l`/`$L` no están ahí: los usan solo las escenas (SCRIPT) y su expansor no está ubicado (#56).

**¿El apodo va a `PILOT.BIN`?** Sí, en RAM: al entrar al mapa el juego copia **apodo → nombre corto** (`+0x29`,
12 B) y **nombre + espacio + apellido → nombre completo** (`+0x04`, 20 B) en el casillero de piloto del protagonista
(card CP01: casillero 3, `0x8015B474`); los ids 259–290 de `PILOT.BIN` no se usan para él. Con 8/8/8 entra todo
(máx. 18 B con "Luckfield"). Una partida guardada con el juego japonés conserva los nombres japoneses (salen de la card).

**Lista del EXE** (`0x800522FC`): no es la tabla por defecto sino otra con kanji (諒斗/氷川, 樟葉/水羽) y el
productor (寺田 貴信 / Tﾌﾟﾛﾃﾞｭｰｻｰ): parece la de nombres especiales. Se deja en japonés (#56).

**Aplicado** (`tools/src/entry_patch.py`, etapa `entry`, encadenada sobre la salida de `menus`; cada cambio se compara
con el original):
1. Apodo 4 → 8: `0x8011B240` (máx. 3 → 7), `0x8011B274` y `0x80119B64` (4 → 8).
2. Recorte seguro: el bucle de carga (`0x8011B17C`, 11 instrucciones) corta en el tope. Antes, "Luckfield" pisaba el
   primer casillero del nombre (nombre vacío en el editor y cuelgue del emulador al escribir): ahora se ve entero en
   el juego y queda "Luckfiel" solo si el jugador abre el editor y confirma.
3. Nombres por defecto de §2 desde `translation/entry_en.csv` (espacio = 0xA0).
4. `"%s%s"` y `"%s=%s"` → `"%s %s"` en ENTR, IMIS, PRM y TITL; en SNMP "＝" → espacio y `$f/$F` con 日本読み pasan
   por el mismo camino con los registros cruzados ("Hikawa Ryoto"). El orden 日本読み sigue disponible en inglés.

**Probado en el juego** (`build.sh --selftest`, 15 archivos, `verify` OK): lista de predefinidos en inglés con
cumpleaños/sangre ("Rio Mei Long" con el espacio 0xA0), editor con "Luckfiel" sin desborde, apodo de 8 letras
guardado y mostrado. **Visto de paso (#57, viene de la etapa `menus`)**: con los menús en inglés, el editor pierde
sus rótulos (título, menú izquierdo, 名前/愛称) y la ficha "Edit Settings" no muestra los valores.
