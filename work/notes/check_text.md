# Validador de traducciones `check_text.py` — 2026-09-27

Un solo validador para el campo `"en"` de **todos** los volcados de texto. Mide cada línea en píxeles como el
maquetador del juego (`FUN_80018CC4` + parche VWF) y controla los límites de cada formato.
Herramienta: `tools/src/check_text.py` · pruebas: `tools/src/test_check_text.py`.

## Uso

```bash
cd work
# validar todo (dump/*.jsonl) → resumen en pantalla + build/check_text.csv; código de salida 1 si hay errores
python3 tools/src/check_text.py
# solo algunos formatos, o un JSONL de traducción que no está en dump/
python3 tools/src/check_text.py --only snmsg,bxclist --input dc=translation/dc_en.jsonl
# además, proponer saltos de línea para las filas con problemas de ancho o de líneas
python3 tools/src/check_text.py --wrap build/wrap_propuestas.jsonl [--keep-breaks]
# probar un texto suelto (muestra el ancho de cada línea propuesta)
python3 tools/src/check_text.py --wrap-text 'Tashiro: Number One! How many of our ships survived?' --format snmsg
# pruebas unitarias (16 casos con líneas sintéticas)
cd tools/src && python3 -m unittest test_check_text
```

No necesita numpy ni la ISO: solo `sjis_text.py` y la fuente.

## Qué controla

| Control | Tipo (`kind`) | Detalle |
|---|---|---|
| Codificación | `encoding` | cp932; espacio → `0xA0`, `\n` → `0x0A`, escapes `{XX}`. Caracteres sin Shift-JIS (`é`, `—`…) = error. |
| Bytes | `bytes` | texto codificado sin el NUL, contra el tope del formato. |
| Líneas | `lines` | cantidad de `\n` + 1. |
| Ancho | `px` | por línea: byte simple → tabla VWF; SJIS → 12 px (hiragana/katakana → `kana_px`); `$n`/`$N`/`$l` → 48 px, `$m`/`$M`/`$s`/`$S` → 60 px, `$f`/`$F`/`$L` → 120 px (`VAR_PX`, ver `nombres_protagonistas.md`). |
| Variables | `placeholder` | el multiconjunto de `$n $N $f $F $m $M $s $S $l $L` tiene que ser igual al de `"jp"`. |
| Glifos especiales | `marker` | `0xDE`/`0xDF` (ﾞ/ﾟ) sueltos detrás de un carácter: el motor los consume como marca de glifo especial (`pilot_bin.md`). No cuenta el 2.º byte de un kanji. |
| Espacios | `spaces` (aviso) | espacios dobles o al principio/final (gastan píxeles). |

**Severidad**: `error` si el límite está verificado (formato del archivo o medido en el juego); `warn` si es un
supuesto. En el resumen los avisos llevan `?` (p. ej. `px:12?`).

**Tabla de anchos**: usa `patches/vwf_table.bin` si existe. Como `*.bin` está en `.gitignore`, en las sesiones de la
nube no está: entonces la calcula desde `font/en_8px.txt` con la misma regla que `font_build.py` (ancho del dibujo + 1,
`adv=N`, `keep` = 8 px). La primera línea del resumen dice cuál se usó. Comprobado: *"The EOT fleet we built is being
torn apart"* = **175 px**, igual que en `fuente_en.md`.

## Límites (editables en `FORMATS`, al principio del script)

| Formato | Bytes | Líneas | Ancho | `kana_px` | Supuestos |
|---|---|---|---|---|---|
| `snmsg` | 255 (slot de 256) | 3 | 240 | 8 | ninguno (medido en `poc_snmsg.md`) |
| `script` | libre | 3 | **272** | 8 | ninguno (medido, #31: parte sola por carácter > 272 px; renglón 4+ se pierde) |
| `bxclist` | libre | 2 | 240 − 「」 | 8 | ninguno (medido, #31: el juego agrega 「 y 」, 12 px c/u; renglón 3 cae fuera de la caja) |
| `deadmess` | 251 (252 con NUL) | 3 | 240 − nombre「」 | 8 | ninguno (medido, `deadmess_em.md`) |
| `em` | 255 (256 con NUL) | 3 | 240 | 8 | ninguno (medido, `deadmess_em.md`) |
| `dc` / `dr` | campo − 1 (`option_dict.LAYOUT`); línea e índice 46 | 2 por campo | 264 | 12 | ninguno (layout confirmado y probado, #15) |

- **SCRIPT y BXCLIST**: el largo es libre porque `script_bin.py` y `bxclist.py` rehacen tamaños y punteros.
  Medidos en el emulador (#31, `tools/formato_test.sh ancho` y `tools/ancho_test.sh bx`): escena 3×272 px; batalla
  2×240 px con `「`/`」` que agrega el juego. En los dos casos el juego **parte solo por carácter** al pasar el ancho
  (cortaría palabras y correría renglones): el validador lo marca como error.
- **Dato a favor de `kana_px=8` en escenas y batalla**: midiendo el japonés original con kana a 12 px, 2.160 líneas
  de SCRIPT y 302 de BXCLIST pasarían de 240 px; con 8 px quedan 14 y 0. Las 14 de SCRIPT tienen `$n`/`$l`, que el
  validador reserva a 48 px (un nombre japonés ocupa menos). Es consistente con que usen la misma caja que el mapa.
- **DC/DR**: el volcado no trae `"en"`; el validador acepta `"en"` como lista paralela a `"fields"`
  (formato de `translation/dc_en.jsonl`) o un `"en"` dentro de cada campo. Cada campo es una fila con id
  `entrada@offset`. El tope de bytes sale del layout real (`option_dict.LAYOUT`). Ancho: la caja deja ~270 px (46 letras ≈ 210).
- **EM**: pantalla propia; se desconoce el ancho (el japonés llega a 56 bytes por renglón).

## Salidas

- **CSV** (`build/check_text.csv` por defecto): `format, id, kind, severity, line, value, limit, detail, en`.
  Ids: SNMSG `id`; SCRIPT `script/inst`; BXCLIST `pilot/idx`; DEADMESS `slot`; EM `rec`; DC/DR `id@off`.
- **Resumen** en pantalla: filas, traducidas, errores, avisos y conteo por tipo.
- **`--wrap`** (JSONL): para cada fila con problemas de ancho o de líneas, `en`, `en_wrapped`, `lines`, `fits`.
  Algoritmo codicioso por palabra con el ancho real en px; por defecto re-fluye todo el texto (une los `\n`);
  con `--keep-breaks` respeta los saltos existentes y solo parte las líneas largas. Una palabra más ancha que la
  caja se corta por caracteres. **Es una propuesta**: no toca el volcado; revisar los cortes (nombre del hablante,
  sangría) antes de copiarlos.

## Prueba sobre los volcados

Hoy ningún volcado tiene `"en"` (0 filas traducidas, 0 violaciones). Para probar el recorrido completo se corrió con
el japonés copiado en `"en"`: se leen los 7 formatos (32.544 + 45.363 + 18.128 + 544 + 30 + 5.036 + 5.562 filas) y
aparecen los casos esperados, p. ej. 383 marcas `ﾔﾟﾕﾟﾚﾟ` ("Mk-II") en SNMSG como `marker`.

## Pendiente / incierto

1. ~~Medir ventanas~~ ✅ 2026-09-28 (#31): SCRIPT 3×272, BXCLIST 2×240 con 「」, DEADMESS/EM (antes), DC/DR (#15).
   Ningún formato queda con límites `assumed`.
2. ~~Reserva de nombres~~ ✅ 2026-09-28: `VAR_PX` por variable según los topes aprobados (apodo 8, nombre 9, apellido 10;
   `nombres_protagonistas.md`). Si la pantalla de ingreso termina con otros topes, ajustar `VAR_PX` aquí y en `snmsg.py`.
3. ~~Layout de DC/DR~~ ✅ 2026-09-28 (#15, `diccionarios_traduccion.md`).
4. ~~Formato del hablante~~ ✅ 2026-09-28 (#23): `Nombre: texto` probado en el emulador. SNMSG y SCRIPT avisan
   (`speaker`) si una línea con hablante japonés (`X「`, `X（`) no empieza con `Nombre: `, lleva `「」（）` o tiene
   sangría en los renglones 2–3.
