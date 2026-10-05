# Super Robot Wars Alpha (PSX) English Ver.

**Latest release: [Release Candidate 2 (RC02)](https://github.com/Nrlemo/Super-Robot-Wars-Alpha-PSX-English-Ver/releases/tag/RC02)** — fan translation of *Super Robot Taisen Alpha* (PlayStation, 2000) into English.

The first complete, playable English build of **Super Robot Taisen Alpha** (PlayStation, 2000) — the crossover that brought Mazinger, Getter Robo, Gundam (UC and AU), Evangelion, Macross, Dancougar, Dunbine, L-Gaim, Gunbuster, Brain Powerd, the Masou Kishin and the Banpresto originals together for the first time on PSX.

**This is a release candidate**: every line of dialogue is translated and inserted, the game boots and plays in English from the title screen to the battle animations and so forth. Please report anything that looks wrong (see *Reporting problems* below).

### We need your support! 💫

While every line is translated and the game is fully playable from the title screen to the battle animations, we are looking for players to test this build on emulators and physical consoles. 💥

Grab your original Japanese ISO, check the README.md for the quick xdelta patching instructions, and help us polish this masterpiece! Please report any visual bugs🐛, or text issues on our GitHub.

**AND CONSIDER SUPPORTING FURTHER DEVELOPMENT!** 

<a href="https://www.buymeacoffee.com/Srwa_en" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/v2/default-blue.png" alt="Buy Me A Coffee" style="height: 60px !important;width: 217px !important;" ></a>

## What's new in RC02

- **New dedication and support screen** after the copyright screen (about 6 seconds; press Start to skip it). It has two QR codes: **GitHub** (updates and bug reports) and **Buy Me a Coffee** (support development).
- Everything else is the same as RC01.

## What is translated

| Content | Status |
|---|---|
| Intermission scenes (`SCRIPT.BIN`, 45,712 lines) | ✅ 100 % |
| Map dialogue (`SNMSG.BIN`, 32,288 messages) | ✅ 100 % |
| Battle quotes (`BXCLIST.BIN`, 18,128 lines) | ✅ 100 %, three style passes |
| Defeat and suspend quotes | ✅ 100 % |
| Pilot names (469), units (486) and weapons (692 names) | ✅ |
| Character and robot dictionaries (350 + 449 entries) | ✅ |
| Menus: title, intermission, status, map, battle, save/load, options, name entry | ✅ |
| Stage titles (128), prologue, terrain and place names, map labels | ✅ |
| Graphics: battle effects, barriers, copyright screen, map location boxes, UI labels | ✅ (most; see known issues) |

**~96,700 lines of dialogue** in total, plus menus and graphics.

**Technical work behind it:** a new English font with a **variable-width font (VWF)** routine patched into the executable (~55 characters per line instead of 20 full-width kana), a raised on-screen text-object limit, re-implemented LZSS compression for the unit/dictionary archives, and a rebuild of the disc image with files allowed to grow.

**Style:** names and attack calls follow the official Western localizations of each series where they exist (Gundam, Evangelion, Macross…), otherwise standard Hepburn. Menu and system terms follow the English *Super Robot Wars OG* releases (*Will*, *Accel*, *Luck*, *Fury*…). A canonical glossary of 1,739 terms keeps names consistent across all files. Each character keeps their voice and verbal tics (Shinobu's *Let's do this!*, Asuka's *You idiot!?*, Masaki's cats' *~nya*…).

## Not translated (by design)

- FMV videos, sound test track names and song lyrics.
- The ending credits (staff names stay as in the original).

## How to apply

You need your own dump of the original Japanese disc. **The patch only works on this exact image:**

| | |
|---|---|
| Game | Super Robot Taisen Alpha (Japan) (v1.0) — SLPS-02636 |
| File | `Super Robot Taisen Alpha (Japan) (v1.0).bin` (single track, 646,374,288 bytes) |
| MD5 | `8cc4b3af159d26d11cad46b136a5c833` |
| SHA-1 | `cfce3c7a76f64269387fbb7b77e3bcfe41b723c6` |

1. Download `SRWAlpha_EN_RC02.xdelta` and `Super.Robot.Taisen.Alpha.English.RC02.cue` from the [Releases page](https://github.com/Nrlemo/Super-Robot-Wars-Alpha-PSX-English-Ver/releases/tag/RC02).
2. Apply the patch to the Japanese `.bin`:
   - **Windows / macOS / Linux (GUI):** [Delta Patcher](https://github.com/marco-calautti/DeltaPatcher) or the [Rom Patcher JS](https://www.marcrobledo.com/RomPatcher.js/) web page.
   - **Command line:**
     ```
     xdelta3 -d -s "Super Robot Taisen Alpha (Japan) (v1.0).bin" SRWAlpha_EN_RC02.xdelta "Super Robot Taisen Alpha (English RC02).bin"
     ```
3. Name the patched file `Super Robot Taisen Alpha (English RC02).bin` (that is the name the `.cue` points to) and keep both in the same folder. You can rename the `.cue` freely; if you rename the `.bin`, edit the `FILE` line of the `.cue` to match.
4. Load the `.cue` in your emulator. Tested with **PCSX-Redux**, **DuckStation** and **RetroArch**. Real hardware / ODE has not been tested yet.

`SHA1SUMS` lists the expected hashes. Patched image: SHA-1 `38e852eb52526c3d48ef3ffb269b2bbbccd609cb`, MD5 `bb79678772db5cf74fe5ed965b656843` (646,442,496 bytes).

> **Memory cards:** saves from the Japanese version load fine, but the protagonist's and partner's names are stored on the card, so they will appear in kana. Start a new game for the English names.

## Known issues

- A few small graphical labels and button icons inside menu strings may sit slightly off (e.g. the triangle icon in the *Counter* menu).
- Digits in dialogue use the fixed 8 px width, so numbers look a bit spaced out.
- A final style read-through (battle quotes per pilot, scenes against the running game) is still to come.

## Reporting problems

Please open an issue with: the scenario number (or the scene), a screenshot, and what you expected. Text cut mid-word, Japanese text left on screen, freezes and wrong names are the most useful reports at this stage.

---

Fan translation, not affiliated with Bandai Namco / Banpresto. No game data is distributed here — only a patch. Please support the official releases.

<a href="https://www.buymeacoffee.com/Srwa_en" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png" alt="Buy Me a Coffee" style="height: 60px !important;width: 217px !important;" ></a>
