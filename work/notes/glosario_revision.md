# Revisión del glosario: términos `proposed`

Fecha: 2026-09-27. Detalle fila por fila: `work/glossary/proposed_review.csv`
(`category, jp, current_en, recommended_en, short_form, confidence, source, rationale`).
Este documento no modifica `glossary.csv`: las recomendaciones hay que aplicarlas a mano o con script
cuando el mantenedor las apruebe.

## Resumen

Se revisaron las 94 filas `proposed` más las 4 decisiones pendientes de `glosario.md`
(98 filas en el CSV).

| Grupo | Filas | Sin cambio | Cambio recomendado |
|---|---|---|---|
| Espíritus sin nombre oficial | 8 | 4 (Self-Destruct, Miracle, Sacrifice, Revive) | 4: 挑発 Provoke, 隠れ身 Cloak, 奇襲 Raid, 激闘 Frenzy |
| Decisiones pendientes | 4 | 3 (Luck, Hope, Chogokin Z) | 1: 加速 Accel |
| UI | 40 | 34 | 6: 命中 Hit, 必要気力 Will, 必要技能 Req. Skill, 命中率 Hit Rate, レベル Level, 戦闘デモ表示 Battle Animation (short: Battle Anim.) |
| Habilidad de unidad | 1 | — | 換装 Re-Equip (confianza baja) |
| Pilotos | 45 | 33 | 12 (ver abajo) |

### Fuentes usadas
- **Akurasu**, páginas de espíritus de cada juego: Alpha, Alpha Gaiden, OG (GBA, Atlus), OGs, OGMD, T, 30, V, X, Y, Impact, Compact 3, 64, GC.
- **OGMD Weapon List** (Akurasu): nombres oficiales de las columnas de armas (Attack Power, Range, Hit, CRT, Ammo, EN, Will; terrenos Air/Land/Water/Space).
- `work/glossary/web/*.html` (copias locales de T/30/OGs): muestran que **T, 30 y X usan "Morale"** para 気力 y OGs usa "Will".
- **Sitio oficial de Gundam** (`en.gundam-official.com/series/{v,f91,0083}/character`): grafías oficiales de Victory Gundam, F91 y 0083.
- `info/` (Akurasu Alpha y guías de GameFAQs) y los dumps del juego (`work/dump/*.jsonl`) para el contexto.
- Limitación: se agotó el cupo de búsquedas web antes de verificar dos cosas: la forma de 超合金Z en los subtítulos de *Mazinger Z: Infinity* y los nombres de Raideen en SRW DD (inglés).

## Hallazgos que corrigen datos existentes

1. **ルセット・オデビー no es de Masou Kishin**: es de *Gundam 0083: Stardust Memory*. Grafía oficial: **Lucette Audevie**. Hay que corregir la serie.
2. **アギャール** es un general del Imperio Yoma en *Brave Raideen*. Akurasu y Hepburn dan **Agyaru**. Hay que corregir la serie.
3. **Victory Gundam** (sitio oficial): *Elisha/Martina Klánský* (sin tilde en el juego: **Klansky**), *Tomache Massarik* y *Karel Masaryk* (las dos grafías son oficiales aunque sean hermanos), *Mutterma **Sugan*** (no Zugan).
4. **帝国監察軍兵**: en Alpha, el 帝国監察軍 es el ejército inspector del Imperio Balmar, o sea los **Aerogater** (Levi, Laodicea). *Inspector* es otra facción en OG (los Zuvorg), así que "Inspector Soldier" confundiría a los fans. El juego usa エアロゲイター 862 veces y 監察軍 484.
5. **予言者** es el profeta de la película *Mazinger Z vs. el Gran General de la Oscuridad* (SNMSG 8619–8621). Prophet está bien.
6. **激闘 "Fury"**: en OG1/OG2 de Atlus, *Fury* es el nombre oficial de 直撃 (otro efecto). Por eso se recomienda evitarlo.
7. **Límite de 20 bytes de PILOT.BIN**: *Neo Zeon Cyber Soldier* y *Zanscare Cyber Soldier* (22) necesitan short form (`… Cyber Sldr`, 19). *Space Monster Soldier* (21) pasa a *Space Monster Troop*. *Photon Power Lab Staff* (22) pasa a *Photon Lab Staff*. Aparte, PILOT.BIN tiene un campo `short` propio (p. ej. 所員, 兵隊) que también habrá que traducir.

## Decisiones pendientes

### 加速: Accelerate vs Accel

| Opción | Usada en | Pros | Contras |
|---|---|---|---|
| **Accel** | OG1/OG2 GBA (Atlus), T, 30, V, X, Y, fan Alpha/Alpha Gaiden | Mayoría absoluta de fuentes oficiales, incluida la OG de Atlus; 5 caracteres | Suena abreviado |
| Accelerate | OGs / OG Moon Dwellers | Palabra completa | Una sola fuente oficial; 10 caracteres en un menú de ancho fijo |

**Recomendación: Accel** (confianza alta). Es el único caso en que la regla "OG primero" y la regla "T/30/V/X" coinciden.

### 幸運: Luck vs Fortune

| Opción | Usada en | Pros | Contras |
|---|---|---|---|
| **Luck** | OG1/OG2 GBA (Atlus), OGs/OGMD, fan Alpha/Alpha Gaiden | Toda la familia OG; 4 caracteres; es lo que conoce quien leyó guías de Alpha | Los juegos modernos (T/30/V/X/Y) cambiaron a Fortune |
| Fortune | T, 30, V, X, Y | Es el estándar actual de Bandai Namco | Contradice la prioridad OG del proyecto |

**Recomendación: Luck** (confianza media). Es una decisión de política: si el proyecto prefiriera el estándar moderno, habría que cambiar también 期待 para mantener la coherencia.

### 期待: Hope vs Prospect

| Opción | Usada en | Pros | Contras |
|---|---|---|---|
| **Hope** | OG1/OG2 GBA (Atlus), OGs/OGMD, fan Alpha Gaiden | Familia OG; corto y claro | Los modernos usan Prospect |
| Prospect | T, 30, V, X, Y | Estándar actual | Contradice la prioridad OG; menos transparente |

**Recomendación: Hope** (confianza media). Mismo criterio que Luck: Luck y Hope van juntos.

### 超合金Ｚ: Chogokin Z vs Super Alloy Z

| Opción | Usada en | Pros | Contras |
|---|---|---|---|
| **Chogokin Z** | SRW T, SRW 30 (oficial) | Oficial en SRW en inglés; coherente con Chogokin New Z | Transliteración: requiere conocer el término |
| Super Alloy Z | Akurasu, GameFAQs (Superalloy Z), traducciones fan de Mazinger | Se entiende sin conocer el japonés | No es la forma oficial de SRW |

**Recomendación: Chogokin Z** (confianza media), aplicando la regla "oficial gana". No verifiqué cómo lo traducen los subtítulos de *Mazinger Z: Infinity*.

### Nueva: 気力 Will vs Morale

No estaba en la lista original, pero afecta a 気力, 必要気力 y a todas las descripciones de espíritus.

| Opción | Usada en | Pros | Contras |
|---|---|---|---|
| **Will** | OG1/OG2 GBA (Atlus), OGs/OGMD | Familia OG; 4 caracteres | T/30/X usan Morale |
| Morale | T, 30, X | Estándar moderno | Contradice la prioridad OG; 6 caracteres |

**Recomendación: Will**, que es lo que ya tiene el glosario. Conviene que el mantenedor lo confirme de forma explícita.

## Espíritus sin nombre oficial (recomendación)

| JP | Actual | Recomendado | Confianza | Motivo |
|---|---|---|---|---|
| 自爆 | Self-Destruct | Self-Destruct | alta | Unánime en las traducciones de Akurasu |
| 挑発 | Taunt | **Provoke** | media | Akurasu Alpha/64 y GameFAQs; Taunt queda como short form |
| 隠れ身 | Stealth | **Cloak** | media | Akurasu Alpha, Alpha Gaiden y 64 |
| 奇襲 | Ambush | **Raid** | media | Alpha Gaiden y GameFAQs; *Surprise Attack* es demasiado largo; *Blitz* choca con el oficial OGs |
| 激闘 | Fury | **Frenzy** | baja | Evita el choque con Fury = 直撃 de OG. Otras opciones: Fury, Fierce |
| 奇跡 | Miracle | Miracle | alta | Universal |
| 捨て身 | Sacrifice | Sacrifice | media | Akurasu Alpha. El efecto no es un sacrificio; otras opciones: Reckless, Abandon |
| 復活 | Revive | Revive | alta | Alpha e Impact |

## UI: formas cortas

Las etiquetas del juego ocupan de 4 a 12 bytes. Cada fila del CSV trae una forma completa y otra corta. Las cortas siguen
las abreviaturas oficiales de OGMD y T cuando existen: ATK, RNG, HIT, CRT, EN, Will, Air/Lnd/Sea/Spc.
Cambios de fondo:
- **命中** en la ficha de arma: **Hit** (columna de OGMD) en lugar de Accuracy, que no entra en la columna.
- **必要気力**: basta con **Will** (así la rotula OGMD); *Req. Will* si hay espacio.
- **海**: Sea (T y guías de Alpha) en lugar de Water (OGMD).
- **資金**: Funds (T) en lugar de Credits (30).
- **機甲**: probablemente sea 装甲 en el juego (機甲 viene de la guía de GameFAQs). Hay que verificarlo al extraer el overlay.

## Pendiente de decisión del mantenedor

1. **Política Luck/Hope (OG) vs Fortune/Prospect (T/30/V/X/Y)**. Se recomienda OG.
2. **Will vs Morale**. Se recomienda Will.
3. **激闘**: Frenzy (recomendado), Fury (actual; choca con OG1) o Fierce.
4. **ムッターマ・ズガン**: *Mutterma Sugan* (sitio oficial) o *Mutterma Zugan* (lo que usan los fans).
5. **帝国監察軍兵**: *Aerogater Soldier* (recomendado) o *Inspectorate Soldier* (literal).
6. **親衛隊兵**: *Imperial Guard* o *Royal Guard*, según a qué facción pertenezca en el juego (no se pudo determinar con los dumps).
7. **人工知能改**: *Advanced A.I.*, *A.I. Custom* o *A.I. Kai*.
8. **換装**: *Re-Equip* (confianza baja). Verificar en el juego qué unidades lo tienen antes de fijarlo.
9. **ゼントラン兵/メルトラン兵**: *Zentran/Meltran* (términos canónicos de género en Macross) o *Zentradi Soldier* (más reconocible).
10. **Series mal asignadas** en `manual.csv`: ルセット (pasa a Gundam 0083) y アギャール (pasa a Brave Raideen).
11. **Pendiente de verificar en la web**: 超合金Z en *Mazinger Z: Infinity* y los nombres de Raideen en SRW DD (se agotó el cupo de búsquedas).
