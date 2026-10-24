# Compresión de ROBOT.RAF, DC.BIN y DR.BIN — 2026-09-27

**Resuelto: los tres archivos usan el mismo LZSS (estilo Okumura).** Herramienta: `tools/src/robot_raf.py`
(`lzss()` se reutiliza para DC/DR). Volcado de unidades y armas: `dump/robot.jsonl`.

## Cómo se descubrió
Durante la batalla del prólogo, un volcado de RAM (`DUMP_RAM`) tenía el registro de Excelion **ya descomprimido**
en `0x80138234` (nombre `ﾏﾟｸｾﾘｦﾝ` + 4 armas: 対空ﾊﾟﾙｽﾚｰｻﾞｰ砲, 光子魚雷, 中口径光線砲, 紅玉式光線主砲). Buscando fragmentos
de ese registro en `ROBOT.RAF` apareció la entrada 342 con el nombre literal tras un byte `ff`: flags LZSS.

## Algoritmo
- Byte de banderas cada 8 elementos, **LSB primero**: bit 1 = byte literal; bit 0 = referencia de 2 bytes.
- Referencia `b1 b2`: posición en el anillo = `b1 | (b2 & 0xF0) << 4`; largo = `(b2 & 0x0F) + 3` (3..18).
- Anillo de 4096 bytes inicializado en **cero**, se escribe desde **4078** (`N − F`, F = 18).
- Validación: la salida coincide byte a byte con la RAM salvo (a) el orden de los registros de arma, que el juego
  reordena en memoria, y (b) un bit de estado (`c0`→`e0`) en +71. Las 486 entradas de ROBOT.RAF dan exactamente el
  tamaño declarado; DC 350/351 y DR 449/450 (la restante es una entrada vacía).
- **Compresor** (`lzss_compress`, `pack_entry`, `build_raf` en `robot_raf.py`): voraz con cadenas de hash, solo copias
  desde bytes ya escritos. Ida y vuelta exacta en ROBOT 486/486, DC 350/350, DR 449/449. Sale ~3% más grande que el
  original (no aprovecha los ceros iniciales del anillo); el ISO se reconstruye con mkpsxiso, así que el tamaño no es
  un límite. `robot_raf.py --repack salida.RAF` recomprime todo sin cambios (prueba en el juego: ver `README.md`).

## Contenedores
| Archivo | Tabla | Entrada |
|---|---|---|
| `UNITPRAM/ROBOT.RAF` | `u32 n` (486) + `u32 offset[n]` relativos al fin de la tabla | `u32 tamaño descomprimido`, `u32 0`, datos LZSS |
| `OPTION/DC.BIN` | `u32 offset[n]` **absolutos**; el primero = tamaño de la tabla (351 entradas) | igual |
| `OPTION/DR.BIN` | igual que DC (450 entradas) | igual |

## Registros descomprimidos
- **ROBOT.RAF** (unidad): +0 nombre en kana de medio ancho (NUL) … armas desde **+0x44**, registros de **0x28**:
  `+0` índice (0..n−1) · `+2` u16 ? · `+4` u16 potencia · `+6` u16 tipo/flags · `+8` nombre (SJIS + kana de medio ancho, NUL).
  2.589 registros de arma, **686 nombres únicos** (sin contar `ﾀﾞﾐｰ` = relleno). Ya están en el glosario (`weapon`).
- **DC** (personaje): nombre completo, nombre corto, serie, actor de voz, biografía. **DR** (robot): nombre, altura,
  peso, serie, descripción. Campos de **ancho fijo rellenos con `0xCD`** (se ven como `ﾍﾍﾍ`). La entrada 0 de cada uno
  es un índice con todos los nombres.

## Observaciones
- Pares `kana + ﾟ` en nombres (`ﾔﾟﾕﾟﾚﾟ` en "ガンダムMk-II", `ﾏﾟ` en "ヱクセリヲン"): probablemente **glifos especiales**
  de la fuente (Mk-II, ヱ…). Sin verificar; importa al traducir nombres de unidades.
- Nombres de unidad y arma en kana de medio ancho → campos de bytes fijos: los nombres ingleses deben respetar el largo.
