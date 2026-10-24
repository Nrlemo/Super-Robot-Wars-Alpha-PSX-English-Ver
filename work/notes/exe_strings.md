# EXE (`SLPS_026.36`): inventario de strings para la etapa `exe_strings` — 2026-10-03

Investigación para #12 (etapa `exe_strings` de `build_all.py`, hoy `pendiente`). Fuentes: `work/dump/ovl_strings.jsonl`
(filas `file: EXE`, 3.123 candidatos, casi todos falsos positivos de código) y diff byte a byte
`work/iso_jp/SLPS_026.36` vs `work/iso_chs/SLPS_026.36` (mismo tamaño, 315.392 B).

## Hallazgos

1. **Solo hay 2 strings del EXE que ve el jugador**: los títulos de la partida guardada (los muestra la BIOS en el
   administrador de memory card, con su fuente SJIS; no pasan por el VWF).

   | VA | bytes | lugar | refs | texto |
   |---|---|---|---|---|
   | `0x800100F0` | 44 | 47 | 1 | `スーパーロボット大戦アルファ　システムデータ` |
   | `0x80010120` | 46 | 47 | 2 | `スーパーロボット大戦アルファ　シナリオデータ%s` (el `%s` es el número de slot) |

2. **Otros 8 strings con japonés son `printf` de depuración** (`0x800105EC`–`0x800108AC`: "ループが…", "消音失敗",
   "ファイルオープンに失敗しました", "これはTIMではありません"…). No se ven en el juego: **no traducir**.
3. **El diff con el parche chino confirma el alcance**: cambia exactamente los 2 títulos de guardado y la tabla de
   nombres de `0x800522FC` (paso 0x48, kana de medio ancho + kanji: ﾌﾞﾙｯｸﾘﾝ/ﾗｯｸﾌｨｰﾙﾄﾞ/ﾌﾞﾘｯﾄ…, 諒斗/氷川, 樟葉/水羽 y el
   productor 寺田 貴信 / Tﾌﾟﾛﾃﾞｭｰｻｰ). Nada más del EXE tiene texto visible.
4. Esa tabla es la de **nombres especiales** (ver `nombres_protagonistas.md`, #56): la de nombres por defecto que ve el
   jugador vive en `ENTR_GRP` y ya la reemplaza la etapa `entry`. Traducirla solo importa si queremos que los
   nombres especiales disparen su efecto con nombres en inglés.
5. **El botón はい del diálogo "No system file. Create one?" no está en el EXE** (no aparece `はい` en SJIS en todo el
   archivo): queda buscarlo en los overlays (`ovl_strings.jsonl`) o en los gráficos (`WINTEX`/`FONTWIN`).

## Propuesta para la etapa `exe_strings`

- Reemplazo **in situ** (hay lugar: 47 B cada uno), encadenado sobre la salida de `exe`, y sumar
  `0x800100F0–0x8001011E` y `0x80010120–0x8001014E` a `EXE_WINDOWS`.
- Texto en **SJIS de ancho completo** (la BIOS no tiene VWF; ASCII simple puede verse raro según la BIOS), ej.:
  `ＳＲＷ　Ａｌｐｈａ　Ｓｙｓｔｅｍ` (40 B) y `ＳＲＷ　Ａｌｐｈａ　Ｓｃｅｎａｒｉｏ%s` (≤ 46 B). Decisión pendiente (#12).
- No tocar el nombre de archivo de la card (`SRWAx`/`SRSYS`) para que las partidas japonesas sigan cargando.
- Probar en el menú de memory card de la BIOS (DuckStation y Redux) booteando desde cero.
