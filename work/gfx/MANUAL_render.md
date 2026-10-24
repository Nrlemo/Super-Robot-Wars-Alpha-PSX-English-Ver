# Manual rápido: generar los gráficos en inglés por script

El script `work/tools/src/gfx_render.py` dibuja el inglés sobre cada gráfico japonés **copiando su estilo** (colores
de la paleta original, contorno, degradé, sombra). Vos solo editás textos en CSV; el script genera los PNG, y
`gfx_entrega.py check` los valida. Todo se corre desde la raíz del repo.

```bash
cd ~/"Documentos/SRW Alpha (PSX) Trad"        # o el checkout donde estés
PY=work/.venv/bin/python
```

## 1. Qué editar

| Grupo | Piezas | Archivo a editar | Qué viene ya cargado |
|---|---|---|---|
| Títulos de escenario y "Stage N" | G01–G13 | **Nada** (ver abajo): los genera `subtitle.py` con el inglés de `misiones.csv` | Todo |
| Prólogo | G14–G17 | `work/gfx/render/prologo_en.txt` | Nada: pegá el texto en inglés (párrafos separados por una línea en blanco) |
| Cartel del prólogo | G18 | `G18.csv` | Las 6 cajas; falta el inglés |
| Rótulos de interfaz | G19 | `G19.csv` | Inglés sugerido (glosario / menús) |
| Copyright | G20 | `G20.csv` | Las 12 cajas; falta el inglés (opcional) |
| Efectos de batalla | G22 | `G22.csv` | Inglés del glosario |
| Barreras | G23–G32 | `G23.csv` … `G32.csv` | Inglés del glosario |
| Mapa 「現在位置」 | G33–G36 | **`lugares_mapa.csv`** (lugares) · `G33.csv` … `G36.csv` solo la fila `H1` (cabecera `Location`) | Un renglón por recorte que usa el juego, con su inglés (ver abajo) |

Los CSV se abren con LibreOffice Calc (separador coma, UTF-8) o con cualquier editor de texto.

### Columnas del CSV

| Columna | Significado |
|---|---|
| `caja` | Nombre de la caja (`R04b` = renglón 4, segundo fragmento). Se ve en `out/Gxx_cajas.png` |
| `x, y, w, h` | Rectángulo donde se dibuja, en píxeles. **Nada sale de ahí.** |
| `jp` | El japonés (referencia; en títulos, entre corchetes el id de `misiones.csv`) |
| `en` | **Lo que se dibuja.** Vacío = queda el japonés. `-` = la caja queda vacía |
| `align` | `l` izquierda, `c` centro, `r` derecha |
| `font` | `game8` (fuente del juego, 8 px) o el nombre de un `.ttf` (`DejaVuSerif-Bold`, `DejaVuSans-Bold`…). Para usar otra, copiá el `.ttf` a `work/gfx/fonts/` y poné su nombre sin extensión |
| `size` | Tamaño **máximo** en px. Si el texto no entra a lo ancho, el script lo achica y después prueba la variante *Condensed* |
| `style` | `ramp` (antialias), `outline` (relleno + contorno) — no hace falta tocarlo |

## 2. Generar

```bash
$PY work/tools/src/gfx_render.py render             # todas las piezas
$PY work/tools/src/gfx_render.py render G05 G23     # solo algunas
```

Sale en `work/gfx/render/out/`:
- `Gxx.png` — la pieza en inglés (PNG indexado, listo para reinsertar)
- `Gxx_preview.png` — japonés | inglés, ampliado, para revisar
- `Gxx_cajas.png` — el original con cada caja numerada (para saber qué fila del CSV es cada texto)

Si algo no entra, el script lo avisa en la consola:
```
AVISO G03 R07a: "He Who Calls the Wind" no entra en 122×24 (mide 141×15)
```
Si un texto TTF no entra en un renglón, el script prueba solo **dos renglones** (corte más parejo; `|` en el
texto fuerza dónde cortar). Si ni así entra: abreviar, bajar `size`, usar una fuente más angosta, o retocar a
mano (paso 4).

### Lugares del mapa (G33–G36): cajas dinámicas
Las cajas las define cada escena en `SCRIPT.BIN` (#188), así que el inglés **no tiene que caber en el ancho del
japonés**: `mapa_lugares.py` dibuja cada texto grande (DejaVu Sans Bold 14, la altura de los kanji), lo acomoda en la
hoja y el build reescribe el recorte de cada escena. En `lugares_mapa.csv` solo se edita `en` (una fila por recorte:
algunas escenas muestran solo el principio del rótulo japonés y tienen su propia fila, p. ej. 連邦軍極東支部). Tope:
231 px por caja (3/4 de pantalla con el marco); si algo no entra, primero pasa a Condensed y después achica, y avisa.
`en` vacío = queda el japonés de ese recorte.

## 3. Validar

```bash
$PY work/tools/src/gfx_entrega.py check work/gfx/render/out
```
Tiene que decir `OK` en cada pieza. (El script ya respeta las reglas; esto confirma que no se rompió nada si
retocaste a mano.)

## 4. Retoques a mano (opcional)

Abrí `work/gfx/render/out/Gxx.png` en **Aseprite / LibreSprite / Grafx2** (o GIMP, con cuidado: exportar sin
"optimizar paleta"). Reglas: mismo tamaño, modo indexado, sin colores nuevos, sin tocar nada fuera de las cajas.
Guardá con el mismo nombre y volvé a correr el `check` del paso 3. **Ojo:** si después volvés a correr `render`,
el script pisa tus retoques de esa pieza; guardá una copia o retocá al final.

## 5. Entregar

Cuando estés conforme: commit de los CSV / `prologo_en.txt` (y de los PNG retocados a mano, si los hay, en
`work/gfx/render/out/` — esa carpeta no se versiona salvo que la agregues con `git add -f`) y avisame. Yo integro la
reinserción en el build (`gfx_entrega.py import`) y lo pruebo en el juego.

## Cosas a revisar sí o sí

- **Rótulos muy cortos** de G19 (`Will`, `Expert Pts`) y G22 (`Shield Defense`, `After Image`): con 8 px y contorno
  algunos no entran o se leen mal → abreviar (`Wil`, `Exp.Pts`, `Shield`, `Mirage`) o retocar.
- **Iconos con fondo** (G19 `I01`–`I05`, C/D/E/A de la batalla): la caja tiene que ser el interior exacto de la celda
  (14×14, sin el borde), porque el fondo se toma del anillo de la caja; si toca el trazo del kanji, sale transparente
  (se ve negro en el juego). Columna opcional `conservar`: índices de paleta (hex, separados por espacio) del arte que
  no es texto y no se borran (p. ej. el gancho de la D variante: `1 2 b`).
- **Barreras**: la mitad de arriba de las letras queda hueca (así es el original). Si no se lee, retocar.
- **Prólogo**: entran 84 renglones de 238 px (los párrafos se separan con una pausa del desplazamiento, no con un renglón en blanco); el script avisa si sobran. El largo del desplazamiento lo fija una tabla de `OVL/PRO_GRP.BIN` que `import` reescribe con la cantidad de renglones.

## Títulos de escenario (G01–G13): `subtitle.py`, automático

Los títulos no se dibujan en cajas: `work/tools/src/subtitle.py` (etapa `titles` del build) toma el `en` de
`traduccion/referencia/misiones.csv` (el mismo del menú de intermisión), lo dibuja en Liberation Serif Bold 20, lo
reparte en las hojas de `SUBTITLE.BIN` y **reescribe la tabla de recortes del juego** (overlay SNMP), así que el largo
del japonés no limita. Un título que no entra en pantalla (> 304 px) va en dos renglones, cortado en el espacio más
parejo. El encabezado 第N話 pasa a **Stage N** (como el menú: `Stage %d`).

- Para cambiar un título solo en la imagen o forzar el corte de renglón: agregá una fila a
  `work/gfx/render/titulos.csv` (`id` de `misiones.csv`, `jp` de referencia, `en` con `|` donde va el corte).
- Vista previa (cómo lo arma el juego, todos los títulos): `$PY work/tools/src/subtitle.py build - /tmp/tit` →
  `/tmp/tit/preview/titulos_*.png` (y en cada build: `work/build/<nombre>/titles/preview/`).
- Tope: 144 pedazos de hasta 256 px para los 128 títulos (hoy 136). Si un cambio lo pasa, el script lo dice.
