# Protagonistas: personalidad, variantes y pareja

**Lo central:** en SRW Alpha el protagonista **no es un personaje fijo**. En la pantalla de ingreso (overlay `ENTR`)
el jugador elige, por separado:

| Campo (texto del juego) | Qué define |
|---|---|
| `顔を選択します。性別も自動的に決定されます。` — cara (8) | **Género** (4 caras de varón, 4 de mujer) y retrato |
| `氏名を変更します。` / `愛称を変更します。` — nombre, apellido, apodo | `$n` (apodo en el diálogo), `$f` (nombre completo) |
| `誕生日` / `血液型` — cumpleaños y sangre | Espíritus y habilidades (Akurasu, Pilot Database) |
| `性格を４つのタイプから選択します。` — **personalidad (4 tipos)** | **Qué variante de cada línea dice** |
| `ｽｰﾊﾟｰﾛﾎﾞｯﾄ/ﾘｱﾙﾛﾎﾞｯﾄの種別` — tipo | Ruta (Super/Real) y robots |

Los "8 personajes" (Bullet, Yuuki…) son **preajustes** (`8人の登録キャラクターから選択します。`): una combinación de
cara + nombre + personalidad. Después se configura la **pareja** (`恋人設定`, `「はい」を選ぶと恋人キャラクター設定に移ります。`).

> La guía de Cyath (`info/`) lista otras personalidades (`まじめでやさしい熱血漢`, `クールでニヒル`…): están copiadas de una
> guía de SRW F Final y **no son las de Alpha**. Valen los textos del juego (`ENTR`, `SNDM`, `TITL`).

## 1. Las 8 variantes = género × personalidad

Cada línea del protagonista viene en **8 variantes consecutivas** (SCRIPT: bloques de 8 líneas de `$n`; SNMSG: opcode
`18`, columna `variante` de `dump/sndata_map.csv`). El orden es **varón × 4 personalidades, mujer × 4 personalidades**:

| Var. | Género | Personalidad (texto del juego) | EN del menú (borrador) | Preajuste por defecto | Pareja que habla en `$l`/`$N` var. k |
|---:|---|---|---|---|---|
| 1 | varón | 真面目で正義感が強い | Serious, strong sense of justice | Brooklyn "Bullet" Luckfield | Kusuha (mujer, tímida) |
| 2 | varón | 冷静沈着で頭脳明晰 | Calm and brilliant | Yuuki Jaggar ("Yuu") | Carla (mujer, alegre) |
| 3 | varón | 内気で心優しい | Shy and kind | Ryoto Hikawa | Rio (mujer, seria) |
| 4 | varón | 陽気で楽天家 | Cheerful and optimistic | Tasuku Shinguji | Leona (mujer, fría) |
| 5 | mujer | 真面目で正義感が強い | Serious, strong sense of justice | Rio Mei Long | Ryoto (varón, tímido) |
| 6 | mujer | 冷静沈着で頭脳明晰 | Calm and brilliant | Leona Garstein | Tasuku (varón, alegre) |
| 7 | mujer | 内気で心優しい | Shy and kind | Kusuha Mizuha | Bullet (varón, serio) |
| 8 | mujer | 陽気で楽天家 | Cheerful and optimistic | Ricarla "Carla" Borgnine | Yuuki (varón, frío) |

**Emparejamiento** (deducido de los datos, coherente en SCRIPT y SNMSG): serio ↔ tímida/o, frío/a ↔ alegre. Las líneas
de la pareja (`$l` en SCRIPT, `$N` en SNMSG) también vienen en 8 variantes y **la variante k la dice la pareja del
protagonista k**: `$l` var. 1 habla como Kusuha, var. 6 como Tasuku. `lote.py` ya lo pone en `ctx.quien`.

**✅ Confirmado en el juego 2026-09-29 (#34, ISO `variantes_test_v01` que muestra V1–V8 en cada línea `$n`):**
- Cara de Bullet + personalidad 3 (tímida) → **V3**: decide la personalidad, no la cara.
- Cara de mujer + personalidad 1 → **V5**; cara de mujer + personalidad 4 → **V8**: variante = género de la cara × personalidad.
- Pareja (`恋人設定`) con el protagonista de la var. 3: **Rio Mei Long, 真面目で正義感が強い** = la pareja de la tabla.
  La personalidad de la pareja sale del emparejamiento fijo y **no se puede cambiar** (`この項目は変更できません。`);
  tampoco su género ni su tipo de robot. Solo se puede cambiar nombre, apodo, cumpleaños y sangre.
- Cómo decide SCRIPT: no hay selector en el bytecode; las 8 líneas `$n` son consecutivas con op/sub/arg idénticos y el
  juego toma la k-ésima del bloque (rachas de 16/24/… líneas = varias líneas del guion seguidas).

## 2. Qué significa para traducir

1. **Traducí la personalidad, no el nombre por defecto.** El jugador puede llamarse como quiera (`$n`), pero la
   variante 1 siempre es "varón serio y justiciero". Nunca escribir "Bullet" en lugar de `$n`.
2. **Los detalles de trasfondo van con la variante**, no con la cara: la var. 1 dice que sus apuntes están en inglés
   (Bullet es estadounidense) y practica kendo; la 3 viene de un dojo de karate; la 5 es delegada de clase criada en
   una ciudad lunar; la 6 monta a caballo. Se traducen tal cual.
3. **Género**: dentro de un bloque de 8, el género es el de la tabla (1–4 varón, 5–8 mujer; la pareja, el opuesto).
   Fuera de los bloques, otros personajes hablan del protagonista sin saber su género → evitar he/she (guía §1.5).
4. **Las 8 líneas deben sonar distintas en inglés** aunque el japonés difiera en una sola partícula: el inglés no
   tiene 俺/僕/私/あたし ni わ/ぜ/かしら, así que la diferencia se hace con vocabulario, contracciones, ritmo y actitud.

## 3. Cómo habla cada personalidad (medido en los volcados)

Estadística sobre todas las líneas de cada variante (`$n`: 2.432 por variante; `$l`: 394; `$N`: 179).
"!" = signos de exclamación por línea.

| Var. | Pronombre | Finales más usados | ! | Voz en inglés |
|---:|---|---|---:|---|
| 1 ♂ serio | 俺 | だ, な, よ, **ぞ** | 0,47 | Earnest, hot-blooded hero. Direct, firm, protective; contractions; "Leave it to me!", "I won't forgive them!". Short temper (perfil del juego). |
| 2 ♂ frío | 俺 | だ, な, **ぞ**, ね | **0,36** | Cool, clipped, analytical, a little aloof or sarcastic. Few exclamations, fewer contractions, complete sentences. Likes tea. |
| 3 ♂ tímido | **僕** | だ, **よ**, ね | 0,44 | Gentle, polite, hesitant ("Um...", "I-I think..."), apologizes, trails off; firm when it counts. |
| 4 ♂ alegre | 俺 | だ, **よ**, な, **ぜ** | 0,47 | Joker and gambler: slangy, cocky, playful ("gonna", "man", "jackpot", betting metaphors). |
| 5 ♀ seria | 私 | **わ**, ね, よ, **のよ** | 0,46 | Bossy class rep: responsible, scolding, righteous ("Honestly!", "Pull yourself together!"). Can be preachy. |
| 6 ♀ fría | 私 | わ, ね, のよ, **かしら** | **0,35** | Aristocratic, composed, cool; correct English with few contractions ("I suppose...", "How tiresome."). |
| 7 ♀ tímida | 私 | わ, ね, よ, のよ | 0,42 | Soft-spoken, kind, hesitant ("...", "um"), never harsh; surprising resolve in a crisis. |
| 8 ♀ alegre | **あたし** | **よ**, ね, だ, な | 0,45 | Bubbly, expressive, flirty without malice ("C'mon!", "Ooh!"), casual contractions, loves music and dancing. |

Como pareja (`$l`/`$N`), cada uno conserva su voz: la variante k usa la voz de la pareja de la tabla §1.

## 4. Perfiles de los preajustes (texto del juego)

En `ENTR` hay un perfil de **3 renglones** por preajuste (el volcado ya los trae completos desde 2026-09-29, #9: el
inventario cortaba en el `0x0A`). El orden coincide con las personalidades de la tabla §1 (el perfil 1 empieza
`義理人情に厚い真面目な少年`). Traducción completa en `translation/menus_map.txt`. Asignación por orden en memoria
(= orden de la tabla de preajustes):

| # | Preajuste | Último renglón del perfil (JP) | Último renglón, borrador anterior |
|---:|---|---|---|
| 1 | Bullet | 集めている。少々短気なところが玉にキズ。 | …the respect of others. A bit hot-headed. |
| 2 | Yuuki | ところがあるが、人付き合いは割と良い。 | …side, but is fairly sociable. |
| 3 | Ryoto | だが、芯はしっかりしており、意外に前向き。 | …but firm at heart and surprisingly upbeat. |
| 4 | Tasuku | 早く洞察力に優れている。実は運動音痴。 | …sharp and perceptive. Bad at sports. |
| 5 | Rio | 優等生タイプで、割と説教くさいところがある。 | Honor-student type; tends to lecture. |
| 6 | Leona | 何でもこなすように見えるが音痴で料理下手。 | Seems capable, but tone-deaf; can't cook. |
| 7 | Kusuha | いざという時の行動力は他人を驚かせるほど。 | In a pinch, acts with startling drive. |
| 8 | Carla | 一晩寝れば忘れる。実は結構ロマンティスト。 | Sleeps it off. Secretly a romantic. |

Datos de `PILOT.BIN` (ids 259–290): los 8 tienen temperamento de combate **強気 (fuerte)**; cada uno tiene 3 registros
(Super, Real y pareja) y los espíritus dependen del registro, no del preajuste. Akurasu: los espíritus y habilidades
cambian con el cumpleaños y la sangre.

## 5. Ejemplos

Guía de estilo §3 (`work/notes/guia_estilo_personajes.md`): escena del examen y declaración a la pareja, las 8
variantes traducidas con su voz.
