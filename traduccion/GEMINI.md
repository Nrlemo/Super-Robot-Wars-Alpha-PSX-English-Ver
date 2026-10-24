# Traducción automática con Gemini (GitHub Actions)

Un lote = una rama `traduccion/...` = un PR. El Action saca el lote de `work/dump/`, lo traduce con la API de Gemini
(por tandas de 40 filas, con el prompt `PROMPT_API.md` + guía de estilo + personalidades + glosario del lote), lo valida
con `check_text` (bytes/píxeles/líneas/variables/hablante), **reintenta las filas que fallan** y commitea el `.jsonl`
traducido y un `.informe.md` (notas, DUDOSO, errores sin resolver, tokens) en la rama. Se revisa en el PR y se mergea.

## Configurar (una sola vez)
1. Secreto: `gh secret set GEMINI_API_KEY` (la clave de Google AI Studio).
2. Ajustes del repo → Actions → General: permisos de lectura/escritura del workflow y **Allow GitHub Actions to create pull requests**.
3. Opcional: variable `GEMINI_MODEL` (por defecto `gemini-3.1-pro-preview`) y `GEMINI_CHUNK` (40).
4. Opcional pero recomendado: secreto `BOT_TOKEN` (PAT con contents + pull-requests). Con el `GITHUB_TOKEN` por defecto los
   pushes y PR del bot **no disparan** `check.yml`; con el PAT sí, y se puede exigir ese check para mergear.

## Workflows
| Workflow | Cuándo | Qué hace |
|---|---|---|
| `traducir.yml` | manual (formato + spec) o push a `traduccion/**` | un lote → rama, traducción, validación, commit, PR en borrador. En push traduce las filas sin `en` de los lotes cambiados (si no hay ninguna, no llama a la API) |
| `traducir_cola.yml` | manual | planifica con `gemini_queue.py` los lotes pendientes (saltea los que ya tienen rama `traduccion/*`), lanza hasta N con P en paralelo |
| `integrar.yml` | push a `main` que cambie lotes | `lote.py integrar` (valida) de los lotes mergeados → commit del volcado `work/dump/` |

Formatos y ramas: `snmsg` = **un nivel/ruta** (`traduccion/mapa-b007`, spec `--bloque 7`, ver `referencia/misiones.csv`);
`script` = intermisión, escenas agrupadas (`traduccion/script-s7-10`, spec `7-10`; no hay tabla escena → nivel);
`bxclist` = batalla (`traduccion/bxclist-0-9`, spec `0-9`, pilotos); `deadmess` y `em` (ya integrados).
Los lotes a mano/otra IA siguen sirviendo: `traduccion/paquetes/`.

## Local
```
GEMINI_API_KEY=... work/tools/gemini_job.sh snmsg "--bloque 7"        # saca el lote, traduce, valida
python3 work/tools/src/gemini_translate.py LOTE.jsonl --dry-run        # tamaño del prompt, sin llamar a la API
GEMINI_EXTRA="--mock --limit 30" work/tools/gemini_job.sh script 3    # prueba del mecanismo sin API
python3 work/tools/src/gemini_queue.py --formatos snmsg --max-trabajos 5   # plan de trabajos
```
Cada lote se puede releer y corregir a mano sobre la misma rama (el push solo traduce filas vacías).
Costo: se mide en el informe (`tokens in/out`); empezar con `max_trabajos: 1` para calibrar antes de lanzar la cola.

## Motor alternativo: Claude

`motor` (en `traducir.yml` y `traducir_cola.yml`) elige quién traduce; el resto del pipeline (lotes, validación, informe, PR) es igual.

| Motor | Secreto | Cobra | Notas |
|---|---|---|---|
| `gemini` (defecto) | `GEMINI_API_KEY` | API de Google | |
| `claude-cli` | `CLAUDE_CODE_OAUTH_TOKEN` (`claude setup-token` en tu máquina) | cupo de tu suscripción de Claude | Consume el límite de 5 h/semanal; conviene lotes chicos (`max_trabajos` bajo). Modelo por defecto `claude-sonnet-5`. |
| `anthropic` | `ANTHROPIC_API_KEY` | API de Anthropic por token | Con caché del prompt. |

```
gh secret set CLAUDE_CODE_OAUTH_TOKEN -R Nrlemo/srw-alpha-psx-en
gh workflow run traducir_cola.yml -R Nrlemo/srw-alpha-psx-en -f mapa=false -f batalla=true -f max_trabajos=3 -f motor=claude-cli
```
