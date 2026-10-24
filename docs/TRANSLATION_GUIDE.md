# Translator's Guide — *Super Robot Taisen Alpha* (PSX) into your language

This guide explains how to use this project's tools to translate *Super Robot Taisen Alpha* (SLPS-02636, PlayStation,
2000) into **any language**, starting from the finished English translation, and how to publish the result as a
patch. It covers every tool in the kit: what it does, when you need it, and what never to touch.

Short version of the rules: **[TRANSLATING.md](../TRANSLATING.md)**.

---

## Contents

0. [The three requirements](#0-the-three-requirements)
1. [What you will make, and how big the job is](#1-what-you-will-make-and-how-big-the-job-is)
2. [Limits to know before you start](#2-limits-to-know-before-you-start)
3. [What you need](#3-what-you-need)
4. [Setup](#4-setup)
5. [Start your language: the pivot](#5-start-your-language-the-pivot)
6. [Where every text lives](#6-where-every-text-lives)
7. [Translating dialogue](#7-translating-dialogue)
8. [Batches and AI-assisted translation](#8-batches-and-ai-assisted-translation)
9. [Names: pilots, units, weapons, speakers](#9-names-pilots-units-weapons-speakers)
10. [Menus, dictionaries, titles, terrain, protagonist, memory card](#10-menus-dictionaries-titles-terrain-protagonist-memory-card)
11. [Graphics with text](#11-graphics-with-text)
12. [Validating](#12-validating)
13. [Building and testing](#13-building-and-testing)
14. [Publishing a release](#14-publishing-a-release)
15. [Staying in sync with upstream](#15-staying-in-sync-with-upstream)
16. [What never to touch](#16-what-never-to-touch)
17. [Troubleshooting](#17-troubleshooting)
18. [Tool reference](#18-tool-reference)
19. [Vocabulary and technical notes](#19-vocabulary-and-technical-notes)

> All commands run **from the root of your clone**. `$PY` below means the kit's Python environment:
> `PY=work/.venv/bin/python` (created by the setup). Most tools print their messages in **Spanish**, the project's
> working language; the kit's own entry points (`kit_setup.sh`, `kit.py`) speak English. Every tool explains its own
> usage in its docstring: `$PY work/tools/src/<tool>.py -h`, or read the top of the file.

---

## 0. The three requirements

There are exactly three, and they are the only conditions for using this kit:

1. **Fork this project** on GitHub ([Nrlemo/Super-Robot-Wars-Alpha-PSX-English-Ver](https://github.com/Nrlemo/Super-Robot-Wars-Alpha-PSX-English-Ver))
   and work in your fork. Keep the fork link: don't re-upload the files as an unrelated repository.
2. **Do not modify the thanks / dedication screen.** That is the screen shown at boot after the copyright notice,
   with a dedication and two QR codes (GitHub and Buy Me a Coffee). It is built by `work/tools/src/dedicatoria.py`,
   `work/patches/dedicatoria.asm` and the `dedicatoria` build stage: leave all three as they are, untranslated, and
   don't skip the stage. The CI step `ci_check.sh dedication` fails if those files change.
3. **Link my Buy Me a Coffee page, <https://buymeacoffee.com/srwa_en>**, in your fork's README and on every page
   where you publish or announce your patch. Keep `.github/FUNDING.yml` unchanged so your fork's **Sponsor** button
   points there.

You may credit yourself and your team anywhere else (README, release notes, announcements). And, as the law requires
anyway: distribute **patches only**, never disc images, BIOS files or files extracted from the game.

---

## 1. What you will make, and how big the job is

**The result** is an **xdelta patch** that players apply to their own copy of the Japanese disc
(*Super Robot Taisen Alpha (Japan) (v1.0)*, SLPS-02636), plus a `.cue` file and checksums. The build pipeline
produces all three in one command (§14).

**What the kit already solves for you:** extraction and byte-exact rebuild of every text format, compressed
containers (LZSS), a variable-width font (about 55 characters per line instead of 20), relocation of menu strings with
pointer fixing, the validator that measures every line in pixels exactly as the game draws it, the name-entry screen,
scenario-title graphics, text graphics re-rendering, and the disc image rebuild. You translate text in plain files;
the pipeline does the rest.

**How much text there is** (counted on the English script; "unique" = distinct Japanese lines):

| Content | Unique lines | All rows | English words (approx.) |
|---|---:|---:|---:|
| Intermission scenes (`script`) | 26,871 | 45,712 | 290,000 |
| Map dialogue (`snmsg`) | 18,755 | 32,288 | 187,000 |
| Battle quotes (`bxclist`) | 7,155 | 18,128 | 34,000 |
| Defeat lines, suspend lines, terrain names (`deadmess`, `em`, `mdata`) | 328 | 2,000 | 1,800 |
| **Dialogue total** | **~53,000** | **96,700** | **~514,000** |
| Character and robot encyclopedia (DC/DR) | 797 entries | | 50,000 |
| Menu strings | 967 | 1,382 placements | |
| Names (glossary: weapons, units, pilots, terms) | 1,739 | | |
| Speaker labels / scenario titles | 355 / 130 | | |
| Text boxes in graphics + prologue | 231 boxes | | 600 (prologue) |

About 19,600 scene lines are protagonist lines that exist in **8 variants** (gender × chosen personality), which is
why "all rows" is much larger than "unique lines". At 2,000–3,000 words a day, the dialogue alone is roughly
170–260 translator-days; AI-assisted batches (§8) shorten that a lot, but every line still needs a human read.

**What stays Japanese by design** (in the English version too): the end credits, song lyrics, FMV videos and the
sound-test screen.

---

## 2. Limits to know before you start

### 2.1 Character set: plain ASCII only

The game stores text in Shift-JIS (cp932), and the kit's English font defines only **printable ASCII**
(0x20–0x7E). In practice you can use:

- letters A–Z a–z, digits, and `! " # $ % & ' ( ) * + , - . / : ; < = > ? @ [ \ ] ^ _ `` ` `` | ~`
- `\n` for line breaks

You **cannot** use accented or special Latin letters today: **á é í ó ú à è ñ ç ã õ â ê ô ü ö ä ß œ ¿ ¡ « » €**,
em/en dashes, curly quotes or the `…` character. They don't exist in cp932, so the validator reports an `encoding`
error and several builders stop. Fullwidth symbols that *do* exist in cp932 (“ ” ‘ ’ … ―) are accepted but are drawn
with the 12 px Japanese font, look out of place and use up a limited pool of character cells: avoid them.

Also never type `{` or `}` (they introduce byte escapes) or the half-width marks `ﾞ` `ﾟ`.

**What you can do today:**

1. **Write without accents** (`decision`, `operacion`, `Ce n'est pas grave`), and use ASCII substitutes for
   punctuation (`?` instead of `¿`, `"` instead of `« »`). Many fan translations of this era did exactly this.
2. **Advanced, untested workaround: reuse the half-width katakana byte codes.** The byte range **0xA1–0xDD** (61
   codes) is drawn from cells of the font texture that the English text never uses. You could:
   - draw your letters in `work/font/en_8px.txt` as glyphs keyed by byte, e.g. `== 0xB1` for `á` (always use the
     hex form: `== á` would land on another cell). Glyphs are 11 rows high and at most 7 px wide; row 0 is the only
     room above a capital letter, so capital accents are cramped;
   - in your text, type the half-width katakana character that encodes to that byte (e.g. `ｱ` = 0xB1) wherever you
     want `á`, or keep real accents in your working copy and convert them with a find-and-replace script just before
     validating.

   The font stage and the validator pick up new glyphs and widths automatically. **Risks:** any Japanese that stays
   half-width kana (sound test, the katakana keyboard of the name editor, untranslated names) would show your letters
   instead; graphics drawn with the game font (§11) would show `?`; and nobody has tested this in the game yet. Test
   every screen.
3. **A proper solution needs code changes** (not implemented): one character-to-byte map used by every encoder
   (`sjis_text.encode`, `script_bin.encode_en`, `bxclist.py`, `mdata_bin.py`, `ovl_patch.encode`, the byte counts in
   `menus_draft.py`), plus `entry_patch.py` (ASCII-only default names), `csv_lint.py`, `dict_build.py` and the
   `game8` renderer in `gfx_render.py`. If you build it, please contribute it upstream.

Graphics rendered with TrueType fonts (scenario titles, map place names) can show accents natively; see §11.

Non-Latin scripts (Cyrillic, Greek) exist in cp932 as 12 px fullwidth characters: they encode, but they are wide,
untested, and limited by the same character-cell pool. Languages without spaces between words (Chinese, Japanese,
Thai) are not supported by the line-wrapping tools.

### 2.2 Space is measured in pixels

Each character has its own width (variable-width font). The validator measures every line in **pixels** with the
real font table; a line that is too wide is **cut by the game mid-word**. Window sizes:

| Window | Lines × width |
|---|---|
| Map dialogue (`snmsg`), defeat lines (`deadmess`), suspend lines (`em`) | 3 × 240 px |
| Intermission scenes (`script`) | 3 × 272 px |
| Battle quotes (`bxclist`) | 2 × 240 px |
| Encyclopedia (DC/DR) | 46 bytes per line |

A rough guide: 50–57 average characters per line in a 240 px box. Digits and the plain ASCII space inside menus are
a fixed 8 px wide.

### 2.3 Fixed-size fields

Some texts live in fixed slots: pilot names (full ≤ 20 bytes, short ≤ 12), unit names (≤ 21), weapon names (≤ 19),
terrain/place names (≤ 15), protagonist default names (≤ 8 letters), map dialogue (≤ 255 bytes per message). Every
field that may not fit has a *short form* column; the build uses it automatically and tells you when neither fits.

---

## 3. What you need

- **Operating system:** Linux (Debian/Ubuntu tested) or **Windows with WSL2** (Ubuntu). Native Windows is not
  supported (bash scripts, Linux binaries); macOS is untested (you'd have to build the tools yourself).
- **Packages** (Debian/Ubuntu names):
  ```bash
  sudo apt install python3 python3-venv git cmake g++ xdelta3 fonts-dejavu-core fonts-dejavu-extra fonts-liberation
  ```
  Python 3.12 or newer (3.14 is the tested version). `cmake` and `g++` build armips and mkpsxiso the first time.
- **Your own dump of the Japanese disc**, exactly this Redump image (the setup checks it):

  | | |
  |---|---|
  | Game | Super Robot Taisen Alpha (Japan) (v1.0), SLPS-02636 |
  | File | `Super Robot Taisen Alpha (Japan) (v1.0).bin` + `.cue` (single track, 646,374,288 bytes) |
  | SHA-1 | `cfce3c7a76f64269387fbb7b77e3bcfe41b723c6` |
  | MD5 | `8cc4b3af159d26d11cad46b136a5c833` |

- **Disk space:** about 2 GB for the extracted disc and tools, plus ~0.65 GB per build you keep.
- **An emulator** to test: DuckStation, PCSX-Redux or RetroArch (any PS1 core that loads `.cue`).
- Optional: a PlayStation BIOS of your own (only for the automated emulator routes, §13.3), and an API key if you
  want AI-assisted batches (§8).

---

## 4. Setup

### 4.1 Fork and clone

1. On GitHub, open <https://github.com/Nrlemo/Super-Robot-Wars-Alpha-PSX-English-Ver> and press **Fork**
   (requirement 1).
2. Clone your fork and add the original as `upstream`:
   ```bash
   git clone https://github.com/<you>/Super-Robot-Wars-Alpha-PSX-English-Ver.git
   cd Super-Robot-Wars-Alpha-PSX-English-Ver
   git remote add upstream https://github.com/Nrlemo/Super-Robot-Wars-Alpha-PSX-English-Ver.git
   ```
3. Copy your disc dump into the clone's root with its Redump names:
   `Super Robot Taisen Alpha (Japan) (v1.0).bin` and `Super Robot Taisen Alpha (Japan) (v1.0).cue`.
   They are ignored by git and never committed. If you keep the disc elsewhere, export its path instead (the `.bin`
   must sit next to the `.cue` with the same name):
   ```bash
   export SRW_JP_CUE="/path/to/Super Robot Taisen Alpha (Japan) (v1.0).cue"
   ```

### 4.2 Run the setup

```bash
work/tools/kit_setup.sh --tools
```

It takes a few minutes the first time and does seven steps (each one prints `ok` or stops with an explanation):

| Step | What it does |
|---|---|
| 1. Prerequisites | checks python3, git, cmake, g++ (and warns if `xdelta3` is missing) |
| 2. Python environment | creates `work/.venv` and installs `work/tools/requirements.txt` (numpy, Pillow, pycdlib, segno…) |
| 3. External tools | with `--tools`: clones and builds **armips** (MIPS assembler, pinned commit) and **mkpsxiso/dumpsxiso 2.30** (disc rebuild/extract) into `work/tools/src_ext/`, copies them to `work/tools/bin/` |
| 4. Original disc | finds your `.bin`/`.cue` and checks the SHA-1 |
| 5. Extract the disc | `dumpsxiso` → `work/iso_jp/` (104 files + `layout.xml` + `license_data.dat`) |
| 6. Restore | `kit.py restore` (below), then renders the text graphics into `work/gfx/render/out/` |
| 7. Toolchain check | `build.sh --null`: rebuilds the disc with no changes and checks it is byte-identical to yours; then `build.sh --dry-run` validates all text |

Run it again any time: every step skips what is already done. `--no-null` skips the one-minute identity check.

### 4.3 Why there is a "restore": the kit contains no game data

The public repository never contains the game's Japanese script. The six dialogue files in `work/dump/` are committed
with only each row's **keys** and **translation**; the Japanese text, which the tools need, is extracted from **your**
disc by `kit.py restore` and merged back by key. `restore` also regenerates the files that are pure game data (pilot
stats, unit data, dictionary layout, menu-string inventory, scenario map) and the derived files.

A git filter (`srwjp`, configured by `restore`, declared in `.gitattributes`) keeps it that way: **on disk** the dumps
have the Japanese, **in git** they don't. `git diff`, `git add` and `git commit` work normally and only ever see your
translation. CI checks it (`ci_check.sh nogamedata`).

> If you ever see an error from `kit.py clean`, the filter is working: run `$PY work/tools/src/kit.py restore` once
> and repeat your git command.

### 4.4 Your first build: the English game

```bash
work/tools/build.sh --selftest --name first
```

The result is `work/build/first_v01/first_v01.bin/.cue`: the English game, identical to the published English
release. Load the `.cue` in your emulator to check that everything works before you change anything.

---

## 5. Start your language: the pivot

Every tool treats a row whose `en` field is empty as "not translated yet". To start from the English, run once:

```bash
$PY work/tools/src/kit.py pivot
git commit -am "Start <language> translation: English moved to en_ref"
```

For every row of the six dialogue dumps, `pivot` moves the English into a new field, **`en_ref`**, and empties `en`.
From then on:

- **`en` is your language.** That is the only field you write. (The name stayed `en` because the whole pipeline
  reads that field; in your fork it simply means "the text that goes into the game".)
- **`en_ref` is the English reference.** Don't edit it.
- The builders use **`en` → `en_ref` → `jp`**: until you translate a row, the game shows the English, so your build
  is always playable and you can test as you go.
- Progress counters (`lote.py estado`, the `validate` stage summary) count only `en`, so they show your real
  progress, starting at 0 %.
- The batch tools give the AI and you the English as `ref` (§8).

`pivot --only snmsg,script` limits it to some formats. The other sources (menus, names, dictionaries, titles,
graphics) are small files you translate **in place**, overwriting the English (§9–§11).

---

## 6. Where every text lives

| What | Edit this file | Column / field | Limit | Then run | Build stage → game file |
|---|---|---|---|---|---|
| Intermission scene dialogue | `work/dump/script.jsonl` | `en` | 3 × 272 px | — | `script` → `BUSTUP/SCRIPT.BIN` |
| Map dialogue | `work/dump/snmsg.jsonl` | `en` | 3 × 240 px, 255 B | — | `snmsg` → `SNMAP/SNMSG.BIN` |
| Battle quotes | `work/dump/bxclist.jsonl` | `en` | 2 × 240 px | — | `bxclist` → `BATTLE/BXCLIST.BIN` |
| Defeat lines | `work/dump/deadmess.jsonl` | `en` | 3 × 240 px, 251 B | — | `deadmess` → `SNMAP/DEADMESS.BIN` |
| Suspend (quit map) lines | `work/dump/em.jsonl` | `en` | 3 × 240 px, 255 B | — | `em` → `SNMAP/EM.BIN` |
| Terrain / place names (map cursor) | `work/dump/mdata.jsonl` | `en` (every duplicate row) | 15 B | — | `mdata` → `SNMAP/MDATA.BIN`, `TEST/MDATA.BIN` |
| Pilot names (menus, status) | `work/glossary/glossary.csv` (category `pilot`), `work/glossary/pilot_names_manual.csv` | `en_final` / `en` | full 20 B, short 12 B | `pilot_bin.py fill` | `pilot` → `UNITPRAM/PILOT.BIN` |
| Speaker labels and short pilot names | `traduccion/referencia/hablantes.csv` | `en` | 12 B | `pilot_bin.py fill` | (inside dialogue) + `pilot` |
| Unit names | `work/glossary/glossary.csv` (category `unit`) | `en_final`, `en_short` | 21 B | — | `robot` → `UNITPRAM/ROBOT.RAF` |
| Weapon names | `work/glossary/glossary.csv` (category `weapon`) | `en_final`, `en_short` | 19 B | — | `robot` → `UNITPRAM/ROBOT.RAF` |
| Menus, spirits, skills, parts, system text | `work/translation/menus_map.txt` | `en`, `en_short` | original slot (auto-relocated) | `menus_draft.py` | `menus` → `OVL/*_GRP.BIN` |
| Character / robot encyclopedia | `work/translation/dict_src/dc_*.txt`, `dr_*.txt` | whole text | 46 B per line | `dict_build.py dc dr` | `dc`/`dr` → `OPTION/DC.BIN`, `DR.BIN` |
| Scenario titles | `traduccion/referencia/misiones.csv` (+ the same titles in `menus_map.txt`) | `en`, `en_corto` | 2 lines × 304 px | — | `titles` → `TITLE/SUBTITLE.BIN` |
| Protagonist default names | `work/translation/entry_en.csv` | `first_en`, `last_en`, `nick_en` | 8 letters, ASCII | — | `entry` → `OVL/ENTR_GRP.BIN` |
| Text in graphics | `work/gfx/render/Gxx.csv`, `lugares_mapa.csv`, `prologo_en.txt` | `en` | box size | `gfx_render.py render` | `graphics` |
| Map warnings (BARRIER HIT…) | `work/gfx/render/G37.csv` | `en` | A–Z, `-`, `!` only | `gfx_render.py render G37` | `graphics` |
| Memory card save title | `EXE_STRINGS` in `work/tools/src/build_all.py` | 3rd element | 47 B, fullwidth | — | `exe_strings` → `SLPS_026.36` |

**Generated files: never edit them by hand** (they are rebuilt and not committed in the kit):
`work/translation/menus_en.jsonl` (from `menus_map.txt`), `work/translation/dc_en.jsonl`/`dr_en.jsonl` (from
`dict_src/`), `pilot.jsonl`'s `full_en`/`short_en` (from the name files), `traduccion/referencia/generado/`
(reference tables for the batch tools), and everything in `work/gfx/render/out/`.

To regenerate all of them at once after editing names, menus or dictionaries:

```bash
work/tools/ci_check.sh generated
```

---

## 7. Translating dialogue

### 7.1 The files

Each dialogue dump is a **JSON Lines** file: one row per text, one row per line of the file. A row after the pivot,
on disk:

```json
{"script": 1, "inst": 12, "line": 0, "sub": 4, "jp": "甲児「ふわ～あ、やっと学校が終わった…。\n…」", "en": "", "en_ref": "Koji: Phew, school's finally over...\n…"}
```
(shortened here; real rows hold the whole box text)

| File | Row key (never change) | Notes |
|---|---|---|
| `script.jsonl` | `script` (scene) + `inst` | speaker is written inside the text: `Koji: ...`; `op: 128` rows are story choices |
| `snmsg.jsonl` | `id` (slot) | `speaker` is the Japanese reference; the label goes inside the text |
| `bxclist.jsonl` | `pilot` + `idx` | battle quotes, **no** speaker label (the game shows the face) |
| `deadmess.jsonl` | `slot` (= 2 × pilot + variant) | the game prints `Name: ` in front by itself |
| `em.jsonl` | `rec` | the speaker label goes inside the text |
| `mdata.jsonl` | `file` + `off` | the same Japanese name appears in many rows: translate all of them alike |

Edit them with any editor that keeps UTF-8 and one-row-per-line (VS Code, Kate, Notepad++, vim), or with your own
scripts. A JSON-aware approach (read row, set `en`, write row) avoids broken quotes.

### 7.2 Rules

1. **Edit only `en`.** Never touch `jp`, `en_ref` or the key fields: they are the address of the text in the game
   (`--selftest` stops the build if a row moved).
2. **`\n` is a line break.** Each window has 2 or 3 lines (§2.2); the validator measures every line.
3. **Variables:** keep exactly the same `$` variables as the Japanese row, no more, no fewer. They are replaced by
   the player's names: `$n`/`$N` protagonist/partner nickname, `$f`/`$F` first name, `$l`/`$L` surname (also
   `$m $M $s $S`). The validator reserves the width of the longest possible name.
4. **Speaker labels:** scenes, map dialogue and suspend lines start with `Name: ` (thoughts: `Name: (text)`); lines 2
   and 3 are not indented. Labels come from `traduccion/referencia/hablantes.csv` (§9). Battle quotes and defeat
   lines have no label.
5. **Story choices** (`script` rows with `op: 128`, and map decisions in `snmsg` whose Japanese contains `選択`): keep
   one option per line, exactly as many lines as the Japanese, no speaker label.
6. **Protagonist variants:** the same scene line exists up to 8 times, one per protagonist (gender × personality:
   serious & just, calm & brilliant, shy & kind, cheerful optimist). `lote.py` tells you which variant each row is
   (§8) so you can keep each one's voice.
7. **Characters:** ASCII only (§2.1); straight quotes `"` `'`, three dots `...`, hyphen `-`. No `{ }`, `ﾞ`, `ﾟ`.
8. **Identical Japanese, identical context:** the same line often appears in several places. Search before
   changing a line: `grep -c "text" work/dump/script.jsonl`.

### 7.3 Useful commands

```bash
# find a line you saw in the game (by English, your language or Japanese)
grep -n "school's finally over" work/dump/script.jsonl | cut -c1-300

# validate one format (0 errors needed); results in work/build/check_text.csv
(cd work && ../work/.venv/bin/python tools/src/check_text.py --only script)

# propose line breaks for a sentence that doesn't fit
(cd work && ../work/.venv/bin/python tools/src/check_text.py --wrap-text "Your long sentence here" --format snmsg)

# re-break lines that were cut mid-sentence, using real pixel widths (writes en with --apply)
$PY work/tools/src/reflow_candidates.py script            # report
$PY work/tools/src/reflow_candidates.py script --apply    # rewrite
```

---

## 8. Batches and AI-assisted translation

The English translation was produced in **batches**: a slice of a dump is extracted with its context, translated
(by a person or an AI), validated, and integrated back. The same tools work for your language.

### 8.1 `lote.py`: batches with context

```bash
$PY work/tools/src/lote.py sacar script 1-3          # scenes 1 to 3
$PY work/tools/src/lote.py sacar snmsg --bloque 1    # map messages of SNDATA block 1 (scenario 1)
$PY work/tools/src/lote.py sacar snmsg 47-120        # a range of map-message slots
$PY work/tools/src/lote.py sacar bxclist 0-9         # battle quotes of pilots 0–9
$PY work/tools/src/lote.py sacar deadmess 0-99       # (and: sacar em 0-29)
$PY work/tools/src/lote.py terminos traduccion/lotes/script/script_001-003.jsonl
$PY work/tools/src/lote.py validar  traduccion/lotes/script/script_001-003.jsonl
$PY work/tools/src/lote.py integrar traduccion/lotes/script/script_001-003.jsonl
$PY work/tools/src/lote.py estado                    # progress per format
```

- `sacar` ("extract") writes a batch to `traduccion/lotes/<format>/…jsonl`: each row has its keys, `jp`, an empty
  `en`, **`ref` (the English)**, and `ctx` (speaker, protagonist variant 1–8, scenario, message type). Next to it:
  `.reparto.tsv` (the cast: personality and voice of each speaker) and `.terminos.tsv` (glossary terms that appear in
  the batch).
- You (or the AI) fill `en` in the batch file.
- `validar` ("validate") runs the validator plus a speaker-label and glossary-term check.
- `integrar` ("integrate") copies the `en` values into `work/dump/` (refusing if `validar` finds errors, unless
  `--forzar`) and re-breaks lines that were cut mid-sentence.
- Batches contain Japanese, so `traduccion/lotes/` is **ignored by git** in the kit: the result lives in
  `work/dump/`, which is what you commit.

### 8.2 AI translation with `gemini_translate.py`

`gemini_translate.py` sends a batch to an AI model in chunks, validates the answer and asks for repairs of the lines
that don't fit:

```bash
export GEMINI_API_KEY=...            # or TRAD_BACKEND=anthropic + ANTHROPIC_API_KEY
export TARGET_LANG="Brazilian Portuguese"
$PY work/tools/src/gemini_translate.py traduccion/lotes/script/script_001-003.jsonl --dry-run   # prompt size only
$PY work/tools/src/gemini_translate.py traduccion/lotes/script/script_001-003.jsonl
work/tools/gemini_job.sh script 1-3  # extract + translate + validate in one go
```

Settings: `GEMINI_MODEL`, `--chunk N` (rows per request), `--repair N` (repair rounds), `--limit N`; backends
`TRAD_BACKEND=gemini|anthropic|claude-cli` with `CLAUDE_MODEL`. It resumes where it stopped (rows with `en` are
skipped) and writes a report next to the batch (`.informe.md`).

**Before using it, adapt the prompt to your language.** The system prompt is built from:

- `traduccion/PROMPT_API.md`: role, input/output format and hard format rules. It is written for English output:
  rewrite the role and style sections for your language (keep the format rules and the JSON contract). It already
  explains `ref`: the published English line, which the model should translate, using `jp` for tone and ambiguity.
- `work/notes/guia_estilo_personajes.md` (Spanish): each character's voice and speech habits.
- `traduccion/referencia/protagonistas.md`, the batch's `.reparto.tsv` (English voice notes in `hablantes.csv`'s
  `voz_en`), `.terminos.tsv` and the reference tables.
- `TARGET_LANG` sets the language named in the section headers.

`traduccion/PROMPT.md` is the equivalent prompt for working with an interactive assistant, and `traduccion/GEMINI.md`
describes how the English batches were run. **Every AI line needs a human review**: names, tone, jokes, and the
8 protagonist variants are where machine output fails.

The upstream project also ran batches on GitHub Actions; those workflows are not part of the kit, because a batch
contains Japanese text and must not be committed. Run batches locally.

---

## 9. Names: pilots, units, weapons, speakers

Most fans expect official or established names, which usually stay the same across languages (*Amuro Ray*,
*Mazinger Z*, *Getter Robo*). Change names only where your language has its own established localization.

- **`work/glossary/glossary.csv`** is the master list of names (columns `category, series, jp, en_final, en_short,
  status, …`; categories `pilot`, `unit`, `weapon`, `spirit`, `pilot_skill`, `part`, `ui`…). In the kit it is a
  source file: edit `en_final` (and `en_short` when the full form doesn't fit) and set `status` to `manual`.
  `decisiones.csv`, `manual.csv`, `units_en.csv` and `weapons_*.csv` are the upstream research behind it; the kit
  doesn't regenerate the glossary from them (`glossary_build.py` needs the reference pages that are not part of the
  kit).
- **Pilot names** (status screens, unit lists): full name ≤ 20 bytes and short name ≤ 12, written to
  `UNITPRAM/PILOT.BIN` from `pilot_names_manual.csv` (`campo` = `full`/`short`, `jp`, `en`, `motivo`) when present,
  else from the glossary; the short name comes from `hablantes.csv`. After editing, run `$PY work/tools/src/pilot_bin.py fill`
  (or `ci_check.sh generated`).
- **Speaker labels** (`Name:` in dialogue) and short pilot names: `traduccion/referencia/hablantes.csv`, column `en`
  (≤ 12 bytes). `lote.py validar` checks that dialogue lines start with these labels.
- **Units** (≤ 21 bytes) and **weapons** (≤ 19 bytes): `glossary.csv`. If neither `en_final` nor `en_short` fits,
  the `robot` stage fails and names the culprit; `work/build/<N>/logs/robot_names.csv` lists what was used.
- **Renaming a character everywhere:** change the glossary row, the speaker label, `pilot_names_manual.csv` if
  needed, then replace the name inside the dialogue (whole words, check the diff), the encyclopedia (`dict_src/dc_*.txt`
  headers and text) and menus that mention it:
  ```bash
  grep -c "Old Name" work/dump/{script,snmsg,bxclist,deadmess,em}.jsonl
  sed -i 's/\bOld Name\b/New Name/g' work/dump/{script,snmsg,bxclist,deadmess,em}.jsonl   # touches en AND en_ref: check git diff
  work/tools/ci_check.sh generated
  (cd work && ../work/.venv/bin/python tools/src/check_text.py)
  ```

---

## 10. Menus, dictionaries, titles, terrain, protagonist, memory card

### 10.1 Menus (`work/translation/menus_map.txt`)

One line per unique Japanese string, `jp || en || en_short || notes` (lines starting with `#` are comments). A string
is translated everywhere it appears (9 overlays + the executable). After editing:

```bash
$PY work/tools/src/menus_draft.py          # regenerates menus_en.jsonl and says whether each string fits
```

Strings that don't fit in their original slot are **relocated** automatically (pointers fixed); some memory zones
are full, so a much longer string may fall back to `en_short`. Centred or column layouts are re-positioned by
`layout_patch.py`. After a build, `work/build/<N>/menus/report.csv` shows where each string went and which ones used
the short form (`$PY work/tools/src/menus_short_list.py` lists them). Spirit commands, pilot skills and parts are
menu strings too.

### 10.2 Character and robot encyclopedia (`work/translation/dict_src/`)

`dc_*.txt` (characters) and `dr_*.txt` (robots) are plain text: a header line per entry (`#id Name | Short | Voice
actor` for characters, `#id Name` for robots) followed by one paragraph per line. Write freely; the tool re-flows the
text to 46 bytes per line:

```bash
$PY work/tools/src/dict_build.py dc dr
```

The series names shown in the encyclopedia and units such as `met`/`t` come from `SERIES` and `unit()` at the top of
`work/tools/src/dict_build.py`: translate them there if your language uses different titles.

### 10.3 Scenario titles

`traduccion/referencia/misiones.csv`, columns `en` (and `en_corto` if it doesn't fit). The titles are drawn as
graphics with Liberation Serif Bold 20 in up to 2 lines of 304 px, with a total budget of 144 pieces for all titles
(the `titles` stage warns if you exceed it); previews in `work/build/<N>/titles/preview/`. Fine adjustments per title
(forced line break with `|`): `work/gfx/render/titulos.csv`. The same titles also appear as menu text in the
intermission menu: translate them in `menus_map.txt` too. The `Stage N` header word is `STAGE_WORD` in
`work/tools/src/subtitle.py` (must fit in 48 px).

### 10.4 Terrain and place names (`work/dump/mdata.jsonl`)

1,426 rows but only 79 distinct names: give every duplicate the same `en` (a small script that maps `jp` → your
text is easiest). Maximum 15 bytes.

### 10.5 Protagonist default names (`work/translation/entry_en.csv`)

The 8 preset protagonists' first name, surname and nickname: ASCII, at most 8 letters each (the name editor can't
hold more). The name-editor button bar (`Enter Delete Space Back`) is `BUTTONS` in `work/tools/src/entry_patch.py`
(36 bytes).

### 10.6 Memory card save title

`EXE_STRINGS` in `work/tools/src/build_all.py`: the title shown by the console's memory card manager. It must be
written in **fullwidth** characters (`ＳＲＷ　Ａｌｐｈａ…`), at most 47 bytes (each fullwidth character is 2 bytes).

### 10.7 Other strings in code

`'Dummy'` for the dummy weapon slot (`robot_raf.py`), `STAGE_WORD` (`subtitle.py`), `BUTTONS` (`entry_patch.py`),
`SERIES`/`unit()` (`dict_build.py`). Everything else is in the files of §6.

---

## 11. Graphics with text

Some texts are pictures: menu labels (G19), effects (G22), barriers, the prologue (G14–G17), map place boxes
(G33–G36), map warnings (G37). They are re-drawn from CSV files in `work/gfx/render/` that copy the original style:

```bash
# 1. edit work/gfx/render/Gxx.csv (column en; "-" = leave empty)   2. draw   3. check
$PY work/tools/src/gfx_render.py render G19          # or no argument: all of them
$PY work/tools/src/gfx_entrega.py check work/gfx/render/out
```

Look at `work/gfx/render/out/G19_preview.png` (Japanese | yours) before building. Columns of `Gxx.csv`:
`caja` (box id), `x y w h` (box), `jp`, `en`, `align`, `font`, `size`, `style`.

- Boxes in the **`game8`** font use the game's own 8 px font: ASCII only (unknown characters become `?`).
- Boxes in **TrueType** fonts (DejaVu, Liberation) can show accented letters, but check the preview: capital
  accents can be cropped at the top.
- **Map place names** (「現在位置」 boxes): `work/gfx/render/lugares_mapa.csv`, one row per name, ≤ 231 px;
  `gfx_render.py render G33 G34 G35 G36`.
- **Prologue**: `work/gfx/render/prologo_en.txt`, free text; the tool lays it out and reports if it's too long.
- **Map warnings** (G37: BARRIER HIT!!, CRITICAL…): `work/gfx/render/G37.csv`, drawn (`gfx_render.py render G37`,
  which calls `kief_labels.py`) with a tiny 3×5 pixel font that only has **A–Z, `-`, `!` and space**. Some of these were already English in the Japanese
  game.
- **Copyright notice** (G20): legal text, leave it as it is.
- `work/gfx/MANUAL_render.md` (Spanish) documents every graphic and style.

Remember that `work/gfx/render/out/` is not in git: after cloning or switching branches, run `gfx_render.py render`
before building (the setup does it once), or the `graphics` stage only includes some pieces.

---

## 12. Validating

**`check_text.py` is the gatekeeper.** It encodes each line as the game would, measures every line in pixels with
the real font table, and checks byte limits, line counts, `$` variables and forbidden characters.

```bash
(cd work && ../work/.venv/bin/python tools/src/check_text.py)                 # everything
(cd work && ../work/.venv/bin/python tools/src/check_text.py --only snmsg,em) # some formats
```

- **Errors** are measured limits: the game cuts the text mid-word or breaks. You need **0 errors** to publish.
- **Warnings** are softer, and some are shaped around English: the speaker format expects `Name: text` with no space
  before the colon (French typography will warn; set `speaker=False` for that format in `FORMATS` at the top of
  `check_text.py` if it gets in the way), and `lote.py validar` looks for glossary terms in your text with an English
  plural rule (inflected languages get false warnings; the checked categories are `CHECK_TIPOS` at the top of
  `lote.py`).
- Results go to `work/build/check_text.csv`.

**`ci_check.sh`** runs the same checks as CI. In the kit, GitHub Actions runs the steps that work without the disc;
run the rest locally:

| Step | Where | What |
|---|---|---|
| `guard` | CI + local | no disc images, BIOS, game executable or save states committed |
| `syntax` | CI + local | all `.py` and `.sh` compile |
| `csv` | CI + local | `csv_lint.py`: shifted columns, duplicates, characters outside cp932 in the glossary |
| `nogamedata` | CI + local | no committed `.jsonl` contains Japanese (`kit.py check-stripped`) |
| `dedication` | CI + local | the dedication screen is unchanged (requirement 2) |
| `tests` | local | unit tests of the validator and the pipeline |
| `validate` | local | `build_all.py --dry-run`: all text + menus up to date |
| `lotes` | local | `lote.py validar` on your batches (if any) |
| `generated` | local | generated files up to date with their sources |

```bash
work/tools/ci_check.sh                       # everything (needs the setup done)
work/tools/ci_check.sh guard nogamedata      # some steps
```

---

## 13. Building and testing

### 13.1 Builds

```bash
work/tools/build.sh --selftest --name es_test     # → work/build/es_test_v01/es_test_v01.bin/.cue
```

The next build with the same `--name` becomes `_v02`, `_v03`… A build takes under a minute. If a stage fails, the
message says which one and where its log is (`work/build/<N>/logs/<stage>.log`).

| Option | What for |
|---|---|
| `--list` | list the 28 stages |
| `--dry-run` | validate everything without building |
| `--selftest` | also check that every tool rebuilds the original files exactly and that no row moved |
| `--only font,validate,script` / `--skip …` | run some stages (iterate on one format quickly) |
| `--allow-text-errors` | build even with lines that don't fit (testing only, never publish) |
| `--null` | rebuild with no changes: must be identical to the original disc |
| `--strict` | refuse to build with uncommitted changes (for releases) |
| `--release` | also make the xdelta patch and `SHA1SUMS` (§14) |
| `--no-version`, `--overwrite` | use `--name` as is / overwrite an existing build |

Stage order: `preflight → selftest → font → validate → exe → snmsg · script · bxclist · deadmess · em · pilot ·
mdata · mdata_test → robot → dc · dr → menus → exe_strings → entry → titles → layout → copyright → graphics →
dedicatoria → iso → verify → [smoke] → [release]`. Each build writes `manifest.json` (commit, inputs, what changed),
`check_text.csv`, `menus/report.csv` and `logs/` next to the image, and weighs ~0.65 GB: delete old ones from
`work/build/`.

### 13.2 Playing your build

- Load `work/build/<N>/<N>.cue` in DuckStation, PCSX-Redux or RetroArch. For RetroArch, **copy** the `.bin`/`.cue`
  to its folder (symlinks are rejected).
- Memory cards from the Japanese version or the English patch load fine, but the protagonist's and partner's names
  are stored on the card: start a new game to see the names of your translation.
- Your build shows English wherever you haven't translated yet (the pivot fallback), so you can test early.
- What to check on screen: lines cut mid-word, text overflowing boxes, names, menus that fell back to their short
  form, and anything still in Japanese.

### 13.3 Automated emulator routes (optional)

The kit includes the project's headless test harness, built on PCSX-Redux: `drive.sh` (inputs, screenshots, RAM
dumps, memory cards), `regresion.sh` (recorded routes: `boot`, `cp04`, `cp12`), `smoke_boot.sh`, `run_redux.sh`,
`run_duckstation.sh` and the `*_test.sh` scripts. They need local setup that the kit can't ship:

- **your own BIOS** at `Bios/scph100.bin` (SCPH-100 v4.3 NTSC-J) and the PCSX-Redux AppImage at
  `work/tools/bin/PCSX-Redux-HEAD-x86_64.AppImage` (DuckStation: `work/emu/duckstation/DuckStation-x64.AppImage`);
- a PCSX-Redux **portable profile** in `work/emu/pcsx-redux/`: open the emulator once with `work/tools/run_redux.sh`
  (needs a display), select your BIOS in its settings and close it, which writes `pcsx.json` there; machines without a
  display use `xvfb-run` or the container in `work/tools/docker/`;
- a blank memory card at `work/emu/states/blank.mcd` for `FRESH_CARD=1`; the upstream checkpoint cards and input
  recordings are not part of the kit.

The header of each script explains its variables. This is optional: playing your build is enough.

---

## 14. Publishing a release

1. Commit everything, then build with the release options:
   ```bash
   work/tools/build.sh --strict --selftest --release --name mylang_v1
   ```
   `--release` creates `work/build/mylang_v1_v01/mylang_v1_v01.xdelta`, **applies it to your original disc and checks
   the result**, and writes `SHA1SUMS`. It needs `xdelta3` and the original `.bin`.
2. Prepare the files players download, with friendly names:
   - `SRWAlpha_<LANG>_v1.xdelta` (the patch);
   - `Super Robot Taisen Alpha (<Language> v1).cue`, a copy of the build's `.cue` whose `FILE` line points to
     `"Super Robot Taisen Alpha (<Language> v1).bin"`;
   - `SHA1SUMS` with those names (the hashes don't change).
3. Write release notes that include, at least:
   - which disc the patch needs (name, size and SHA-1 from §3) and how to apply it (below);
   - credit to your team and **"Based on the English translation by Nrlemo:
     <https://github.com/Nrlemo/Super-Robot-Wars-Alpha-PSX-English-Ver>"**;
   - **the Buy Me a Coffee link, <https://buymeacoffee.com/srwa_en> (requirement 3)**, for example:
     ```html
     <a href="https://www.buymeacoffee.com/Srwa_en"><img src="https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png" alt="Buy Me A Coffee" height="60"></a>
     ```
4. Publish on your fork's **Releases** page (or with `gh release create v1 --notes-file notes.md SRWAlpha_*.xdelta
   *.cue SHA1SUMS`). Patches go only as release assets: the `guard` step refuses `.xdelta`, `.bin` and `.cue` files in
   the repository.

**How players apply it** (put this in your notes): with [Delta Patcher](https://github.com/marco-calautti/DeltaPatcher),
[Rom Patcher JS](https://www.marcrobledo.com/RomPatcher.js/), or

```bash
xdelta3 -d -s "Super Robot Taisen Alpha (Japan) (v1.0).bin" SRWAlpha_<LANG>_v1.xdelta "Super Robot Taisen Alpha (<Language> v1).bin"
```

then keep the `.bin` and the `.cue` together and load the `.cue`.

---

## 15. Staying in sync with upstream

The English project keeps fixing things (tools, English lines, graphics). To bring those fixes into your fork:

```bash
git fetch upstream
git merge upstream/main
$PY work/tools/src/kit.py restore              # if upstream changed tools or dumps: re-extract and regenerate
$PY work/tools/src/kit.py refresh-ref upstream/main
```

- **Conflicts in `work/dump/*.jsonl`** happen when upstream corrected an English line that you have in `en_ref`
  (after the pivot, every row of yours differs from upstream). Keep **your** version of those files, then let
  `refresh-ref` bring the English corrections in:
  ```bash
  git checkout --ours work/dump/script.jsonl      # for each conflicting dump
  git add work/dump/script.jsonl
  ```
- **`kit.py refresh-ref upstream/main`** copies upstream's current English into your `en_ref` fields and writes, for
  every format, `work/logs/kit/refresh_ref_<format>.tsv` with the rows **you had already translated** whose English
  changed (`key`, old English, new English, your translation): review those lines.
- Conflicts in tools are rare (you shouldn't need to change them); when in doubt, take upstream's version.

---

## 16. What never to touch

| Don't touch | Why |
|---|---|
| **The dedication screen**: `work/tools/src/dedicatoria.py`, `work/patches/dedicatoria.asm`, the `dedicatoria` stage | requirement 2; CI checks it |
| `.github/FUNDING.yml` | requirement 3 |
| `jp`, `en_ref` and the key fields of `work/dump/*.jsonl` | they are the address of each text; `--selftest` stops if a row moved |
| `work/iso_jp/` and your original disc | everything is rebuilt from them |
| Generated files (§6) | they are overwritten when regenerated |
| `work/patches/*.asm`, `0x80…` addresses and format constants in the tools (`FULL_MAX`, `MAX_PIECES`, `RSIZE`…) | they are measurements of the game's code and memory; one wrong byte freezes the game |
| `work/font/en_8px.txt` (unless you add glyphs, §2.1) | changing a letter changes the width of every line in the game; check with `font_margen.py` first |
| `.gitattributes` and the `srwjp` filter | they keep game data out of your repository |

The tools that patch code (`ovl_patch.py`, `layout_patch.py`, `entry_patch.py`, `subtitle.py`, `kief_labels.py`,
the VWF in `vwf.asm`) work because every change was placed in verified free memory. If you need something beyond
text (new screens, longer animations, a different layout), open an issue upstream first.

---

## 17. Troubleshooting

| Symptom | Cause and fix |
|---|---|
| `kit_setup.sh`: SHA-1 mismatch | not the Redump v1.0 single-track image; re-dump or find the right image (§3) |
| `kit_setup.sh`: missing armips/mkpsxiso | run with `--tools` (needs cmake and g++) |
| `build.sh --null` not identical | wrong disc, or `work/iso_jp/` is incomplete: delete it and run the setup again |
| A build stage fails | read `work/build/<N>/logs/<stage>.log`; the summary line names the row or file |
| `encoding` error | a character outside ASCII (§2.1); look for accents, curly quotes, `…`, dashes |
| `px` / lines error | the line doesn't fit: re-break it (`--wrap-text`) or shorten it |
| `robot` stage: name doesn't fit | add `en_short` in `glossary.csv` (§9) |
| `menus`: "sin solución" (no solution) | the string can't move and doesn't fit: give it a shorter `en_short` |
| `titles`: more than 144 pieces | shorten titles or use `en_corto` |
| Graphics missing in the build (the `graphics` line of `--dry-run` doesn't list 23 pieces, G14–G37) | run `gfx_render.py render` (§11) |
| `kit.py clean … run kit.py restore` | the git filter has no cached dump yet: run `kit.py restore` |
| `nogamedata` fails in CI | a `.jsonl` with Japanese was committed (e.g. a batch): remove it from git, check `.gitignore` |
| `dedication` fails in CI | the dedication files changed: `git checkout upstream/main -- work/tools/src/dedicatoria.py work/patches/dedicatoria.asm` |
| Japanese text in game | that row has neither `en` nor `en_ref`, or it is one of the parts that stay Japanese (§1) |
| Missing font (DejaVu/Liberation) | install `fonts-dejavu-extra fonts-liberation`, or copy the `.ttf` files to `work/gfx/fonts/` |
| Protagonist names in kana | names are stored on the memory card: start a new game |

Questions about the tools: open an issue on the upstream repository.

---

## 18. Tool reference

All in `work/tools/src/` unless noted; run with `$PY`. Each tool documents its usage at the top of the file.

**Kit and pipeline**

| Tool | What it does |
|---|---|
| `work/tools/kit_setup.sh` | one-time setup of a fork (§4) |
| `kit.py` | `restore` (Japanese from your disc), `pivot`, `refresh-ref`, `clean`/`smudge` (git filter), `check-stripped`, `dedication` |
| `work/tools/build.sh` → `build_all.py` | the build pipeline: all stages, manifest, verification, release patch |
| `build_iso.py` | rebuilds the `.bin/.cue` with mkpsxiso from `work/iso_jp` + replacements |
| `isofs.py` | reads ISO9660 from a MODE2/2352 image |
| `work/tools/ci_check.sh` | the CI checks, locally (§12) |
| `work/tools/env.sh` | environment paths (`source work/tools/env.sh`) |

**Text formats** (each: `dump` from the disc, `build` with your text, a self-test that rebuilds the original exactly)

| Tool | Game file |
|---|---|
| `script_bin.py` | `BUSTUP/SCRIPT.BIN`: intermission scenes |
| `snmsg.py` | `SNMAP/SNMSG.BIN`: map dialogue (32,544 slots of 256 bytes) |
| `sndata.py` | `SNMAP/SNDATA.BIN`: read-only, which map message appears in which scenario (`map`, `disasm N`) |
| `bxclist.py` | `BATTLE/BXCLIST.BIN`: battle quotes per pilot |
| `deadmess_em.py` | `SNMAP/DEADMESS.BIN`, `SNMAP/EM.BIN` |
| `pilot_bin.py` | `UNITPRAM/PILOT.BIN`: names (`fill` from the name files), stats |
| `robot_raf.py` | `UNITPRAM/ROBOT.RAF`: units and weapons (LZSS) |
| `option_dict.py` | `OPTION/DC.BIN`, `DR.BIN`: encyclopedia (LZSS) |
| `mdata_bin.py` | `SNMAP/MDATA.BIN`, `TEST/MDATA.BIN`: terrain and places |
| `lzpack.py` | LZSS containers (`COMMON.BIN`, `MAP.BIN`…) |
| `sjis_text.py` | codec between game bytes and editable text |

**Translation and validation**

| Tool | What it does |
|---|---|
| `check_text.py` | the validator (§12); `--wrap-text` proposes line breaks |
| `lote.py` | batches: `sacar`, `terminos`, `validar`, `integrar`, `estado` (§8) |
| `reflow_candidates.py` | re-breaks lines cut mid-sentence |
| `gemini_translate.py`, `gemini_queue.py`, `work/tools/gemini_job.sh` | AI translation of batches; `gemini_queue.py --resumen` = progress table |
| `paquete_traduccion.py` | packs batches into `traduccion/paquetes/` for translating with an external assistant (contains Japanese: not committed) |
| `font_margen.py` | how many lines would stop fitting if a letter of the font changed width |
| `csv_lint.py` | CSV sanity (columns, duplicates, cp932) |

**Names and references**

| Tool | What it does |
|---|---|
| `traduccion_ref.py` | reference tables in `traduccion/referencia/generado/` (used by `lote.py`) |
| `dict_build.py` | `dict_src/*.txt` → `dc_en.jsonl`, `dr_en.jsonl` (re-flow to 46 bytes) |
| `glossary_build.py`, `weapons_review_build.py` | upstream only: rebuild the glossary from reference pages not included in the kit |
| `end_credits.py` | inventory of the end credits (they stay Japanese) |

**Menus and code patches**

| Tool | What it does |
|---|---|
| `ovl_strings.py` | inventory of strings in the executable and overlays, with their pointers |
| `menus_draft.py` | `menus_map.txt` → `menus_en.jsonl` and whether each string fits |
| `ovl_patch.py` | replaces menu strings in the overlays, relocating and fixing pointers |
| `menus_short_list.py` | lists menu strings that used their short form |
| `layout_patch.py` | x positions of centred menus and titles from the real text width |
| `entry_patch.py` | protagonist name-entry screen (limits, default names) |
| `copyright_patch.py` | width of each copyright line |
| `dedicatoria.py` + `work/patches/dedicatoria.asm` | the dedication screen (**don't modify**) |
| `ovl_base.py`, `find_addr_refs.py` | research: load address of an overlay; who points to a range |

**Font and graphics**

| Tool | What it does |
|---|---|
| `font_build.py` + `work/patches/vwf.asm` | the font (`8FONT_R.TIM`, `WINTEX.BIN`) and its width table |
| `vwf_table.py` | old width-table tool (replaced by `font_build.py`) |
| `tim.py` | TIM ↔ indexed PNG |
| `gfx_render.py` | re-draws the text graphics from `work/gfx/render/*.csv` |
| `gfx_entrega.py` | checks the PNGs and imports them into the game files |
| `subtitle.py` | scenario titles |
| `mapa_lugares.py` | map place-name boxes |
| `kief_labels.py` | map warnings (G37) |
| `gfx_variantes_mapa.py` | compares fonts for the place-name boxes (exploration) |

**Emulator and tests** (optional, §13.3)

| Tool | What it does |
|---|---|
| `work/tools/drive.sh`, `redux_drive.lua` | headless PCSX-Redux with inputs, screenshots, RAM dumps, breakpoints |
| `work/tools/regresion.sh`, `smoke_boot.sh`, `*_test.sh`, `battle_prologue.sh`, `crit_skip.sh` | recorded routes and screen tests |
| `redux_record.lua`, `redux_shots.lua`, `redux_cover.lua`, `raw2png.py`, `sheet.py`, `shots_check.py` | recording, screenshots, contact sheets, automatic screenshot checks |
| `work/tools/run_redux.sh`, `run_duckstation.sh` | open the emulators with a window |
| `test_*.py`, `mk_*_test.py`, `mk_deadem_real.py`, `mk_ancho_bxclist.py` | unit tests and test discs used to measure windows |
| `auditoria_comprimidos.py`, `cobertura_barrido.py`, `diff_files.py`, `ppf_apply.py` | research tools used during the English project |

---

## 19. Vocabulary and technical notes

| Term | Meaning |
|---|---|
| **Dump** (`work/dump/*.jsonl`) | the extracted text of a game file, one row per text |
| **Pivot** | moving the English to `en_ref` so `en` becomes your language (§5) |
| **Overlay** (`OVL/*_GRP.BIN`) | a block of code and strings the game loads at a fixed address for each screen |
| **VWF** | variable-width font: each letter takes its own width, so limits are in pixels |
| **Slot** | a fixed-size record (map dialogue and defeat lines: 256 bytes) |
| **LZSS** | the compression of `ROBOT.RAF` and the encyclopedia; the tools redo it |
| **TIM / CLUT** | PlayStation image format / its colour palette |
| **Batch** (*lote*) | a slice of a dump extracted for translation (§8) |
| **Variant 1–8** | the 8 versions of protagonist lines (gender × personality) |
| **Short form** (`en_short`, `en_corto`) | the fallback text for fields where the full form doesn't fit |
| **`_vNN`** | the version suffix of a build name |

**Technical notes** (`work/notes/`, in Spanish) document every format and decision in depth:

| Topic | Note |
|---|---|
| Environment and emulators | `ENTORNO.md` |
| Build pipeline | `pipeline_build.md` |
| Validator and measured limits | `check_text.md` |
| Font and VWF | `fuente_en.md`, `vwf_investigacion.md` |
| Formats | `script_bin.md`, `poc_snmsg.md`, `sndata.md`, `bxclist.md`, `deadmess_em.md`, `pilot_bin.md`, `mdata.md`, `compresion.md`, `exe_strings.md` |
| Menus and overlays | `menus.md`, `menus_borrador.md` |
| Graphics, titles, copyright, dedication | `graficos.md`, `work/gfx/MANUAL_render.md` |
| Protagonist | `nombres_protagonistas.md`, `prueba_variantes_34.md`, `escenas_nombre_ancho.md` |
| Glossary and style | `glosario.md`, `guia_estilo_personajes.md`, `units_en.md`, `weapons_review.md`, `diccionarios_traduccion.md` |
| End credits, sound test | `creditos_end.md`, `option_s.md` |
| Regression checklist | `checklist_regresion.md` |

---

*Super Robot Taisen Alpha* © Banpresto / Bandai Namco. This is a fan project, not affiliated with them; please
support the official releases.

<a href="https://www.buymeacoffee.com/Srwa_en" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png" alt="Buy Me A Coffee" style="height: 60px !important;width: 217px !important;" ></a>
