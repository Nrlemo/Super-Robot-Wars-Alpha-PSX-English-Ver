# Créditos finales y letras de canciones

Texto que no es diálogo ni menú pero hay que traducir (o decidir no traducir). Está en los overlays: se inserta con
`ovl_patch.py` como el resto de los menús (`work/notes/menus_borrador.md`). Inventario: `work/dump/ovl_strings.jsonl`.

## 1. Créditos finales — overlay `END` (472 strings)

> **Decisión C8 (2026-10-04, #11): los créditos quedan en japonés y `END` no se modifica**
> (`DECISIONES_PENDIENTES.md`). Esta sección queda como referencia por si se retoma; el texto extraído y
> clasificado está en `work/dump/end_credits.csv` (`end_credits.py`) y el análisis en `work/notes/creditos_end.md`.

Estructura observada (**probable**, falta verla en pantalla):

| Marca | Uso | Qué hacer |
|---|---|---|
| sin marca | Rol / encabezado (`プロデューサー`) | Traducir (tabla de abajo). |
| `％` al inicio | Línea de nombre (sangría/columna) | Conservar el `％`; romanizar el nombre. |
| `％Personaje＃Seiyuu` | Reparto: `＃` separa las dos columnas | Conservar `％` y `＃`; personaje = nombre completo de `hablantes.csv`/glosario; seiyuu = romanización (la misma que el campo seiyuu de `work/translation/dc_en.jsonl`). |
| `「Serie」` | Encabezado de serie en el reparto | Título de `series.csv` (sin comillas japonesas: `Mazinger Z`). |
| `ＴＨＡＮＫ　ＹＯＵ　ＦＯＲ　ＰＬＡＹＩＮＧ`, `ＴＨＥ　ＥＮＤ` | Ya en inglés (ancho completo) | Dejar; pasar a ASCII solo si la pantalla de créditos usa la fuente VWF (sin verificar). |

### Nombres propios (staff y seiyuu)
- **Orden occidental** (nombre + apellido): `寺田　貴信` → *Takanobu Terada*. Es lo que usan Wikipedia y los créditos en
  inglés de Banpresto/Bandai Namco. Hepburn sin macrones (*Kouji* → *Koji*).
- Seudónimos y nombres artísticos tal cual se leen: `じっぱひとからげ` → *Jippa Hitokarage*; `望月　親方` → *Oyakata Mochizuki*.
- Empresas/estudios entre paréntesis: `（サラマンダー・ファクトリー）` → *(Salamander Factory)*; `（レイ・アップ）` → *(Ray-Up)* (verificar la grafía de la empresa).
- Nombres con lectura dudosa (`山　彰史`, `餘語　慶一`…): **no adivinar**; marcarlos `DUDOSO` y buscar la lectura en
  los créditos de otras entregas o en Media Arts DB.

### Roles (propuesta)
| JP | EN |
|---|---|
| プロデューサー | Producer |
| エグゼクティブ・プロデューサー | Executive Producer |
| アシスタントプロデューサー | Assistant Producer |
| 脚本・総監督 | Script & General Director |
| 企画・脚本補佐 | Planning & Script Assistance |
| オリジナルメカデザイン | Original Mecha Design |
| オリジナルキャラクターデザイン | Original Character Design |
| グラフィック総監督 | Graphics Director |
| メインプログラム | Main Programming |
| システムデザイン＆システムプログラム | System Design & Programming |
| シナリオデモプログラム | Scenario Demo Programming |
| 戦闘シーンプログラム | Battle Scene Programming |
| ＡＩプログラム | AI Programming |
| イベントプログラム | Event Programming |
| ポケットステーションプログラム | PocketStation Programming |
| 戦闘シーングラフィック | Battle Scene Graphics |
| 戦闘マップ／エフェクトグラフィック | Battle Map / Effect Graphics |
| 戦闘フェイスグラフィック | Battle Face Graphics |
| マップ兵器エフェクトグラフィック | MAP Weapon Effect Graphics |
| ウィンドウ・背景グラフィック | Window & Background Graphics |
| キャラクターグラフィック | Character Graphics |
| ＣＧアニメーショングラフィック | CG Animation Graphics |
| システム管理 | System Administration |
| メインテーマ／エンディングテーマ | Main Theme / Ending Theme |
| サウンド／ＳＥ | Sound / SFX |
| 声の出演　（順不同） | Voice Cast (in no particular order) |
| 音響制作 | Sound Production |
| 録音スタジオ | Recording Studio |
| 営業スタッフ / 広報スタッフ / サポートスタッフ | Sales Staff / Public Relations / Support Staff |
| 印刷物制作スタッフ | Print Materials Staff |
| スペシャルサンクス | Special Thanks |
| 「魔装機神　THE LORD OF ELEMENTAL」原作 | "Masou Kishin: The Lord of Elemental" Original Work |
| デバッグ | Debugging |
| 制作協力会社 | Production Cooperation |
| スーパーロボット大戦委員会 | Super Robot Wars Committee |
| 制作進行 | Production Management |
| 製作・販売 | Produced & Published by |

**Agregar al final** (convención de parches fan): un bloque `English Translation` con los créditos del equipo de la
traducción. Cuidar que entre en el espacio del overlay (reubicar si hace falta).

## 2. Letras de canciones — overlays `SNDM` y `TITL` (≈190 líneas)

Fragmentos de las letras de los temas de apertura (`スーパーロボット マジンガーＺ`, `少年よ 神話になれ`,
`Ｉ ＧＯＴ Ａ ＢＵＲＮＩＮ ＨＥＡＲＴ`…). Algunos ya vienen en inglés (ancho completo). Decisión pendiente
(ya anotada en `README.md`):

| Opción | Pros | Contras |
|---|---|---|
| **A. Dejar el japonés** | Cero riesgo; el fan reconoce la letra; no hay traducciones "oficiales" de casi ninguna | Texto ilegible para quien no lee japonés; necesita que la fuente japonesa siga en el ROM (sigue: el VWF solo cambia la tabla de anchos) |
| B. Romaji | Se puede cantar; fácil de generar | Mucho texto largo; los versos no entran en el mismo ancho |
| C. Traducción al inglés | Se entiende | Traducir letras es subjetivo; más largo que el original (no entra en el ancho) |
| D. Ocultar | Pantalla limpia | Se pierde un contenido del original |

**Recomendación: A** (y pasar a ASCII solo las líneas que ya están en inglés, si la fuente lo permite).

## 3. Títulos de BGM

No hay una lista de títulos de BGM como texto en los overlays (se buscaron `ＡＣＥ`, `マリオネット`, `ＴＩＭＥ`…: solo
aparecen como versos). Si aparecieran en otra pantalla, referencia en inglés: `info/Super Robot Wars_Alpha_BGM - Akurasu Wiki.html`
(p. ej. *Soul of Steel*, *Time Diver*, *Marionette Messiah*). Varios títulos de misión coinciden con temas de BGM
(*Vanishing Trooper*, *Cockpit of Steel*, *For Whom the Bell Tolls*): mantener la misma forma en los dos lados.
