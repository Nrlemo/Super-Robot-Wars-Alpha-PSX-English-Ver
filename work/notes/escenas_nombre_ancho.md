# Escenas: el apodo (`$n`, `$l`) sale con la fuente ancha original — investigación (#224)

2026-10-01. Estado: **causa localizada a medias**; falta saber quién escribe la tabla de nombres.

## Síntoma
En escenas (SCRIPT.BIN) la etiqueta del hablante protagonista/pareja se ve `B u l l e t:` (avance 12 px, glifos del 12F);
el resto de los hablantes ("Tashiro: …") y el texto de la línea salen con la VWF. Captura de la maintainer + reproducido
en headless con `saves/cards/CP14-INT-E01-decision-bullet.rec.txt` (card virgen, ~cuadro 24000–33000, build `todo_v05`).

## Hallazgos (RAM en el cuadro 24000 y 33000)
- El nombre guardado está bien: `Bullet` en **ASCII** en `0x8006E936`.
- La línea de la escena ya llega expandida a los búferes de texto (`0x8015FFB6`, `0x80162BAC`) como
  `82 61 82 95 82 8C 82 8C 82 85 82 94 | 3A A0 45 69 74 68 65 72 …` = **"Ｂｕｌｌｅｔ" en SJIS de ancho completo** + `:` + inglés
  ASCII. Por eso el maquetador (`FUN_80018CC4`) lo dibuja con glifos de 12 px.
- Existe una **tabla de cadenas de ancho completo** en `0x801601C2…` ("Ｂｕｌｌｅｔ", "Ｂｒｏｏｋｌｙｎ＝Ｌｕｃｋｆｉｅｌｄ",
  "Ｋｕｓｕｈａ", "Ｋｕｓｕｈａ＝Ｍｉｚｕｈａ"…), intercaladas con datos de 4 bpp. Las lee la expansión de `$n/$l`.
- El overlay residente en `0x800D61D8` durante la escena es **`SNDM_GRP`** (el motor de escenas; no solo el diccionario).
- No hay conversión ASCII→ancho completo por constantes (`0x8260`, `+0x1F/+0x20` con `0x82`) ni por tabla `8140 8149 8168…`
  en el EXE ni en los overlays (solo `ENTR_GRP 0x8294`, el teclado del editor de nombres).
- Esa tabla **no existe como texto en ningún archivo** del disco (JP ni `todo_v05`) → se genera en ejecución.
- `COMM_GRP`/`SNMP_GRP` leen `*0x8005C248/C24C` (protagonista/pareja), pero eso es retrato (`+0x43/+0x45`) y el
  expansor del mapa; el de escenas sigue sin ubicar (#56).

## Cómo se investigó (trampas)
- Los breakpoints de memoria **solo funcionan con `-interpreter -debugger`**, y `EMU_FLAGS` debe ir como **variable de
  entorno**: `EMU_FLAGS="-interpreter -debugger" bash work/tools/drive.sh …`. Pasarla como argumento `EMU_FLAGS=…` no tiene
  efecto (el script la lee del entorno) y el emulador queda en dynarec: los BP no disparan y no hay error.
- Con `BP_FROM` bajo, los primeros cientos de aciertos son la limpieza de RAM del arranque (cuadro ~30, `pc=801C45A8`):
  usar `BP_FROM=2000`.
- Dirección con rango (`BP_WRITE=0x801601C0:64`) se parte en bloques alineados de 4 bytes.
- `drive.sh` busca `CARD=`/`INPUTS_FILE=` relativas al directorio del emulador: pasar rutas absolutas.

## Intentos con breakpoints (resultado, 2026-10-01)
| Corrida | Qué se probó | Resultado |
|---|---|---|
| dynarec, `BP_EXEC`/`BP_READ`/`BP_WRITE` | maquetador, apodo, tabla | **0 aciertos**: el dynarec no dispara BP de memoria (ni de ejecución en este caso) |
| intérprete, `BP_WRITE 0x801601C0:64`, `BP_FROM=1` | quién escribe la tabla | 100 aciertos, todos limpieza de RAM del arranque (cuadro 30, `pc=801C45A8`) |
| ídem, `BP_FROM=2000` | idem | 264 aciertos: bucle genérico `pc=80040AD0` (cuadros 2314–2547) e **init de objetos de sprite** `pc=800E1D68…800E1E74` (`SNDM_GRP`, cuadro 4471). **Después no hay más escrituras de CPU** aunque el nombre aparece luego → esa tabla entra por **DMA** (CD u otra) o la escribe otro rango; no es el expansor |
| intérprete hasta el cuadro 24000/34000 | línea de texto `0x8015FFB4`, tabla | 0 aciertos: **el intérprete va muy por detrás del dynarec** (cuadro 33000 todavía en el texto del prólogo) y la grabación de entradas (por cuadro) se desincroniza. Con intérprete no sirve reproducir la grabación completa |

| dynarec → `SAVE_STATE` en el cuadro 24000 (21 MB) → intérprete con `LOAD_STATE` + `INPUTS="120:CROSS;…"` + BP en líneas y tabla | observar el expansor desde la escena | **el emulador sale sin capturas ni log al cargar el estado** (los states nuevos rompen el emulador en este entorno; ya anotado en `saves/LEEME.md`). Método descartado |

Conclusión: ni la grabación completa ni los estados sirven con el intérprete. Opciones que quedan: (a) **análisis estático en
Ghidra de `SNDM_GRP`** (base `0x800D61D8`; ya hay proyecto en `work/ghidra_proj` del checkout principal) buscando el código
que copia la línea de SCRIPT al búfer (`0x8015FFB4`/`0x80162BAC`) y el que arma la tabla `0x801601C2`; (b) sesión
interactiva en la desktop con la ventana de PCSX-Redux y su depurador (BP de escritura a mano sobre `0x8015FFB6` con la
decisión de Bullet en pantalla); (c) hacer sincronizar la grabación con el intérprete (hoy a 33000 sigue en el prólogo).

## CAUSA ENCONTRADA (2026-10-01, sesión con depurador en la desktop + análisis estático de `SNDM_GRP`)
Base del overlay `SNDM_GRP` = `0x800D61D8` (dirección = base + offset de archivo). La estructura de la escena está en
`0x8015FF9A` (`s0`/`s3`/`s7` en el código); el búfer de línea es `+0x1A` (256 B) y los nombres `+0x226` (`$n`), `+0x246` (`$N`)…
- **Inicio de escena** `0x800DB880` (file `0x5880`): para el protagonista (`*(s1+4)`) y la pareja (`*(s1+8)`) llama **seis
  veces** a `0x800DB860` (file `0x5688`) con las fuentes `+0x00` (nombre), `+0x15` (apellido), `+0x2A` (apodo) y deja el
  resultado en búferes de pila; arma "nombre＝apellido" (`0x800D65C8`, orden según `+0x47`) y llama a
  `0x800DBD78` (file `0x5BA0`), que con `strcpy` (`0x8002140C`) los guarda en `+0x226…`.
- **`0x800DB860` (file `0x5688`) es el conversor media anchura → ancho completo**: bytes SJIS (`0x81–0x9F`, `0xE0–0xFC`) pasan
  tal cual; el resto se busca en una **tabla de 0x9E entradas** (claves en `0x800F0780`, salidas de 2 bytes en `0x800F0508`) y
  se escriben 2 bytes (`A`→`Ａ`, `=`→`＝`, espacio→`8140`, kana media anchura→kana). La tabla trae 68 entradas ASCII y **no
  trae `0xA0`** (nuestro espacio). Por eso el apodo ASCII sale en ancho completo (12 px, "B u l l e t").
- El expansor de `$n/$N…` está en `0x800DC3E8` (file `0x6210`): compara con patrones de 2 bytes en `0x800D6A24…` y copia desde
  `s3+0x226/0x246…` (los nombres ya convertidos). **No hace falta tocarlo.**
- Las escrituras de CPU no aparecían en las corridas anteriores porque el intérprete aún no había llegado a la escena (ver tabla).

### Arreglo propuesto (a confirmar con el mantenedor)
Dos instrucciones al inicio de `0x800DB860` (file `0x5688`): convertir el ayudante en un `strcpy(dst=a2, src=a1)` de cola:
`j 0x8002140C` / `move $a0,$a2`. El texto SJIS (kana/kanji tecleados) se copia igual; el ASCII y el `0xA0` quedan en 1 byte y la
VWF los dibuja. Con eso `$n`, `$N`, `$l`… y los nombres completos salen con la fuente inglesa. Seguimiento menor (#56): el
separador `＝` (`0x800D65C8`) pasa a espacio `0xA0` y el orden `+0x47`, como en `SNMP_GRP`.
Verificación: reproducir `CP14-INT-E01-decision-bullet.rec.txt` en headless con el dynarec (llega a la decisión) y mirar la captura.

## IMPLEMENTADO Y VERIFICADO (2026-10-03, build `todo_v06_v01`)
`entry_patch.py` (etapa `entry`, ahora también `SNDM`): `0x800DB860` → `j strcpy`/`move a0,a2` y separador `＝` (`0x800D65C8`) → `0xA0`. Replay headless de `CP14-INT-E01-decision-bullet.rec.txt` (dynarec, `FRESH_CARD=1`): cuadro 33500 muestra **`Bullet: W-What do I do…?`** con la VWF (captura `docs/capturas/224-bullet-vwf-todo_v06_v01.png`). Falta que el mantenedor lo vea en otra escena (pareja `$l`, apellido, orden `+0x47`). Los números no mostraron el problema (8 px fijos a propósito).

## Pendiente (histórico, antes del arreglo)
- [ ] Ver qué `pc`/`ra` escribe `0x801601C0…` (corrida `BP_WRITE`, `BP_FROM=2000`) → rutina que convierte/copia los nombres.
- [ ] Decidir el arreglo: parchear esa rutina (copiar ASCII sin convertir) o escribir la tabla en ASCII/medio ancho y revisar
      que la VWF dibuje `$n`, `$l`, `$L`, `$f` con avance de la tabla de anchos.
- [ ] Confirmar si pasa también con los números (los dígitos van a 8 px fijos a propósito, R3).
