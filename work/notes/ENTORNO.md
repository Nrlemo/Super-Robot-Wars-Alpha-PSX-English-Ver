# Entorno de trabajo (Paso 0) — 2026-09-27

Todo vive en `work/`. La ISO original **no se toca**: se lee desde la raíz del proyecto.

```
work/
├── .venv/            Python 3.14 + pycdlib, pillow, numpy, beautifulsoup4, lxml
├── iso_jp/           FS extraído de la ISO JP (dumpsxiso) + layout.xml + license_data.dat
├── iso_chs/          (Paso 1) FS de la copia con parche chino
├── dump/             (Paso 3) texto extraído JSON/CSV
├── glossary/         (Paso 2) glosario canónico
├── build/            builds reconstruidas
├── ghidra_proj/      proyecto Ghidra "SRWAlpha" (SLPS_026.36 importado y analizado)
├── emu/
│   ├── duckstation/  DuckStation x64 portable (settings.ini, memcards, savestates, duckstation.log)
│   ├── pcsx-redux/   config portable de PCSX-Redux (pcsx.json)
│   └── shots/        capturas de smoke tests
├── tools/
│   ├── env.sh               rutas + función armips (source)
│   ├── run_duckstation.sh   [cue]  → jugar/testear
│   ├── run_redux.sh         [cue]  → debugger, VRAM, breakpoints
│   ├── smoke_boot.sh        <cue> <dir> [frames] → boot sin intervención + PNG
│   ├── ghidra.sh            → GUI de Ghidra
│   ├── src/redux_shots.lua  captura frames vía Lua en PCSX-Redux
│   ├── src/raw2png.py       convierte capturas (BGR555/RGB24) a PNG + contact sheet
│   ├── bin/                 mkpsxiso, dumpsxiso 2.30 · PCSX-Redux AppImage · armips 0.11 (wine)
│   ├── ghidra_12.1.3_PUBLIC/ (+ extensión ghidra_psx_ldr 2026.09.03)
│   └── jdk-21.0.12.1+1/     JDK Temurin portable (Ghidra no corre con el JRE del sistema)
└── downloads/        zips originales (839 MB, se pueden borrar)
```

## Verificaciones hechas
| Prueba | Resultado |
|---|---|
| dumpsxiso → mkpsxiso sin cambios | **Byte-idéntico** a la ISO original (0 diferencias en 646.374.288 bytes) |
| PCSX-Redux + SCPH-100 | Boot hasta FMV de intro; Lua + capturas automáticas OK |
| DuckStation | Detecta SLPS-02636, BIOS SCPH-100 (v4.3 J), bootea |
| Ghidra headless + PsxLoader | Import + auto-análisis de SLPS_026.36 OK |
| armips vía wine | Ensambla MIPS (`li v0,0x1234` → `34 12 02 34`) |

## Configuración
- **Audio en 0 / muteado** en ambos emuladores (DuckStation: `OutputMuted=true`, `OutputVolume=0`, `FastForwardVolume=0`; PCSX-Redux: `SPU.Mute=true`, `SPU.Volume=0`).
- DuckStation: modo portable (`portable.txt`), BIOS desde `../Bios` (`PathNTSCJ = scph100.bin`), log a archivo en nivel Info, asistente inicial y confirmación de apagado desactivados.
- BIOS japonesas disponibles: **scph100 (v4.3 J, en uso)**, scph5000 (v2.2 J), scph3500 (v2.1 J).

## Notas / pendientes
- `Emulator/DuckStation-arm64.AppImage` es ARM y no corre en esta máquina (x86_64); se usa la x64 de `work/emu/duckstation/`.
- armips 0.11 es la última release binaria (Windows, vía wine). Si hace falta una versión más nueva: compilar desde fuente (requiere `g++` + `cmake`).
- `info/…Unit Database…` re-guardada: tiene la **lista de unidades por serie** (con modelo, ej. "RX-78GP01 Gundam 'Zephyranthes'"), pero **no armas ni ataques**. Los nombres de ataques van a salir de `ROBOT.RAF` (JP) + nomenclatura oficial de cada franquicia.
- `info/…Story…` re-guardada: prólogo y sinopsis en inglés, útil como contexto de traducción.
- No es un repo git todavía.
