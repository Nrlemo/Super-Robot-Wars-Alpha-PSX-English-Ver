# Checklist de regresión — borrador (2026-09-28)

Qué hay que comprobar en cada build para no romper lo que ya anda, y qué falta cubrir. Se apoya en el pipeline
(`notes/pipeline_build.md`), en las rutas automáticas de `work/tools/regresion.sh` y en los checkpoints de `saves/cards/`.
Cubre las cuatro áreas de la Fase 4 de `CLAUDE.md` (menús, combate, escenas de historia, guardado/carga) y el resto
de lo que el juego muestra.

## 0. Niveles

| Nivel | Qué | Cómo | Cuándo | Tiempo (estimado) |
|---|---|---|---|---|
| **N0** | Controles estáticos | `work/tools/build.sh --selftest` (automático, corta la build si falla) | cada build | ~1–3 min |
| **N1** | Smoke en emulador | `work/tools/regresion.sh <cue> <dir> boot prologo` (automático + mirar 2 hojas) | cada build que toque EXE, fuente, SNMSG o la imagen | ~5 min |
| **N2** | Rutas con checkpoints | `REF=<corrida anterior> work/tools/regresion.sh <cue> <dir> cp04 cp12` + revisar `diff.png` | cada tanda de traducción | ~5 min + revisión |
| **N3** | Manual en la desktop | jugar la build con este checklist (§4) | antes de publicar; después de cambios grandes | 1–2 h |
| **N4** | Publicación | `build.sh --strict --release` + otro emulador + hardware real (§5) | por versión pública | — |

**Flujo por tanda de traducción**
1. Editar `en` (volcados de `dump/`, o la fuente de `translation/` y regenerar con `menus_draft.py` / `dict_build.py`).
2. `check_text.py --only <formato>` hasta 0 errores (funciona en la nube).
3. En server1: `work/tools/build.sh --selftest --name tanda_<n>` → N0 en verde.
4. `REF=work/emu/shots/<tanda anterior> work/tools/regresion.sh work/build/tanda_<n>/tanda_<n>.cue work/emu/shots/tanda_<n>` → N1 + N2.
5. Mirar `sheet.png` / `diff.png` de cada ruta, anotar en la tabla del §8, commit.

## 1. N0 — Controles estáticos (automáticos)

| # | Control | Etapa | Pasa si | Detecta |
|---|---|---|---|---|
| 0.1 | Entorno completo para las etapas elegidas | `preflight` | nada falta | build a medias por herramienta ausente |
| 0.2 | Herramientas: reconstrucción sin cambios == original (SNMSG, SCRIPT, BXCLIST, DEADMESS/EM, PILOT, LZSS) | `selftest` | todas idénticas | una herramienta que dejó de ser fiel |
| 0.3 | Pruebas unitarias (`test_check_text`, `test_build_all`) | `selftest` | OK | regresiones del validador y del pipeline |
| 0.4 | Integridad del `jp` de los volcados de trabajo (SCRIPT, BXCLIST, PILOT) | `selftest` | 0 filas distintas | traducciones corridas de fila / volcado editado a mano |
| 0.5 | Tabla VWF == la derivada de `font/en_8px.txt` | `font`, `validate` | idénticas | validadores midiendo con otra tabla |
| 0.6 | `check_text.py`: bytes, líneas, px, variables `$n…`, marcas ﾞ/ﾟ, cp932 | `validate` | 0 errores (avisos = límites supuestos) | texto cortado, 4.ª línea, glifos especiales, variables perdidas |
| 0.7 | `menus_en.jsonl` al día con `menus_map.txt` | `validate` | 0 filas distintas | editar el mapa y olvidarse de `menus_draft.py` |
| 0.8 | EXE: mismo tamaño, cambios solo dentro de `EXE_WINDOWS`, tabla VWF dentro del EXE correcta | `exe` | sin problemas | armips escribiendo donde no debe |
| 0.9 | Herramientas de texto sin `ERROR`; `AVISO` de BXCLIST (bloque mayor que el original) | `snmsg`…`pilot` | sin errores | casilleros que vuelven al japonés en silencio; bloques de batalla gigantes |
| 0.10 | Menús: filas retenidas con motivo y filas "de riesgo" (in situ más allá de su hueco) | `menus` | revisadas | datos pisados junto a un string |
| 0.11 | Overlays dentro de su zona (lo controla `ovl_patch.py`); crecimiento en zona C avisado | `menus` | dentro | overlay que pisa la zona siguiente |
| 0.12 | Imagen: mismos archivos que el layout; contenido byte a byte; XA/STR por tamaño; sectores 0–15 = original; `.cue` | `verify` | 0 errores | mkpsxiso/FS roto, archivo equivocado, licencia |
| 0.13 | Tamaño: ≤ 74 min (aviso) / ≤ 80 min (error) | `verify` | ≤ 74 min | imagen que no entra en un CD-R |
| 0.14 | `--null`: ISO sin reemplazos == original (sha1) | `verify` | idéntica | cambio de versión de mkpsxiso o de `iso_jp` |
| 0.15 | Parche: aplicado sobre la original reproduce la build | `release` | sha1 igual | parche inservible para el usuario |

## 2. N1 — Smoke en emulador (automático + mirar)

`work/tools/regresion.sh` falla solo (código 1) si faltan capturas, si todas son de un solo color o si todas son iguales.
Además hay que **mirar** `sheet.png` de cada ruta:

| Ruta | Qué mirar en `sheet.png` | Cubre | Estado de la ruta |
|---|---|---|---|
| `boot` (card virgen, 4 capturas hasta f3600) | logos → intro/título sin pantalla negra ni basura | EXE, FS, SYSTEM.CNF, licencia | usada desde el 2026-09-27 (`smoke_boot.sh`) |
| `prologo` (`battle_prologue.sh fresh`, 32 capturas f12360–f14260) | frase de ataque de Tashiro, nombre del arma, vista previa, frase del enemigo, resultado | VWF en batalla, fuente, SNMSG (diálogo previo), BXCLIST, PILOT (hablante), ENTR (datos por defecto) | ruta probada (`fuente_en.md`) |

## 3. N2 — Rutas con checkpoints

Los cambios contra la corrida anterior (`diff.png`) **no son error**: el texto nuevo y el azar del combate cambian
píxeles (con la ISO modificada el combate de CP04 cambia de resultado, `pilot_bin.md`). Sirven para mirar solo lo que cambió.

| Ruta | Card + entradas | Qué mirar | Cubre |
|---|---|---|---|
| `cp04` (41 capturas f3300–f5700) | CP03 + grabación CP04 (Amuro, Fin Funnel) | cursor en el mapa, **lista de armas** (nombres ≤19 B, columnas alineadas), vista previa (nombres de piloto/unidad), frases de 2 líneas, hablante, vuelta al mapa | ROBOT.RAF, PILOT, BXCLIST, BTL, VWF |
| `cp12` (18 capturas: f4900, f6300, f6600–f11100) | CP12, LOAD → intermisión → 次のマップへ → escena del esc. 62 | **menú de intermisión** y descripciones; escena (script 234): líneas en orden, 3 por caja, cambios de escena | IMIS, SCRIPT, VWF |

Los cuadros de `cp04`/`cp12` salen de las grabaciones y de `notes/script_bin.md`: en la primera corrida real
confirmar que caen donde dice la tabla y ajustar `regresion.sh`. Una grabación se desfasa si el texto cambia los
tiempos de lo que recorre: se vuelve a grabar en la desktop (`saves/LEEME.md`).

## 4. N3 — Manual por pantalla (desktop)

Con `ISO=<build>.cue ./jugar.sh CPxx` (o `nuevo`). Marcar lo revisado; entre corchetes, el archivo que lo produce.
Para saber en qué escenario aparece un mensaje de SNMSG que se quiere ver: `work/dump/sndata_map.csv` (slot → bloque →
escenario, `notes/sndata.md`).

**Arranque y título**
- [ ] Logos e intro (FMV `STR/`) completos, con audio; sin cortes ni saltos. [imagen: LBA de XA/STR corridos]
- [ ] Menú del título (nueva partida / LOAD / CONTINUE / opciones): textos y cursor. [TITL]
- [ ] Pantallas con letras de canciones: **quedan en japonés** (decisión 2026-09-28) y se ven igual que en el original. [TITL]

**Ingreso de datos del protagonista**
- [ ] Nombre, cumpleaños, sangre, personalidad, pareja: textos y descripciones. [ENTR — zona C]
- [ ] Teclado de nombre: íconos de botón en su lugar (pendiente P5 de `menus_borrador.md`). [ENTR]
- [ ] Topes aprobados (apodo ≤ 8, nombre ≤ 9, apellido ≤ 10; `nombres_protagonistas.md`): un apodo de 8 letras anchas (p. ej. `WWWWWWWW`) en diálogos de mapa y escenas no pasa de la caja (`check_text.py` reserva 48 px para `$n`/`$N`/`$l`, 60 para nombre/apellido, 120 para el nombre completo). [ENTR, SNMSG, SCRIPT]
- [ ] Nombres por defecto en inglés (Bullet, Yuu, Ryoto, Tasuku, Rio, Leona, Kusuha, Carla) en la pantalla de ingreso y como hablante en batalla. [ENTR, EXE, PILOT]

**Prólogo**
- [ ] Texto del prólogo sobre imagen. [TEST/TXT3x.TIM — gráficos, pendiente]
- [ ] Diálogo del mapa: 3 líneas, nombre del hablante, sin cortes a la derecha. [SNMSG]

**Mapa**
- [ ] Menú de comandos de unidad y de sistema; ventanas de estado de unidad/piloto (stats, rangos de terreno alineados). [SNMP, PRM]
- [ ] Lista de espíritus y su descripción (PRM reempaquetada; las 16 abreviaturas 熱 手 狙… siguen en japonés). [PRM]
- [ ] Condiciones de victoria/derrota. [SNMSG]
- [ ] Título del escenario al empezar. [TITLE/SUBTITLE.BIN — gráficos, pendiente]
- [x] Pantalla de despedida con frase del personaje (セーブ → いいえ; `tools/deadem_test.sh em`, 2026-09-28). [EM]
- [x] Derribar a un piloto con frase de derribo (`tools/deadem_test.sh dm`, 2026-09-28; nombre corto + 「」 los agrega el juego). [DEADMESS]
- [ ] Mensajes de sistema (turno, guardado). [EXE — pendiente]

**Combate**
- [ ] Vista previa: nombres, % de acierto, daño; dígitos alineados (0x20 y dígitos conservan 8 px). [BTL, PILOT, ROBOT]
- [ ] Lista de armas: nombres completos, columnas alineadas. [ROBOT.RAF]
- [ ] Frases de ataque y defensa: 2 líneas, hablante correcto, diálogos piloto/copiloto en secuencia (Show y Cham, Kouji y Sayaka…). [BXCLIST]
- [ ] **Bloque BXCLIST más grande (Show, id 149)**: combate completo sin cuelgue (memoria dinámica). [BXCLIST — sin probar]
- [ ] Animación ON/OFF; nombres de ataque dibujados. [BATTLE/UNIT.BIN — gráficos, pendiente]
- [ ] Contraataque / defensa / esquiva, apoyo; menú de orden de reacción. [BTL]
- [ ] Resultado: dinero, experiencia, subida de nivel, espíritus y habilidades nuevas. [PRM, BTL]

**Intermisión**
- [x] Menú principal y descripciones (8 overlays, 1276 textos; `tools/menus_test.sh` y CP12, 2026-09-28). [IMIS]
- [ ] Cada submenú: estado de unidad, mejoras de unidad y de arma, estado de piloto, trasbordo, hadas, partes, guardar/cargar, opciones, siguiente mapa. [IMIS, PRM]
- [ ] Listas de pilotos y unidades: nombres (≤20 / ≤21 B), números alineados. [PILOT, ROBOT]
- [ ] Partes: nombres y efectos (tabla de ancho fijo en PRM: forma corta). [PRM]
- [ ] Diccionarios de personajes y robots: nombres, series, biografías de 44 columnas, cantidad de filas. [DC/DR; rótulos de SNDM en japonés, #11]
- [ ] Escenas: 3 líneas por caja, `$n`/`$l`, variantes por protagonista (8), cambios de escena. [SCRIPT]
- [ ] Mensajes de error de memory card (sin card, llena). [IMIS — strings contiguos sin puntero]

**Guardado y carga (memory card)**
- [ ] セーブ en la intermisión → mensaje de éxito → reset → LOAD → misma partida (nombres, dinero, escenario).
- [ ] 中断 en el mapa → CONTINUE desde el título → vuelve al mismo turno.
- [ ] Nombre del archivo de guardado en el administrador de la BIOS. [EXE — pendiente: queda en japonés]
- [ ] Cards grabadas con la ISO japonesa (CP01–CP12) cargan en la build; ¿los nombres de pilotos se guardan en la card? (pregunta abierta 3 de `pilot_bin.md`)
- [ ] Una partida guardada con la build carga en la build siguiente (compatibilidad entre versiones de la traducción).

**Final**
- [ ] Créditos (overlay END, ~470 strings; sin traducir por ahora): sin basura. [END]
- [ ] FMV de los finales con audio. [STR/XA]

## 5. N4 — Publicación

- [ ] `build.sh --strict --selftest --release` en verde; `SHA1SUMS` con la sha1 esperada de la ISO original.
- [ ] Parche aplicado con un aplicador de Windows (Delta Patcher / xdelta UI) sobre una copia de la original → misma sha1.
- [ ] Segundo emulador: **DuckStation** (`work/tools/run_duckstation.sh`) — boot, prólogo, CP04, CP12.
- [ ] Hardware real: ODE o CD-R de 74 min en una consola japonesa (o con chip); cargas, FMV, audio, guardado.
- [ ] Reproducibilidad: dos builds del mismo commit dan la misma sha1.
- [ ] N3 completo en la última build.

## 6. Matriz de trazabilidad

| Archivo | Etapa | Control N0 | Ruta N1/N2 | Ítems N3 | En el juego |
|---|---|---|---|---|---|
| `SLPS_026.36` (VWF) | `exe` | 0.8 | boot, prologo | todo el texto | ✅ mapa, menús, escena, batalla |
| `FONTWIN/8FONT_R.TIM`, `WINTEX.BIN` | `font` | 0.5 | prologo, cp12 | todo el texto | ✅ |
| `SNMAP/SNMSG.BIN` | `snmsg` | 0.6, 0.9, 0.2 | prologo | prólogo, mapa | ✅ prueba de concepto |
| `BUSTUP/SCRIPT.BIN` | `script` | 0.4, 0.6 | cp12 | escenas | ✅ largo libre (esc. 62) |
| `BATTLE/BXCLIST.BIN` | `bxclist` | 0.4, 0.6, 0.9 | prologo, cp04 | combate | ✅ todas más largas (CP04); ⏳ bloque de Show |
| `SNMAP/DEADMESS.BIN` | `deadmess` | 0.6 | `deadem_test.sh dm` | derribo | ✅ textos de prueba (3 líneas) |
| `SNMAP/EM.BIN` | `em` | 0.6 | `deadem_test.sh em` | despedida | ✅ textos de prueba (3 líneas) |
| `UNITPRAM/PILOT.BIN` | `pilot` | 0.4, 0.9 | prologo, cp04 | combate, listas | ✅ nombre corto en batalla |
| `UNITPRAM/ROBOT.RAF` | `robot` | — | cp04, cp12 | lista de armas, listas | ✅ nombres de unidades y armas (#13, 2026-09-28) |
| `OPTION/DC.BIN`, `DR.BIN` | `dc`, `dr` | 0.6 | `dict_test.sh dc\|dr` (sin ruta de `regresion.sh`: grabar, §7) | diccionarios | ✅ fichas en inglés (#15, 2026-09-28); rótulos de SNDM en japonés (#11) |
| `OVL/IMIS_GRP.BIN` | `menus` | 0.7, 0.10, 0.11 | cp12 | intermisión | ✅ 403 textos (`menus_test.sh`) |
| `OVL/PRM`, `SNMP`, `TITL` | `menus` (reempaquetado) | 0.10, 0.11 | cp04, boot | mapa, combate, título | ✅ (`menus_test.sh`); quedan encabezados de columna y abreviaturas |
| `OVL/BTL`, `SNDU`, `ENTR`, `COMM` | `menus`, `entry` | 0.10, 0.11 | prologo, cp04 | combate, ingreso de datos | ✅ combate; ✅ ingreso de datos (#16, #57, 2026-09-28) |
| Gráficos (títulos, prólogo, texturas, `UNIT.BIN`) | `graphics` ⏳ | — | — | prólogo, mapa, combate | ⏳ |
| Imagen (FS, `.cue`) | `iso`, `verify` | 0.12–0.14 | boot | FMV, audio, cargas | ✅ rebuild idéntico; archivos que crecen ✅ |

## 7. Checkpoints y grabaciones a pedir en la desktop

Hoy no hay ruta automática para esto (nombres sugeridos según `saves/LEEME.md`):

| Sugerido | Qué grabar | Para |
|---|---|---|
| `CP13-MAP-…-suspender` | desde una card MAP: CONTINUE → menú del mapa → 中断 → pantalla de despedida | EM.BIN |
| `CP14-BAT-…-derribo` | ataque que derribe a un piloto enemigo con nombre (frase de derribo) | DEADMESS.BIN |
| `CP15-BAT-…-show` | combate con Show Zama (bloque BXCLIST 149, el más grande) | memoria de batalla |
| `CP16-INT-…-diccionario` | intermisión o título → diccionario de personajes y de robots, recorrer unas fichas | DC/DR |
| `CP17-INT-…-guardar` | intermisión → セーブ → reset → LOAD | guardado/carga |
| grabación de CP11 | CONTINUE → ○, ↓, ○ (lista de armas del Eva-02) | ROBOT.RAF (nombres) |
| `CP18-MAP-…-inicio` | justo antes de empezar un escenario (sin 中断) para ver el título del escenario | SUBTITLE.BIN |
| card cerca del final | un escenario final que cargue (la CP10 no carga) | END, FMV de final |

## 8. Síntomas → causa probable

| Síntoma | Causa probable | Dónde mirar |
|---|---|---|
| Pantalla negra al bootear / vuelve a la BIOS | EXE mal parcheado, área de sistema o `SYSTEM.CNF` | N0 0.8 y 0.12; comparar con `build.sh --null` |
| "ロード中です" sin fin / cuelgue al cambiar de pantalla | archivo no encontrado o corrupto; overlay más grande que su zona | `verify.json`; tamaños en `manifest.json` |
| Texto cortado a la derecha | línea de más de 240 px | `check_text.csv` (`px`) |
| Una 4.ª línea fuera de la caja | más de 3 líneas | `check_text.csv` (`lines`) |
| Glifo raro (Mk-II, ν, ヱ) en medio de una palabra | ﾞ/ﾟ (0xDE/0xDF) detrás de un carácter | `check_text.csv` (`marker`) |
| Espacios anchos o con basura | espacio 0x20 en vez de 0xA0 | la herramienta del formato |
| Números desalineados en menús | glifos de dígitos o del 0x20 tocados en la fuente | `font/en_8px.txt` (`keep`) |
| Basura o textos cruzados en un menú | puntero reubicado mal (falso positivo) o in situ que pisó un dato | `menus/report.csv` (dirección vieja → nueva), `logs/menus.log` |
| Cuelgue en combate | bloque de BXCLIST demasiado grande | `AVISO` de `bxclist` en el log |
| Nombres cortados | campos fijos: piloto 20/12 B, unidad 21 B, arma 19 B | `pilot_bin` / `units_en.csv` / `weapons_review.csv` |
| Diccionario con basura | DC/DR mal reempaquetado | etapas `dc`/`dr` |
| La ruta automática se desfasa | cambió el tiempo del texto en lo que recorre | regrabar en la desktop |
| FMV o audio que no suena | XA/STR movidos o dañados | `verify.json` (XA/STR) |

## 9. Registro por build

Copiar una fila por build revisada (`OK` / `FALLA` / `—` no corrido):

| Build | Fecha | Commit | N0 | N1 | N2 | N3 | Notas |
|---|---|---|---|---|---|---|---|
| | | | | | | | |
