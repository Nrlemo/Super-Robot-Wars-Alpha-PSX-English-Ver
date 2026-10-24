# Prueba en el juego: variante del protagonista (#34, C7)

ISO: `variantes_test_v01` (RetroArch, carpeta SRWA). Generada por `tools/src/mk_variantes_test.py` (+ `script_bin.py build`
+ `build_iso.py`; EXE VWF y fuente de `build/`). Cada línea `$n` / `$l` de SCRIPT.BIN dice **su número de variante** en
vez del texto (11.918 líneas `$n` y 3.152 `$l`, 15.070 en total; el resto sigue en japonés):

- `$n: V3 (m shy) #234.1653`  → el juego eligió la variante 3 (varón tímido) del bloque 1653 del script 234.
- `Partner: L5 (matches V5) #…` → línea de la pareja, variante 5.

Tabla de variantes (referencia/protagonistas.md §1): 1 varón serio · 2 varón frío · 3 varón tímido · 4 varón alegre ·
5 mujer seria · 6 mujer fría · 7 mujer tímida · 8 mujer alegre.

## Checklist

Anotá para cada caso: cara elegida, personalidad elegida (texto japonés del menú, en orden 1–4), y qué `V?` / `L?`
aparece (con una captura de una escena con `$n` basta; el número de bloque `#script.bloque` ayuda a comparar).

1. [ ] **Preajuste por defecto** (p. ej. Bullet: cara de varón 1 + personalidad 1) → esperado `V1`.
2. [ ] **Cara de Bullet + personalidad 3 (内気で心優しい, tímida)** → si decide la personalidad: `V3`; si decide la cara: `V1`.
3. [ ] **Cara de mujer + personalidad 1** → esperado `V5` (género de la cara, personalidad 1); si sale `V1`, el género no cuenta.
4. [ ] **Cara de mujer + personalidad 4** → esperado `V8`.
5. [ ] **Pareja** (`恋人設定`): con el protagonista del caso 2, ¿qué `L?` sale? Esperado `L3` (la pareja "de la variante 3").
       Si la pantalla deja cambiar la personalidad de la pareja, probar una distinta y ver si `L?` cambia.
6. [ ] Repetir 2 con otra combinación cruzada (p. ej. cara de Kusuha + personalidad 2) para descartar coincidencias.
7. [ ] (Opcional) ¿el `$n` cambia dentro de la misma partida si se carga otra memory card? (solo si algo no cuadra).

Escena para mirar: la más rápida con `$n` es la de la ruta CP12 (`saves/cards/CP12-INT-E62-mixta-1714.mcd`,
intermisión → 次のマップへ; script 234 tiene 40 líneas `$`, empieza en el bloque `#234.1653`), pero esa tarjeta ya tiene un
protagonista fijo: para los casos 2–6 hay que empezar **partida nueva** y llegar a la primera intermisión con `$n`
(script 1, escena de la escuela de Kouji, o la que aparezca primero según la ruta).

## Al terminar

Pasame el resultado (una línea por caso) y actualizo `traduccion/referencia/protagonistas.md`,
`work/notes/guia_estilo_personajes.md` §3 y §7.1, `script_bin.md` ("Pendiente") y marco C7 en
`traduccion/DECISIONES_PENDIENTES.md`, y cierro #34.
