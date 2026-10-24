# Overlays pendientes de #11: qué son (2026-10-04)

Análisis hecho **sin ISO**, sobre el inventario versionado `dump/ovl_strings.jsonl` (lo genera `ovl_strings.py` desde
`work/iso_jp/`). Extractor de END: `tools/src/end_credits.py` → `dump/end_credits.csv`.

**Decisión C8 (2026-10-04): los créditos quedan en japonés; `END` no se modifica** (`traduccion/DECISIONES_PENDIENTES.md`).
Las flechas de COMA siguen en #275. Lo de abajo queda como referencia si algún día se retoma.

## Veredicto por overlay

| Overlay | Zona | Candidatos | Texto real | Qué es |
|---|---|---:|---:|---|
| **END** | A `0x800D61D8` | 675 | **472** | **Créditos finales** (staff roll). Las otras 203 filas son bytes de código (desde 0x3100). |
| COMA | B `0x800FF190` | 864 | 9 + 4 | IA del enemigo ("COM AI"): 9 `printf` de depuración (`%s<%d> … ＡＩターン開始`, `移動思考で決定`) → **no traducir** (igual que los del EXE, `exe_strings.md`). 4 strings 上/右/下/左 en una tabla de punteros propia (`0x800FF5E8`, offset 0x458) → **sin verificar** si se ven o solo alimentan los logs (#275). |
| PRO | A | 133 | 0 | Prólogo: el texto es gráfico (`TEST/TXT30–33.TIM`, `PRO_FONT.TIM`; #19 cerrado, `graficos.md`). Las filas son código. |
| MPWP | C `0x8011308C` | 84 | 0 | Todo código (cero `refs`, patrones `ｿｯ`/`ｾｯ` = `sw $ra/$s*, n($sp)`). Probablemente animación de armas MAP (MaP WeaPon) — **hipótesis**, no verificada. |
| MOVE | C | 81 | 0 | Todo código, igual que MPWP. Función no identificada (¿movimiento de unidades o película?). |

Clasificación: un string es "texto real" si tiene referencia (`ptr`/`code`) o si es ≥ 70 % kana/kanji de ancho completo
con algún kana y casi sin símbolos sueltos; ninguna fila sin referencia de COMA/PRO/MPWP/MOVE pasó ese filtro.

## END: estructura

- **Bloque de texto** `0x0004–0x30BC` (11.704 B con los NUL), strings alineados a 4 bytes.
- **Tabla de créditos** desde el offset `0x5C0C` hasta `0x6AFC`: 479 entradas de **8 bytes** (puntero + 4 bytes que no
  se conocen sin el binario: probablemente posición/espera/estilo). El orden de la tabla es el orden en pantalla; casi
  siempre sigue al del texto, pero hay saltos y **reusos** (寺田 貴信 aparece 3 veces: productor, bloque final y
  脚本・総監督; じっぱひとからげ y 杉浦 俊朗, 2 veces). Columna `orden` del CSV = índice de entrada en la tabla.
- **Todos** los strings tienen referencia `ptr` → se pueden **reubicar** con `ovl_patch.py` (ya corrige punteros de
  tabla). No hace falta que el inglés entre in situ.
- Marcas: `％` al inicio = línea de nombre; `％Personaje＃Seiyuu` = reparto en dos columnas; `「Serie」` = encabezado;
  `＃　…(順不同）` = cierre del reparto; muchas líneas de reparto traen espacios ASCII al final.
- **El renderer acepta 1 byte por carácter**: el original ya mezcla ASCII (`THE LORD OF ELEMENTAL`, `THE ANIMATION`) y
  kana de medio ancho con `=` ASCII (`ﾗｲﾃﾞｨｰｽ=F=ﾌﾞﾗﾝｼｭﾀｲﾝ`, `ﾗｵﾃﾞｷﾔ=ｼﾞｭﾃﾞｯｶ=ｺﾞｯﾂｫ`, `ﾌｧ-ｽﾄｽﾏｲﾙ･ｴﾝﾀﾃｲﾝﾒﾝﾄ`). Que
  esos nombres se hayan pasado a medio ancho sugiere un **tope de columna ≈ 15 caracteres de ancho completo** para
  el personaje (16–17 ya no entraban). Falta saber si usa el VWF o ancho fijo: verlo en pantalla (checkpoint CP27, #210).

## END: contenido (472 strings)

| Tipo | Filas | Con `en_sugerido` | Fuente de la sugerencia |
|---|---:|---:|---|
| reparto (`％Personaje＃Seiyuu`) | 261 | 250 | personaje: `decisiones.csv` > `glossary.csv` > `hablantes.csv` > fichas DC; seiyuu: campo voz de `dc_en.jsonl` |
| staff (nombre de persona) | 114 | 3 | ejemplos ya romanizados en `creditos_y_canciones.md`; el resto **falta** |
| rol | 41 | 39 | tabla de roles de `creditos_y_canciones.md` (faltan 企画 y 開発) |
| empresa | 28 | 0 | falta (estudios y proveedores: タバック, アーツプロ, サラマンダー・ファクトリー…) |
| serie | 25 | 23 | `series.csv` / fichas DC (faltan 真・ゲッターロボ y Giant Robo) |
| fin (`ＴＨＡＮＫ ＹＯＵ ＦＯＲ ＰＬＡＹＩＮＧ`, `ＴＨＥ ＥＮＤ`) | 2 | 2 | ya en inglés |
| espaciador | 1 | — | se deja |

Orden de los créditos: producción (寺田 貴信 / じっぱひとからげ) → diseño de mechas y personajes → programación →
gráficos → planificación → sonido → **reparto por serie** (Mazinger Z, Great Mazinger, Getter, Raideen, Combattler V,
Voltes V, Daitarn 3, Gundam 0079/0080/0083/Z/ZZ/CCA/F91/V/W, Dunbine, Dancougar, Evangelion, Gunbuster, Macross/DYRL,
Macross Plus, Giant Robo, Masou Kishin, Super Robot Wars originales) → sonido/estudios → ventas, prensa, soporte,
impresos → agradecimientos (Ichiro Mizuki, Mitsuko Horie, Hironobu Kageyama, Chumei Watanabe, Dynamic Planning,
Studio Nue, Winkysoft…) → debug → empresas colaboradoras → comité SRW → productores ejecutivos → desarrollo
(Banpresoft) → Banpresto → 脚本・総監督 寺田 貴信 → THANK YOU FOR PLAYING → THE END.

## Lo que faltaría si se retoma (hoy descartado por C8)

1. **Romanizar 111 nombres de staff y 28 empresas** con fuente (créditos en inglés de otras entregas, Media Arts DB);
   lecturas dudosas (`山　彰史`, `餘語　慶一`, `伊藤　遺`…) marcadas, no adivinadas (`creditos_y_canciones.md`).
2. **11 seiyuu y 1 personaje sin fuente**: los originales de Banpresto de Alpha (杉田智和, 真殿光昭, 小林由美子,
   夏樹リオ, 雛野まよ, 高橋美佳子), 岡村明美, 木原正次郎, 角田なるみ, Ashura (柴田秀勝・北浜晴子: la ficha DC solo
   trae apellidos) y カムジン０３８５０ (Kamjin, Macross).
3. Roles 企画 (*Planning*) y 開発 (*Development*); series 真・ゲッターロボ y Giant Robo en `series.csv`.
4. Decidir `ＴＨＡＮＫ　ＹＯＵ…` en ancho completo o ASCII, y el bloque *English Translation* al final (convención de
   parches fan; necesita entradas nuevas en la tabla → hay que ver cómo termina la tabla en el binario).
5. Pasar el CSV a `menus_map.txt`/`menus_en.jsonl` (o un `end_en.csv` propio), sumar `END` a `MENU_OVLS` y probar con
   el checkpoint de créditos (#210). La cola de la zona A después de END podría ser área de trabajo como en PRO: no
   contar con ella como espacio libre sin verificar.

Tamaño: en las 317 filas que ya tienen sugerencia, el inglés ocupa 9.102 B contra 8.589 B del japonés (+6 %), así que el
bloque completo debería quedar cerca del original. Igual se reubica por la tabla si no entra in situ.
