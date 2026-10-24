# Memory cards de otros jugadores (GameFAQs)

Origen: `saves/super-robot-taisen-alpha.<id>.gme` (DexDrive), convertidas a `.mcd` (se quita la cabecera de 3.904 bytes;
las recortadas se completan hasta 128 KB con entradas libres en el directorio). Descripción según la página de descarga.

| Card | Contenido (directorio) | Descripción del autor |
|---|---|---|
| `gme_1714.mcd` (= `../card_1714.mcd`) | SRSYS (con 中断) + SRWA0…SRWAb | Goharoth, 2002: partidas de las últimas misiones de la ruta **Real**; el 中断 está en la batalla final. 79 puntos de habilidad. |
| `gme_14700.mcd` | SRSYS (con 中断) + SRWA0…SRWA7 | RockmanXZ, 2007: varias partidas con **Kusuha** (pareja Bullet) en la ruta **Super** y **Ryoto** (pareja Rio) en la ruta **Real**. |
| `gme_552.mcd` | solo SRWA3 (sin SRSYS) | philyee, 2000: inicio del **episodio 16 "Roar, Eva Unit 1"** (ruta Super). |
| `gme_553.mcd` | solo SRWA1 (sin SRSYS) | philyee, 2000: inicio del **episodio 67 "Spirit of Steel"**, último de la ruta Real (final con menos de 45 puntos). |
| `gme_1708.mcd` | SRSYS de Alpha + partidas de **SLPS-03148** (`SRWAG*`, probablemente Alpha Gaiden) | StriderVM, 2002 (card norteamericana): empezar en nivel 1 con 1.500.000 de dinero (después de terminar el juego). |

Conversión: `work/emu/states/ajenas/gme_<id>.mcd`. Hallazgos (2026-09-27): el 中断 de la 1714 no carga (se queda en "ロード中です")
y la card no deja guardar (セーブに失敗しました), aun con espacio libre; con el SRSYS limpio de una partida propia (card mixta
`saves/cards/CP12-…`) las SRWA cargan y guardan. Pantalla LOAD de la 1714: Bullet, nivel 58–60, escenarios 61–64.
