# Carpeta de traducción (Fase 2) — SRW Alpha JP→EN

Todo lo que necesita una sesión (humana o de Claude) para traducir diálogo: el **prompt**, las **referencias de
nombres** y las **herramientas de lotes**. El texto japonés sigue en `work/dump/` (fuente de verdad de los
archivos del juego); acá se trabaja por lotes y el resultado se integra al volcado cuando está revisado.

## Cómo empezar (3 comandos)

```bash
# 1. Refrescar referencias (conteos, correcciones aplicadas, glosario unificado, reporte de conflictos)
python3 work/tools/src/traduccion_ref.py
# 2. Sacar un lote con contexto (hablante en inglés, variante del protagonista, escenario, términos)
python3 work/tools/src/lote.py sacar script 1-3
# 3. Traducir con PROMPT.md, y validar
python3 work/tools/src/lote.py validar traduccion/lotes/script/script_001-003.jsonl
```
Solo Python 3.10+ de sistema (sin dependencias, sin ISO): sirve igual en server1, la desktop y la nube.

## Estructura

```
traduccion/
├── README.md                 este índice
├── PROMPT.md                 prompt para las sesiones de traducción (bloque listo para pegar)
├── DECISIONES_PENDIENTES.md  lo que falta decidir (con la opción provisoria que usa el prompt)
├── referencia/               nombres y términos canónicos (los CSV se editan a mano; ver "Mantenimiento")
│   ├── hablantes.csv         355 hablantes de SCRIPT+SNMSG → etiqueta inglesa, nombre completo, serie, líneas,
│   │                         personalidad, voz en inglés, perfil de habla medido y temperamento de combate
│   ├── protagonistas.md      el protagonista = género × personalidad (4 tipos): variantes 1–8, parejas, voces
│   ├── series.csv            32 series: título oficial en inglés, localización de referencia, convenciones
│   ├── misiones.csv          130 títulos de escenario: borrador EN (menús), título fan, referencia al episodio
│   ├── lugares.csv           79 lugares (ciudades, bases, colonias, planetas, Byston Well, La Gias…)
│   ├── facciones.csv         57 ejércitos, organizaciones, empresas, escuadrones
│   ├── naves.csv             24 naves y megaestructuras tal como se nombran en el diálogo
│   ├── terminologia.csv      117 términos: tipos de mecha, tecnología de cada serie, operaciones, rangos y cargos
│   ├── frases_fijas.csv      72 frases: reacciones recurrentes, gritos de batalla, condiciones de victoria/derrota,
│   │                         rótulos de tutorial, frases icónicas de cada serie
│   ├── correcciones.csv      13 erratas del glosario con su corrección propuesta (11 ya aprobadas, #46)
│   ├── creditos_y_canciones.md  créditos finales (roles, romanización), letras de canciones, BGM
│   └── generado/             NO EDITAR (lo arma traduccion_ref.py)
│       ├── pilotos.csv · unidades.csv · armas.csv · sistema.csv   glosario con las correcciones aplicadas
│       ├── glosario_unificado.tsv   2.608 pares jp→en de todas las fuentes (lo usa lote.py)
│       └── reporte.txt              conflictos entre fuentes, caracteres no codificables, avisos
└── lotes/                    lotes de trabajo (<formato>/<formato>_<rango>.jsonl + .terminos.tsv + .reparto.tsv)
                              y REGISTRO.md
```

## Referencias: de dónde sale cada cosa

| Archivo | Fuente | Estado |
|---|---|---|
| `hablantes.csv` | `speakers.csv` (77 con ficha de voz) + glosario (189) + resueltos a mano (89: los 67 que no tenían inglés y las coincidencias ambiguas, p. ej. `ユイ` = Yui Ikari, no Heero Yuy; `リン` = Ring Mao; `ニー` = Neal Given) | Completo: los 355 hablantes de los volcados tienen etiqueta (lo verifica `traduccion_ref.py`) |
| `misiones.csv` | `dump/sndata_bloques.csv` (escenario/ruta/bloque) + borrador de `translation/menus_en.jsonl` (IMIS/TITL, con tope de bytes) + títulos de Akurasu | Borrador; errores del título fan anotados |
| `lugares/facciones/naves/terminologia.csv` | Guía §5, glosario, dc/dr_en, localizaciones oficiales, y **términos minados de los diálogos** (katakana/kanji frecuentes sin entrada en el glosario). Cada fila trae `apariciones` reales | `fijo` / `propuesta` / `DUDOSO` por fila |
| `frases_fijas.csv` | Guía §2 + líneas más repetidas de los volcados + patrones de las 659 condiciones de victoria/derrota | Propuesta |
| `series.csv` | Tabla `SERIES` de `dict_build.py` (títulos tal como los da el juego) + convenciones por franquicia | Propuesta |
| `generado/*` | `work/glossary/glossary.csv` + `correcciones.csv` | Regenerable |

## Lo que se agregó además de nombres, unidades, lugares y misiones

- **Hablantes completos** (no solo personajes jugables): genéricos (`連邦軍兵`, `所員`, `声`, `？？？`), villanos,
  científicos, familiares; con las **etiquetas que chocan en inglés** marcadas (Hayato, Elle, Rei, Shiro, Kenzo).
- **Naves y terminología técnica** de cada serie (Minovsky, AT Field, Getter Rays, aura power, prana, T-LINK, fold…),
  **rangos y cargos**, operaciones (Operation Stardust, Yashima).
- **Frases fijas**: memoria de las líneas más repetidas y plantillas de **condiciones de victoria/derrota**
  (el mismo `Xの撃墜。` es "Defeat X." o "X is destroyed." según la lista).
- **Créditos finales y letras** (overlays END/SNDM/TITL): texto a traducir que no es diálogo.
- **Erratas del glosario** (`Daijiburou Higashiyamo`, `Kozo Fuyutski`…) y **términos con dos versiones** en el repo:
  los de glosario/referencias en `generado/reporte.txt` (9) y los de dc/dr_en y menús en `DECISIONES_PENDIENTES.md` §B.
- **Herramientas** `lote.py` (sacar / términos / validar / integrar / estado) y `traduccion_ref.py`.
- **Contexto que el volcado no daba**: quién dice cada una de las 8 variantes del protagonista en SCRIPT
  (bloques de 8 consecutivos: variante k = protagonista k; en las líneas de `$l`, la pareja del protagonista k).
- **Personalidades** (2026-09-28): los 355 hablantes con personalidad, voz en inglés, **perfil de habla medido**
  (pronombre, finales de frase, trato, formalidad) y temperamento de combate de `PILOT.BIN`; cada lote trae su
  `.reparto.tsv`. Hallazgo: el protagonista **no es un personaje fijo** sino **cara (→ género) + personalidad
  elegida** (真面目で正義感が強い / 冷静沈着で頭脳明晰 / 内気で心優しい / 陽気で楽天家): las 8 variantes son
  género × personalidad (`referencia/protagonistas.md`). La guía de Cyath trae otras personalidades (de SRW F Final).

## Avisos que cambian la traducción

1. **Tokyo-2, no Tokyo-3**: la historia de Alpha dice `第２新東京市`. Solo las fichas DC/DR (que resumen el anime)
   dicen `第３`.
2. **Condiciones de victoria/derrota**: mirar `ctx.tipo` antes de traducir `Xの撃墜。`.
3. **Variantes del protagonista**: 8 combinaciones género × personalidad → 8 traducciones distintas (`ctx.quien`);
   se traduce la personalidad, no el nombre por defecto (el jugador puede renombrarlo).
4. **Ancho** (medido en el juego, #31): 240 px por línea (≈ 50–57 caracteres con el VWF) en mapa, DEADMESS, EM y batalla
   (en batalla el juego agrega 「」, 12 px c/u); **272 px en escenas** (SCRIPT). 3 líneas por caja (2 en batalla). Manda el
   validador: lo que se pasa, el juego lo parte solo a mitad de palabra y pierde los renglones de más.
5. **Solo ASCII** (la fuente es cp932): nada de rayas largas, comillas curvas, acentos, `²` o `…`.
6. `CLAUDE.md` §1 lista franquicias que **no están en Alpha** (Brain Powerd, Full Metal Panic, Detonator Orgun,
   Zeorymer, L-Gaim, GaoGaiGar, Gravion) y le faltan varias que sí están (Combattler V, Voltes V, Daitarn 3, Raideen,
   Giant Robo, Macross/Macross Plus). La lista real (según los datos del propio juego) está en `referencia/series.csv`.

## Volumen a traducir (hoy: 0 líneas de diálogo)

| Formato | Filas | Lote típico |
|---|---:|---|
| `script` (escenas de intermisión) | 45.363 | 1–3 escenas |
| `snmsg` (diálogo de mapa, condiciones) | 32.544 (256 `Dummy String`) | 1 bloque de SNDATA |
| `bxclist` (frases de batalla) | 18.128 (7.155 únicas: la memoria `tm` ayuda) | 5–10 pilotos |
| `deadmess` (al ser derribado) | 544 | entero |
| `em` (al suspender) | 30 | entero |

Menús, DC/DR, nombres de unidades/armas/pilotos ya tienen borrador en `work/translation/` y `work/glossary/`.

## Mantenimiento

- Se editan a mano: los CSV de `referencia/` (salvo `generado/`) y este README. Después, correr
  `python3 work/tools/src/traduccion_ref.py`: reescribe **solo** las columnas de conteo, regenera `generado/` y avisa
  si un término no aparece en el juego, si un hablante del volcado no tiene etiqueta o si hay conflictos nuevos.
- Una corrección aprobada pasa de `correcciones.csv` a `work/glossary/decisiones.csv` (y se borra de acá).
- Un término nuevo que aparece al traducir: agregarlo al CSV que corresponda (con `estado = propuesta`) en el mismo
  commit del lote.
