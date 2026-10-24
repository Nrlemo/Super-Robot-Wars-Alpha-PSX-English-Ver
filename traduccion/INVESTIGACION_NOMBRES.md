# Investigación externa: decisiones de nombres pendientes — ronda 2

> **Estado (2026-09-28): cerrado.** La ronda 2 se respondió completa y quedó aplicada tras la revisión del mantenedor
> (respuestas y veredicto fila por fila en `traduccion/investigacion/ronda2_respuestas.csv`: 49 aprobadas, 18 ajustadas,
> 69 confirmadas, 8 rechazadas). Los 10 puntos sin fuente verificable quedan en el issue **#54** para revisión manual; mientras
> tanto se mantiene el valor actual. El prompt de abajo queda como registro; si hiciera falta otra ronda, sumar a §2.2 lo
> decidido en la ronda 2 (ver `work/glossary/decisiones.csv`).

_Ronda 1: 2026-09-28 (119 puntos; la otra IA respondió ~45, sin URL). Ronda 2: 2026-09-28._ Prompt autocontenido para
que **otra IA con búsqueda web** investigue las decisiones de nombres que siguen abiertas y proponga una opción
justificada para cada una. Reúne lo pendiente de los issues #38–#45 y #14, de `traduccion/DECISIONES_PENDIENTES.md`,
de los `proposed`/DUDOSO de `work/glossary/` y `traduccion/referencia/`, y de inconsistencias encontradas.

**Resultado de la ronda 1.** Se aprobaron y cargaron en `work/glossary/decisiones.csv` (y en las referencias, DC/DR y
menús) las decisiones de §2.2. La respuesta no traía URL y tenía errores comprobados (p. ej. *Aura Warrior*: SRW X usa
*Holy Warrior*), así que en esta ronda **sin URL no hay decisión** y el trabajo va en **6 tandas** más chicas (78 puntos).

**Cómo usarlo.** Copiar todo lo que está debajo de la línea `INICIO DEL PROMPT` y pegarlo en la otra IA. Pedir **una
tanda por respuesta** ("hacé la tanda 1"; después "tanda 2"…). Si el japonés llega con caracteres rotos al pegar la
respuesta, no importa: los IDs alcanzan. Con cada respuesta:
1. Revisar las propuestas y aprobar o rechazar cada una. La IA propone; la decisión es del mantenedor.
2. Pasar las aprobadas a `work/glossary/decisiones.csv` (gana siempre en `glossary_build.py`; columna `en_short` para
   las formas cortas) o, si son de estilo (rangos, epítetos), a `work/notes/guia_estilo_personajes.md` y
   `traduccion/referencia/terminologia.csv`.
3. Regenerar: `glossary_build.py`, `traduccion_ref.py`, `menus_draft.py` y `dict_build.py dc dr`; validar con
   `check_text.py`. Cerrar o tachar los issues.

**No entran en esta lista** porque no son nombres: muletillas (`だわさ`, `やってやるぜ`, `あんたバカ？`), la política de
honoríficos y los problemas técnicos.

---

<!-- ================= INICIO DEL PROMPT ================= -->

# Encargo: investigar nombres para una traducción fan de *Super Robot Wars Alpha* (PS1) — ronda 2

## 1. Rol

Sos investigador/a de localización, especialista en anime mecha de los años 70 a 2000 y en la saga **Super Robot
Wars (SRW)**. Conocés cómo se localizaron oficialmente al inglés las franquicias (Bandai/Sunrise, Toei/Discotek, ADV,
Netflix, AnimEigo, Media Blasters, Sentai Filmworks, Bandai Visual) y cómo las nombra el fandom angloparlante
(Akurasu, Super Robot Wars Wiki, GameFAQs, MAHQ, Gundam Wiki, Macross Mecha Manual, EvaGeeks, fansubs).

**Tenés que buscar en internet** para cada punto. No respondas de memoria: cada afirmación sobre una grafía lleva su
fuente con URL. **Un punto sin URL cuenta como "no resuelto"**, aunque la respuesta parezca obvia.

## 2. El proyecto

Traducción fan del japonés al inglés de **Super Robot Taisen Alpha** (Banpresto, PlayStation, 2000). Es un crossover
con: Mobile Suit Gundam (0079, 0080, 0083, Zeta, ZZ, Char's Counterattack, F91, Victory, Wing, Endless Waltz),
Mazinger Z, Great Mazinger, las películas de Mazinger, Getter Robo, Getter Robo G, Shin Getter Robo, Combattler V,
Voltes V, Daitarn 3, Brave Raideen, Dancouga, Giant Robo (OVA), Gunbuster, Neon Genesis Evangelion y *The End of
Evangelion*, Macross (TV y *Do You Remember Love?*), Macross Plus, Aura Battler Dunbine, Masou Kishin y los
originales de Banpresto (SRX Team, Aerogaters/Balmar).

El texto se ve en tres lugares:
- **Menús y listas** (unidades, pilotos, armas, espíritus): campos de **largo fijo en bytes**.
- **Diálogos** (unas 96.000 líneas): **sin límite de bytes**, pero un nombre largo repetido mil veces pesa.
- **Diccionario** de personajes y robots del juego.

### 2.1 Restricciones técnicas (obligatorias)

- **Solo ASCII**: la fuente del juego no tiene acentos, macrones ni diéresis. Nada de `ō`, `ū`, `é`, `á`. El único
  símbolo especial disponible es `ν` (solo para *ν Gundam*).
- **Límites en bytes** (1 carácter ASCII = 1 byte). **Solo valen para esos campos, no para el diálogo**:
  - nombre completo de piloto: **≤ 20**
  - nombre corto de piloto (rótulo del hablante en batalla): **≤ 12**
  - nombre de unidad: **≤ 21**
  - nombre corto de arma: **≤ 19**
  - espíritus y rótulos de menú: se indica en cada punto.
- Si la mejor opción no entra, proponé además una **forma corta**, idealmente una que ya se use oficialmente (por
  ejemplo, cómo la abrevian los SRW en inglés). Contá los bytes y decilo.

### 2.2 Ya decidido (no lo reabras)

- **Romanización**: se usa el **nombre oficial en inglés si existe**. Si no existe, **Hepburn sin macrón** y sin
  `ou`/`uu`: *Hyoma*, *Juzo*, *Kozo*, *Taiso*. Nunca *Hyouma* ni *Hyōma*. Si hay grafía oficial con `oh`/`ou`, gana
  la oficial (*Planet Raioh*).
- **Terminología del sistema** (espíritus, habilidades, rótulos de menú): la de **SRW OG en inglés** (Atlus, GBA). Ya
  fijados: *Accel*, *Luck*, *Hope*, *Fury*, *Will* (no *Morale*), *Sword Cut*, *Telekinesis Field*, *Self-Destruct*.
- **Términos**: *Federation Forces* / *Earth Federation Forces* (EFF) en todo el juego, también SRX (no EFA) ·
  *Imperial Inspection Army* (帝国監察軍), *Galactic Frontier Inspection Army* (辺境銀河方面監察軍) y *Aerogaters* solo
  donde el japonés dice エアロゲイター · *Ze Balmary Empire* (sin guion) / *Balmar* · *Holy Warrior* (聖戦士, habilidad
  y diálogo) · *Photon Power Laboratory* (corta *Photon Lab*), *Photon Power* (光子力) · *Chogokin Z* / *Chogokin
  New Z* · *Cyber Newtype* (sin guion) / *Cyber Soldier* · *Berserk* (暴走, en todo) · *Jupitorians* (facción) /
  *Jupitris* (nave) · *Planet Raioh* · reinos *the Kingdom of Na / Rau / Ku / Ah / Mi* · *Demon Empire* (妖魔帝国) ·
  *Battle Beast* (戦闘獣).
- **Personajes y unidades**: nombres japoneses en Voltes V (no el doblaje filipino) · *Do Zuhl* · *Katherine Rii*
  (provisorio, ver D03) · *Taiso* · *Shokatsuryo Komei* · *Chief Chujo* · *Priest* (平祭官) · *Shakti Kareen* ·
  *Mahalia Merrill* · *Connie Francis* · *Chronicle Asher* · *Vrlitwhai 7018* · *Exsedol 4970* · *Quamzin 03350* ·
  *Milia Fallyna Jenius* (y *Milia* en sus unidades) · *Ricarl* · *Bluegar* · *Boddole Flagship* · *Raideen* /
  *Brave Raideen* · *Dancouga* · *Zentradi Soldier* / *Meltrandi Soldier* · *Great General of Darkness* (corta *Dark
  Great General*) · *Professor Yumi* (rótulo *Prof. Yumi*) · *Zaku III Custom* · *Evangelion Unit-00 Kai* (corta *EVA
  Unit-00 Kai*) · *the Red Comet*.
- **Rangos**: 少尉 *Ensign* · 中尉 *Lieutenant* · 大尉 *Captain* en todas las series (*Captain Amuro*, *Captain
  Burning*) · 少佐 *Major* · 中佐 *Commander*: *Cmdr. Bright* si se nombra el rango, *Captain Bright* si se lo llama
  por su puesto al mando de la nave (艦長) · 長官 según el personaje (*General Oka*, *Chief Chujo*, *Commander Igor*).
- **Títulos de misión**: 誰がために鐘は踊る = *For Whom the Bell Dances* (parodia intencional).
- Otros ya decididos antes: *Pinpoint Barrier*, *I-Field*, *Prince Sharkin* / *Giant Sharkin*, *Agyaru*, *Elisha* y
  *Martina Klansky*, *Karel Masaryk*, *Tomache Massarik*, *Lucette Audevie*, *Minmay Doll*, *Mutterma Sugan*,
  *Aerogater Soldier*, *Imperial Guard*, *A.I. Kai*, *Kozo Fuyutsuki*, *Hikaru Ichijo*, *Hyoma Aoi*, *Claudia
  LaSalle*, *Gundam Mk-II (AEUG)*, *Meltrandi*, *Daizaburo Higashiyama*, *Dr. Kotaro Hazuki*, *Koichiro Ohta*, *Juzo
  Naniwa*, *Taro Sarumaru*, *RyuKoOh* / *KoRyuOh* / *RyuOhKi* / *KoOhKi*, *VF-1J Armored*, *Degeneration Cannon*,
  *Yuuki Jaggar*, los apodos del protagonista (*Bullet, Yuu, Ryoto, Tasuku, Rio, Leona, Kusuha, Carla*) y el formato
  de diálogo `Nombre: texto`.
- Si encontrás **evidencia fuerte en contra** de algo ya decidido, anotalo en la sección "Alertas" de tu respuesta,
  con URL, pero no lo cambies.

### 2.3 Hechos verificados en la ronda 1 (para no repetir errores)

- **Voltes V y Dancouga sí están en SRW 30** (DLC). Su versión en inglés es fuente oficial válida para esas series.
- **SRW X en inglés** usa la habilidad *Holy Warrior* y la grafía *Sho Zama* (Dunbine), según NamuWiki y la SRW Wiki: conviene confirmarlo con una fuente primaria.
- En SRW 30 la unidad de Getter aparece como *Shin Getter* (sin número): eso no resuelve *Getter 1* vs. *Getter-1*.
- *Quamzin 03350* figura así en los créditos del film *Do You Remember Love?*.

## 3. Cómo decidir y cómo justificar

Para **cada punto** justificá con estos cuatro ejes, en este orden:

1. **Coincidencia con la traducción (fidelidad)**: qué dice y cómo se lee el japonés (kanji, katakana, furigana,
   juegos de palabras) y, si el nombre viene de otro idioma, la grafía de origen (hebreo, nórdico, ruso, chino,
   latín…). Una opción que contradice la lectura japonesa necesita una razón fuerte.
2. **Localización oficial, si la hay**. Indicá empresa, producto, año y la grafía **exacta** (mayúsculas, guiones,
   espacios), con URL. En orden de peso:
   a) la localización oficial de la **propia franquicia** (subtítulos o doblaje oficiales, sitios oficiales como
      gundam-official.com / gundam.info, fichas oficiales, packaging de Bandai en inglés);
   b) los **SRW oficiales en inglés**: OG y OG2 (Atlus, GBA), OG Saga: Endless Frontier, *The Moon Dwellers*,
      SRW V, X, T, 30, Y (ediciones en inglés de Bandai Namco) y SRW DD. **Antes de citar un SRW, verificá que la
      serie esté en ese juego** (lista de series del juego, con URL).
   c) otro material oficial (Blu-ray, artbooks, juguetes).
   Para términos del sistema de juego, el orden es: OG primero, después T/30/V/X/Y.
3. **Uso fan**: qué grafía usa el fandom angloparlante y qué tan extendida está (Akurasu, SRW Wiki, GameFAQs
   —incluida la guía de Alpha de Cyath—, fansubs, traducciones fan de otros SRW como Alpha Gaiden, Alpha 2, Alpha 3,
   Z, MX, GC). Decí cuál domina y en qué fuentes.
4. **Otras traducciones**: doblajes regionales (Robotech para Macross; doblajes filipinos de Voltes V y Combattler V;
   doblajes italianos, franceses y latinoamericanos), versiones chinas o coreanas oficiales, y diferencias entre
   juegos SRW en inglés (OG vs. T vs. 30).

**Regla para elegir:**
1. Hay localización oficial de la franquicia, consolidada → esa.
2. Personajes y términos originales de Banpresto → la grafía de SRW OG en inglés.
3. No hay oficial → la grafía fan más extendida, siempre que respete la lectura japonesa. Si no hay ninguna clara →
   Hepburn sin macrón.
4. Las localizaciones regionales con **nombres cambiados** (Robotech, el doblaje filipino de Voltes V) cuentan como
   "otras traducciones", no como oficial, salvo que el fandom angloparlante de SRW las haya adoptado.
5. Siempre dentro de los límites en bytes (§2.1).

### Reglas de investigación

- Buscá en inglés **y** en japonés (Wikipedia en japonés, Pixiv Encyclopedia, sitios oficiales japoneses) para
  confirmar la lectura y la grafía de origen.
- **No inventes.** Si no encontrás algo, poné "no encontrado" y decí qué buscaste.
- **Sin URL, no hay decisión**: el punto va a "No resuelto". No pongas confianza **alta** sin una fuente oficial con URL.
- Una wiki fan es fuente **fan**, aunque cite material oficial. Si podés, citá la fuente primaria.
- Si las fuentes se contradicen, listalas todas y explicá por qué elegís una.
- Confianza: **alta** (fuente oficial clara, con URL), **media** (fan consolidado u oficial indirecto), **baja**
  (deducción).

## 4. Formato de la respuesta

Respondé en **español** (los nombres, en inglés y japonés). **Una tanda por respuesta**, en el orden de la lista;
esperá a que te pidan la siguiente. Respondé **todos** los puntos de la tanda (aunque sea con "no encontrado").

**Por cada punto**, un bloque así:

```
### A10 — ゲッター1/2/3
- Propuesta: **Getter-1** · forma corta: —
- Fidelidad: …
- Oficial: … (URL)
- Fans: … (URL)
- Otras traducciones: … (URL)
- Confianza: alta | media | baja
- Riesgos / notas: (conflicto con otro término, límite de bytes, etc.)
```

Si un punto tiene varias preguntas o varios nombres, respondé cada uno.

**Al final de cada tanda**, tres secciones:
1. **CSV** en un bloque de código (separador `;`, una fila por nombre decidido) para importar:
   `id;jp;propuesta_en;forma_corta;tipo_fuente;fuente_principal;url;confianza;nota`
   `tipo_fuente` = `oficial_franquicia` | `oficial_srw` | `fan` | `literal`. **La columna `url` no puede quedar vacía.**
2. **Alertas**: decisiones ya tomadas (§2.2) con evidencia fuerte en contra (con URL).
3. **No resuelto**: puntos sin fuente suficiente, con lo que buscaste.

## 5. Lista de decisiones pendientes

Prioridad: 🔴 cambia cientos o miles de líneas · 🟡 media · ⚪ baja. Entre paréntesis, apariciones aproximadas en
el texto del juego cuando se conocen. "Hoy" = valor provisorio actual del proyecto. Los IDs son los de la ronda 1
(faltan los que ya se decidieron).

### Tanda 1 — Términos, organizaciones, rangos y epítetos

| ID | JP | Hoy / opciones | Dónde · límite | Qué resolver |
|---|---|---|---|---|
| A10 🔴 | ゲッター1/2/3, 真ゲッター1… | *Getter 1* (hoy, Akurasu) · *Getter-1* · *Getter One* | unidades, armas, diálogo | Grafía de un SRW en inglés que incluya Getter Robo (TV o *Shin Getter Robo*), de Discotek y del sitio oficial. |
| B03 🟡 | 第１３独立外部部隊 (10) | *13th Autonomous Squadron* | diálogo | Nombre formal de Londo Bell en Alpha. ¿Hay traducción fan establecida (Akurasu, traducciones de Alpha/Alpha Gaiden)? |
| B05 🟡 | コープランダー隊 (13) | *Copelander Team* · *Cope Lander Squad* | diálogo (Raideen) | Grafía de Discotek (*Brave Raideen*). |
| B06 🟡 | 科学要塞研究所 (8) | *Fortress of Science* · *Fortress of Science Research Institute* | diálogo (Great Mazinger) | Grafía de Discotek / SRW en inglés. |
| B07 🟡 | 特脳研 (37) | *Special Brain Research Institute* · *SBRI* · *the Institute* | diálogo (SRX) | ¿Existe en OG en inglés? |
| F07 🟡 | 特佐 (13, OZ) | *Special Lieutenant*; en trato *Lieutenant Zechs* | diálogo | Término oficial de Gundam Wing (doblaje de Cartoon Network / Bandai). |
| F08 🟡 | Nerv: 一尉, 三佐, 司令, 副司令 | *Captain*, *Major*, *Commander*, *Sub-Commander* | diálogo | Oficial de ADV **y** de Netflix (Misato, Gendo, Fuyutsuki). Si difieren, decí cuál y por qué. |
| F09 ⚪ | 副長 | *Vice Captain* · *XO* · *First Officer* | diálogo; rótulo corto de operador | Oficial de Gunbuster y del resto de las series. |
| F10 ⚪ | Abreviaturas | *Lt.*, *Capt.*, *Cmdr.* (ya fijada para Bright), *Col.*, *Gen.* | diálogo | Qué abreviaturas usan OG y los oficiales, para líneas justas de ancho. |
| G01 🟡 | 連邦の白い奴 | *the Federation's white mobile suit* · *the white one* · *the White Devil* (este es 白い悪魔) | diálogo | Frase oficial de Gundam en inglés (subtítulos/doblaje de 0079). |
| G03 ⚪ | 青き巨星 | *the Blue Giant* | diálogo | Confirmar (Ramba Ral). |
| G04 ⚪ | 先輩 (Maya → Ritsuko) | *senpai* · el nombre · *Doctor* | diálogo | Cómo lo resuelven ADV y Netflix. |
| G05 ⚪ | お姉様 (Gunbuster) | *Onee-sama* (excepción prevista) | diálogo | Cómo lo dejan los subtítulos oficiales. |

### Tanda 2 — Giant Robo, Voltes V, Combattler V, Raideen, Dancouga

| ID | Serie | JP → hoy | Qué resolver |
|---|---|---|---|
| D03 🟡 | Voltes V | リー・カザリーン → *Katherine Rii* (provisorio; rótulo *Katherine*) · ド・ズール → *Do Zuhl* | **Grafía exacta en SRW 30 en inglés (DLC1)**, con URL o captura citada. Si SRW 30 usa otra (*Ri Kazarin*, *Katharine*, *Zuhl*…), proponela. ≤ 20 y rótulo ≤ 12. |
| D04 🟡 | Combattler V | ミーア → *Miia* · ロペット → *Ropett* · 南原博士 → *Dr. Nanbara* | ¿*Mia*? ¿*Lopet* / *Robet*? ¿*Professor Nanbara*? Combattler V también está en SRW 30: ¿cómo los escribe? ¿Existe doblaje o subtítulo oficial en inglés? |
| D05 🟡 | Giant Robo | 呉学人 → *Go Gakujin* · 鉄牛 → *Tetsugyu* · Ｑボス → *Q Boss* (glosario) / *Q-Boss* (hablantes) | Grafías del doblaje y los subtítulos oficiales (Manga Entertainment, Media Blasters, Discotek). Ya decidido: *Taiso*, *Shokatsuryo Komei*. |
| D06 🟡 | Giant Robo (Magnificent Ten, 十傑集) | 衝撃のアルベルト → *Alberto The Impact* (piloto) / *Shockwave Alberto* (unidad) · 素晴らしきヒィッツカラルド → *The Fabulous Fitzkarald* (23 bytes) · 眩惑のセルバンテス → *Cervantes the Dazzler* (21) · 混世魔王 樊瑞 → *Hanzui the Chaos Lord* (21) · 激動たるカワラザキ → *Kawarazaki The Stormy* (21) · オロシャのイワン → *Ivan the Terrible* | Epítetos **oficiales** en inglés (con URL a subtítulos/doblaje); mayúsculas coherentes (*the* / *The*); grafía de ヒィッツカラルド (*Fitzkarald*, *Fitzcarraldo*, *Hitzcarald*) y de 樊瑞 (*Hanzui* / *Fan Rui*). Un mismo nombre para piloto y unidad. **Además**, forma corta ≤ 20 para L04–L07 (abajo) y rótulo ≤ 12. |
| D07 🟡 | Brave Raideen | 神宮寺力 → *Chikara Jinguji* (la guía decía *Rikiya*) · 桜野マリ → *Marie Sakurano* · バラオ → *Barao* · 化石獣バストドン → *Fossil Beast Bastodon* (unidad) / *Bastdon* (Akurasu) · ベロスタン → *Berostan* | Grafías de Discotek y de SRW en inglés que incluya Raideen (verificá cuál). ¿Cómo se lee 力 en la serie? Ya decidido: *Raideen*, *Brave Raideen*. |
| D09 ⚪ | Dancouga | ゲラール → *Grawl* | Grafía oficial (Blu-ray, SRW 30). Ya decidido: *Dancouga*. |

Formas cortas (≤ 20 bytes) de los Magnificent Ten, ligadas a D06:

| ID | JP | Hoy (bytes) |
|---|---|---|
| L04 | 素晴らしきヒィッツカラルド | *The Fabulous Fitzkarald* (23) |
| L05 | 眩惑のセルバンテス | *Cervantes the Dazzler* (21) |
| L06 | 混世魔王 樊瑞 | *Hanzui the Chaos Lord* (21) |
| L07 | 激動たるカワラザキ | *Kawarazaki The Stormy* (21) |

### Tanda 3 — Dunbine y Gundam

| ID | Serie | JP → hoy | Qué resolver |
|---|---|---|---|
| D08 🟡 | Aura Battler Dunbine (**revisar la serie entera**) | ショウ・ザマ *Show Zama* (SRW X: *Sho Zama*) · マーベル・フローズン *Marvel Frozen* · チャム・ファウ *Chum Huau* · エル・フィノ *Elle Fino* · ベル・アール *Bell Earl* · ニー・ギブン *Neal Given* · キーン・キッス *Keen Kiss* · エレ・ハンム *Elle Hunm* · シーラ・ラパーナ *Ciela Lapana* · エイブ・タマリ *Abe Tamari* · カワッセ・グー *Kawase Gu* · リムル・ルフト *Rimul Luft* · トッド・ギネス *Tod Guines* · ガラリア・ニャムヒー *Garalia Nyamhee* · バーン・バニングス *Bern Bunnings* · ドレイク・ルフト *Drake Luft* · ビショット・ハッタ *Bishott Hate* · ジェリル・クチビ *Jeril Coochibi* · アレン・ブレディ *Allen Brady* · フェイ・チェンカ *Fei Chenka* · ミュージィ・ポー *Muisy Poe* · ショット・ウェポン *Shot Weapon* · ガラミティ・マンガン *Garamity Mangan* · ダー *Dar* · ニェット *Neet* · ルーザ・ルフト *Leeza Luft* · 黒騎士 *Black Knight*. Unidades: ブブリィ *Bubury* · ウィル・ウィプス *Will Wips* · ゲア・ガリング *Gea Garing* (Akurasu *Gyre-Garing*) · メット / ルフトン *met* / *rufton* | Fuente principal: **SRW X en inglés** (tiene Dunbine) y los subtítulos oficiales (Sentai Filmworks / ADV). Muchas grafías vienen de Akurasu y algunas parecen erratas (*Bishott Hate* por ハッタ, *Leeza* por ルーザ). ダー / ニェット son un chiste con el ruso *da* / *nyet*: ¿*Da* / *Nyet*? *Elle Fino* y *Elle Hunm* no pueden llamarse igual: ver K01. Unidades ≤ 21. |
| K01 ⚪ | Dunbine / Gundam ZZ | Rótulo *Elle* para エレ (*Elle Hunm*, Dunbine) y エル (*Elle Vianno*, Gundam ZZ); también エル・フィノ (*Elle Fino*, Dunbine) | ¿Hay grafías oficiales que los separen (*Ele*, *El*)? Rótulo ≤ 12. |
| D10 🟡 | Victory Gundam | カルル → rótulo *Karel*, nombre *Karlmann Dukartuse* · フラニー → *Franny* / *Francesca O'Hara* · ファラ・グリフォン → *Fuala Griffon* (en menús aparece ファラ solo) | Grafías oficiales de Bandai / gundam.info. |
| D11 🟡 | Gundam varios | ハサウェイ・ノア → *Hathaway Noa* · ベラ・ロナ → *Berah Ronah* · ミリィ・チルダー → *Milly Childer* | Confirmar la grafía oficial. Para ミリィ, confirmar también la serie (hoy figura como ZZ, sin confirmar). |
| E02 🟡 | Gundam Wing | ガンダムデスサイズヘルカスタム: corta *Deathscythe H. Custom* · *Deathscythe Hell (EW)* | Forma corta oficial o más usada, ≤ 21. |
| E03 🟡 | Gundam Wing | ガンダムエピオン・バード形態: *Gundam Epyon (Bird Mode)* (literal del juego) · *(MA Mode)* (oficial) | ¿Nombre oficial del modo transformado? ≤ 21. |
| J03 ⚪ | Dunbine | Título *Aura Battler Dunbine* | Título oficial actual en inglés. |

### Tanda 4 — Macross, Evangelion, Gunbuster, Mazinger, originales de Banpresto y formas cortas

| ID | JP | Hoy / opciones | Límite | Qué resolver |
|---|---|---|---|---|
| D14 🟡 | EVA量産機 · 第7使徒イスラフェル甲/乙 | *Mass Production Evangelion* (unidad) / *Mass Produced EVA* (piloto) · *7th Angel Israfel A/B* (unidad) / *Israfel (A)/(B)* (piloto) | piloto ≤ 20, rótulo ≤ 12, unidad ≤ 21 | Término oficial (ADV / Netflix / sitio oficial) y cómo distinguir 甲/乙 (¿*A/B*, *α/β*, *Alpha/Beta*?). Un mismo término para piloto y unidad. |
| D15 🟡 | 宇宙怪獣・兵隊 / 高速型 / 上陸艇 / 混合型 / 合体怪獣 | unidad *Space Monster (Soldier) / (Fast) / (Lander) / (Mixed) / (Fused)*; piloto *Space Monster Troop / Fast Space Monster / Space Monster Lander / Hybrid Space Monster / Fused Space Monster* | piloto ≤ 20, unidad ≤ 21 | ¿Tienen nombres oficiales los subtipos en los subtítulos de Bandai Visual? Unificar unidad y piloto. |
| D16 🟡 | Naves y mechas Aerogater | ヘルモーズ *Hermodr* (Cyath *Helmoze*, otra guía *Helmoz*) · メギロート *Megillot* (¿*Megilot*?) · ズフィルード *Zfylud* · ジュデッカ *Judecca* · ゼカリア *Zechariah* · ハバクク *Habakkuk* (la fuente dice *Habbakuk*) · エゼキエル *Ezekiel* · アンティノラ *Antenora* · アストラナガン *Astranagant* · グルンガスト弐式 *Grungust Type 2* (¿*Type-2*?) · ドゴス・ギア *Dogosse Giar* / *Dogos Gear* (Zeta) | unidad ≤ 21 | Grafía de OG1/OG2 (Atlus), OGs y *The Moon Dwellers* en inglés; para ドゴス・ギア, Bandai. |
| E05 🟡 | 空戦ポッド | *Aerial Battle Pod* · *Gnerl* | ≤ 21 | ¿Es el *Gnerl* (fighter pod zentradi) oficial? |
| E06 🟡 | メルトランディ軍標準戦艦 · 中型砲艦 | *Meltrandi Standard Battleship* / *Medium Gunboat* (cortas *Meltran Battleship* / *Gunboat*) | ≤ 21 | ¿Nombres de clase oficiales en Macross? |
| E07 🟡 | トップリム · ボトムリム | *Top Rim* / *Bottom Rim* | ≤ 21 | ¿De qué serie son y qué son? Su arma es ピンポイントバリアパンチ. ¿Partes de la Macross? |
| E08 🟡 | RX-7ジゼル | *RX-7 Giselle* · *RX-7 Gazelle* (Akurasu) | ≤ 21 | Serie y grafía oficial (ジゼル = *Giselle*). |
| E09 🟡 | ズガール (戦闘獣) | *Zugal* (unidad) vs *Battle Beast Zugul* (glosario) | ≤ 21 | Unificar; grafía de Discotek. |
| E10 🟡 | ピクドロン (el juego) / 光波獣ピグドロン (glosario) | *Pikudron* (unidad) vs *Lightwave Beast Pikadron* (glosario) | ≤ 21 | ¿ク o グ en el original? Grafía y el prefijo 光波獣. |
| L01 🟡 | カトル・ラバーバ・ウィナー | *Quatre Raberba Winner* (21) | ≤ 20 | Forma corta (¿cómo la abrevian los SRW en inglés?). El diálogo puede usar la larga. |
| L03 🟡 | 東山大三郎 | *Daizaburo Higashiyama* (21) | ≤ 20 | Forma corta. |
| L08 🟡 | ライディース・F・ブランシュタイン | *Raidiese F. Branstein* (21) | ≤ 20 | Forma corta (OG en inglés). |
| L09 🟡 | ラオデキヤ・ジュデッカ・ゴッツォ | *Laodicea Judecca Gozzo* (22) | ≤ 20 | Forma corta. |
| L10 🟡 | ネオ・ジオン強化兵 | *Neo Zeon Cyber Soldier* (22) | ≤ 20 | Forma corta coherente con *Cyber Soldier*. |
| L11 🟡 | ザンスカール強化兵 | *Zanscare Cyber Soldier* (22) | ≤ 20 | Ídem. |

### Tanda 5 — Espíritus, habilidades y rótulos de menú

Regla: OG en inglés primero; después T, 30, V, X e Y. Indicá qué juego usa cada nombre.

| ID | JP | Hoy | Alternativas |
|---|---|---|---|
| H02 | 挑発 | *Provoke* | *Taunt* |
| H03 | 隠れ身 | *Cloak* | *Stealth*, *Hiding* |
| H04 | 奇襲 | *Raid* | *Ambush*, *Surprise Attack* |
| H05 | 奇跡 | *Miracle* | — |
| H06 | 捨て身 | *Sacrifice* | *Desperate*, *Reckless*, *Abandon* (el efecto no es un sacrificio: verificarlo) |
| H07 | 復活 | *Revive* | — |
| H08 | 換装 (habilidad de unidad) | *Re-Equip* (confianza baja) | *Swap Parts* (sin confirmar), *Exchange*: nombre oficial en SRW en inglés, con URL |
| H09 | HP回復(小) / (大) · EN回復(小) / (大) | *HP Regen (S)/(L)*, *EN Regen (S)/(L)* (menús) vs *HP Recovery* / *EN Recovery* (glosario) | Nombre oficial OG / T / 30 y forma corta |
| H10 | 恋人 (rótulo) | *Partner* | *Lover* |
| H11 | Tipos de movimiento: 水中 · 地中 · 水上 (≤ 7 bytes) | — | *Underwater* / *Sea* · *Underground* / *Dig* · *On Water* / *Water* |
| H12 | Rótulos de ficha (≤ 4–12 bytes): ユニット能力, 修理費, タイプ, 機動力, 運動性, 機甲 (¿装甲?), 限界, サイズ, 地形, 空/陸/海/宇, 武器性能, 武器名, 攻撃力, 射程, 命中, 弾薬, 地形適応, 必要気力, 消費EN, 必要技能, クリティカル補正, パイロット能力, 撃墜数, 資金, 経験値 | *Unit Stats, Repair Cost, Type, Move, Mobility, Armor, Limit, Size, Terrain, Air/Land/Sea/Space, Weapon Stats, Weapon, Attack, Range, Hit, Ammo, Terrain, Will, EN Cost, Req. Skill, Critical, Pilot Stats, Kills, Funds, EXP* | Contrastar el bloque con OG y OGMD / T; formas cortas ATK, RNG, HIT, CRT. Solo marcar las que difieren. |

### Tanda 6 — Títulos de misión, nombres de series y rótulos repetidos

Títulos de misión que citan episodios. Buscá el **título oficial en inglés** de cada episodio (para Evangelion, el de
ADV **y** el de Netflix, por separado) y decí si conviene usarlo o dejar el literal. Hoy la regla es "literal, salvo
que el oficial sea casi igual".

| ID | JP | Hoy | Referencia |
|---|---|---|---|
| I01 | 使徒、襲来 | *Angel Attack* | Eva ep. 1 |
| I02 | 決戦、第２新東京市 | *Showdown in Tokyo-2* | Eva ep. 6 (el original es 第3; Alpha lo cambia a 2) |
| I03 | 瞬間、心かさねて | *Hearts in Unison* | Eva ep. 9 |
| I04 | 静止した闇の中で | *In the Still Darkness* | Eva ep. 11 |
| I05 | 奇跡の価値は | *The Value of a Miracle* | Eva ep. 12 |
| I06 | 男の戰い | *A Man's Fight* | Eva ep. 19 |
| I07 | せめて、人間らしく | *At Least, Like a Human* | Eva ep. 22 |
| I08 | 最後のシ者 | *The Final Messenger* | Eva ep. 24. **Juego de palabras**: シ者 = 使者 (mensajero) / 死者 (muerto). Proponé una adaptación que conserve el doble sentido. |
| I09 | Ａｉｒ | *Air* | *The End of Evangelion*, ep. 25' |
| I10 | シト新生 | *Death and Rebirth* | película de Eva (título oficial); シト = 使徒 / 死と |
| I11 | ブービー・トラップ · カウント・ダウン · スペース・フォールド · リン・ミンメイ · トランス・フォーメーション · バイバイ・マルス · ミス・マクロス · ファースト・コンタクト | *Booby Trap, Countdown, Space Fold, Lynn Minmay, Transformation, Bye-Bye Mars, Miss Macross, First Contact* | Macross TV: confirmar los títulos oficiales. |
| I12 | 愛・おぼえていますか | *Do You Remember Love?* | película de Macross |
| I13 | 少女が見た流星 | *The Shooting Star She Saw* | Gundam Wing ep. 1 |
| I14 | 女王リリーナ | *Queen Relena* | Gundam Wing |
| I15 | ダカールの日 | *Day of Dakar* | Zeta Gundam ep. 37 (¿*The Day of Dakar*?) |
| I17 | レッツ!コンバイン · 獣を超え、人を超え、いでよ神の戦士 · 魔神皇帝 | *Let's Combine!* · *Beyond Beast, Beyond Man, Arise, Warrior of God* · *Demon God Emperor* | Frases de Combattler V, Dancouga y Mazinkaiser: ¿hay versión oficial en inglés? |

Nombres de series y rótulos de hablante repetidos:

| ID | Tema | Hoy | Qué resolver |
|---|---|---|---|
| J04 | ジャイアントロボ THE ANIMATION | *Giant Robo: The Day the Earth Stood Still* | Título oficial. |
| J05 | 超電磁ロボ コン・バトラーV, 超電磁マシーン ボルテスV, 無敵鋼人ダイターン3, トップをねらえ!, 魔装機神 | *Super Electromagnetic Robo Combattler V*, *Super Electromagnetic Machine Voltes V*, *Invincible Steel Man Daitarn 3*, *Aim for the Top! Gunbuster*, *Masou Kishin: The Lord of Elemental* | Marcar solo los que difieren del título oficial en inglés. |
| K02 | Rótulo *Hayato* | 隼人 (Hayato Jin, Getter Robo) · ハヤト (Hayato Kobayashi, Zeta Gundam) | ¿Hay grafías oficiales que los separen? Rótulo ≤ 12. |
| K03 | Rótulo *Rei* | レイ (Rei Ayanami, Eva) · 麗 (Rei Asuka, Raideen) | Ídem. |
| K04 | Rótulo *Shiro* | シロ (gato de Masaki, Masou Kishin) · シロー (Shiro Kabuto, Mazinger Z) | Ídem. |
| K05 | Rótulo *Kenzo* | ケンゾウ (Kenzo Kobayashi, SRX) · 剣造 (Kenzo Kabuto, Mazinger) | Ídem. |

<!-- ================= FIN DEL PROMPT ================= -->
