# MDATA.BIN (SNMAP y TEST) — nombres de terreno y lugares (#221) — 2026-10-01

Herramienta: `tools/src/mdata_bin.py` (`dump` → `dump/mdata.jsonl`; `build SNMAP|TEST entrada.jsonl salida.BIN`; `selftest`).
Traducción: `translation/mdata_en.csv` (jp → en, 72 nombres únicos; la fuente de verdad de `en` es el volcado, el CSV lo genera).
Pruebas sin ISO: `tools/src/test_mdata_bin.py` (en `ci_check.sh tests`).

## Formato (verificado sobre los 140 bloques de SNMAP y los 11 de TEST)
- `u32 offset[…]` absolutos, múltiplos de 0x800: un bloque por mapa; el último valor = tamaño del archivo (SNMAP 2.699.264 B, 141 valores).
- Dentro de cada bloque, **registros de 20 bytes alineados a 4**: `u8[4]` cabecera + `char name[16]` (SJIS, relleno NUL).
  Nombres de terreno (領域外, 平原, 道路, 海, 森…), de lugares (光子力研究所, 兜甲児の家, ﾘﾘｰﾅの屋敷…) y de naves/colonias en
  kana de ancho medio (ﾏｸﾛｽﾄﾞｯｸ, ﾋﾞｯｸﾞﾌｧﾙｺﾝ…). Máximo japonés: 14 bytes → **inglés ≤ 15 bytes + NUL**.
- No hay punteros a los nombres: el reemplazo es **en el mismo lugar** y el archivo no cambia de tamaño.
- Cuidado al buscarlos: un barrido a paso 4 también "encuentra" los sufijos de un nombre (外 dentro de 領域外). `fields()` avanza
  16 bytes al aceptar un campo; sin eso daba 1.463 campos en vez de 1.375.
- Regla de detección: campo de 16 B con NUL al final, ≥1 carácter de ancho completo, **o** solo kana de ancho medio y ASCII con ≥3
  kana y 2 NUL al final (ruido de gráficos tipo `ﾀﾀ` queda fuera). Los nombres pueden llevar ASCII: `ｺﾛﾆ-` (Colony, el `-` es ASCII),
  `NERV本部`, `DC本部ﾋﾞﾙ`. La primera versión los descartaba (52 campos; lo vio el mantenedor en el juego: «コロニ-» sin traducir).

## Volumen
SNMAP: 1.343 campos · TEST: 83 · 79 nombres únicos (1.426 filas). Todos con `en` (≤ 15 B, 0 avisos de `check_text.py --only mdata`).

## Pendiente / sin verificar en el juego
- Cómo se muestran (ventana de información de terreno y cartel de lugar): ancho en px sin medir (`line_px` = None en `check_text.py`).
- Se concatenan en tiempo de ejecución? (電力供給ﾋﾞﾙ, 南原ｺﾈｸｼｮﾝ llevan el segundo término pegado: ver si el juego agrega algo).
- 神面岩 = *Jinmen Rock* (hangar de Raideen, じんめんいわ; sin nombre oficial en inglés, Hepburn). Confirmados por el mantenedor: ﾋﾞｯｸｼｪﾙ = *Big Shell*, 雷王星 = *Planet Raioh*, ﾗﾋﾞｱﾝﾛ-ｽﾞ = *La Vie en Rose*.
- Probar en el juego: escenario 1 (terrenos al mover el cursor) y un mapa con lugar (光子力研究所 / 兜甲児の家).
