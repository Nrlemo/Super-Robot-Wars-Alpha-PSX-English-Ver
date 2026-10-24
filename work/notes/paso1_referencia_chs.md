# Paso 1 — Referencia del parche chino (CHS v2.0) — 2026-09-27

## Cómo se reproduce
```bash
source work/tools/env.sh
# 1. Aplicar el PPF a una COPIA (valida tamaño y bloque PPF; se niega a parchear in-place)
$SRW_PY work/tools/src/ppf_apply.py "Super Robot Taisen Alpha (Japan) (v1.0).bin" Utils/SRT_Alpha/SLPS_025.28 work/build/chs.bin
# 2. Extraer archivos CHS usando el layout de la ISO JP (el directorio CHS está corrupto, ver abajo)
$SRW_PY work/tools/src/isofs.py extract work/build/chs.bin work/iso_chs --layout-from "Super Robot Taisen Alpha (Japan) (v1.0).bin"
# 3. Diff clasificado por archivo → notes/diff_jp_chs.md + analysis/diff_runs.json
$SRW_PY work/tools/src/diff_files.py work/iso_jp work/iso_chs work/notes/diff_jp_chs.md work/analysis/diff_runs.json
```
El extractor propio (`isofs.py`) fue validado contra dumpsxiso: 0 diferencias en los 104 archivos de datos.

## Hallazgos confirmados

### Cómo el juego localiza archivos
- Por **nombre en el ISO9660** (`CdSearchFile` con rutas `\SNMAP\SNMSG.BIN;1` en el EXE y en los overlays). No hay tabla de LBAs propia en el EXE.
- ⇒ Reconstruir con **mkpsxiso** (FS consistente) permite que los archivos cambien de tamaño/posición sin parchear código. El round-trip ya es byte-idéntico.

### El parche chino NO tiene hacks de código
- `SLPS_026.36`: 202 bytes cambiados, todos texto (título de guardado, nombres por defecto en kana medio ancho).
- Overlays `OVL/*_GRP.BIN`: solo strings de menú reemplazados in-place.
- **La fuente `12F.DAT` no fue modificada**: escribieron chino con los kanji que ya existen en la fuente japonesa, codificados en SJIS. ⇒ El texto CHS se decodifica como SJIS: **corpus paralelo JP/CHS alineado**, útil como referencia secundaria de sentido.
- ⇒ No hay nada que reutilizar para el problema del ancho de fuente en inglés (VWF / medio ancho): eso es trabajo nuestro.

### Archivos de texto y su formato
| Archivo | Formato | Estado en CHS | Notas para EN |
|---|---|---|---|
| `SNMAP/SNMSG.BIN` | **32.544 slots fijos de 256 bytes**, SJIS, relleno `00`. Sin punteros (índice = nº de slot). | Traducido in-place | 255 bytes útiles por mensaje. Máx. JP actual: 134 bytes, 3 líneas. |
| `BUSTUP/SCRIPT.BIN` | Tabla de 255 offsets u32 → scripts de intermisión: **bytecode + args ASCII + texto SJIS inline** | **Sin traducir in-place** (solo 13 KB) | El archivo más difícil: hay que decodificar el bytecode para poder cambiar largos de texto. |
| `BATTLE/BXCLIST.BIN` | Tabla de 2048 entradas (sin usar = `0xCDCDCDCD`) → frases de batalla | **Sin tocar** | Diálogos de combate (`くらえ` ×321, `当たれ` ×130). |
| `SNMAP/DEADMESS.BIN` | Frases de derribo SJIS | Traducido in-place | |
| `SNMAP/EM.BIN` | Texto de eventos de mapa | Traducido in-place | |
| `UNITPRAM/PILOT.BIN` | Nombres SJIS + lectura en kana medio ancho | Modificado | |
| `OPTION/DC.BIN`, `OPTION/DR.BIN`, `UNITPRAM/ROBOT.RAF` | **Tabla de offsets + entradas comprimidas** (entropía ~6,8) | **Re-comprimidos** (tamaños distintos) | DC = diccionario de personajes (351 entradas), DR = de robots (450), ROBOT.RAF = datos de unidades/armas (486). **Hay que identificar el algoritmo de compresión.** |
| `OVL/*_GRP.BIN`, `SLPS_026.36` | Strings de menú de largo fijo embebidos en código | Traducidos in-place | Espacio fijo; alargar implica mover strings y repuntar en código MIPS. |

### Códigos de control en SNMSG
- `0x0A` salto de línea (máx. 3 líneas por mensaje).
- `$n` (8.033 usos), `$N` (1.971), `$F` (33), `$f` (26): variables (probable: nombre del protagonista, de la pareja/rival y su apellido; **a confirmar en el emulador**).
- Kana de medio ancho con `ﾟ` (ej. `ﾔﾟﾕﾟﾚﾟ`): glifos especiales (probable nombre de unidad dibujado con glifos propios; **a confirmar**).
- Línea típica: 14–16 caracteres full-width; máx. ~22 con el nombre del hablante (`タシロ「…`).
- 256 slots "Dummy String" sin uso.

### Gráficos con texto modificados por CHS
`TITLE/SUBTITLE.BIN` y `ENTRYDAT.BIN` (títulos de escenario), `FONTWIN/WINTEX.BIN`, `WINDOW.TIM`, `TITLEDAT.BIN`, `WINDATA*.DAT`, `TEST/TXT3x.TIM` + `PRO_FONT.TIM` (prólogo; los usa `PRO_GRP`), `ANMTST/EFETES.TIM`, `BATTLE/BATTLE.WAC`, `BUSTUP/CHARA.BIN` (113 KB), `BATTLE/UNIT.BIN` (392 KB, probablemente nombres de ataque gráficos), `AI/AIUNP.BIN`.

## Rarezas del parche chino (incertidumbre explícita)
1. **Texto escrito sobre sectores de directorio**: los sectores de directorio de `ANMTST/` (LBA 2924) y `BATTLE/` (LBA 2944) quedan pisados con texto, y la cabecera y gran parte de `BGDATA.BIN` también (~2 MB).
2. Ese texto es **la traducción china de SCRIPT.BIN** (Quattro, Astonaige, Titans…), escrita en el rango LBA 2924–~4420.
3. **No hay cambios de código ni de rutas** que expliquen cómo el juego chino cargaría el script desde ahí. Además, con el directorio `BATTLE/` destruido, `CdSearchFile("\BATTLE\…")` debería fallar.
4. Hipótesis sin confirmar: (a) su PPF se generó contra un volcado JP con otro orden de archivos; (b) su imagen tiene bugs que no se manifiestan en ciertos emuladores; (c) hay algún mecanismo de caché que no vi.
   **Prueba pendiente**: bootear `work/build/chs.bin` en DuckStation, llegar a la primera intermisión y a la primera batalla, y ver si funciona.
   **No bloquea** nuestro camino: reconstruimos con mkpsxiso y un FS consistente.

## Consecuencias para el plan
- SNMSG: extracción/reinserción trivial (slots fijos). Es el grueso del texto (~32 k mensajes).
- SCRIPT.BIN: requiere ingeniería inversa del bytecode (saltos/offsets internos) antes de poder reinsertar texto de otro largo.
- DC/DR/ROBOT.RAF: identificar la compresión (probable LZSS o variante) — prioridad media-alta porque ROBOT.RAF tiene los nombres de armas/ataques.
- BXCLIST: formato por investigar; el chino no ayuda.
- Fuente/ancho de línea: sigue siendo el problema central; el chino no aporta nada ahí.
