<p align="center">
  <img src="logo.png" alt="Bottled Kraken" width="300">
</p>

<h1 align="center">Bottled Kraken</h1>

<p align="center">
  A desktop OCR workbench for Windows 10/11 that treats recognition as an
  <strong>editable workflow</strong> — not a one-click black box.
</p>

<p align="center">
  <img src="https://img.shields.io/badge/license-MIT-2D6A9F" alt="MIT License">
  <img src="https://img.shields.io/badge/Python-3.13%20x64-2D6A9F" alt="Python 3.13">
  <img src="https://img.shields.io/badge/Kraken-7.0.3-2D6A9F" alt="Kraken 7.0.3">
  <img src="https://img.shields.io/badge/platform-Windows%2010%20%7C%2011-2D6A9F" alt="Windows 10/11">
  <img src="https://img.shields.io/badge/UI-16%20languages-2D6A9F" alt="16 languages">
</p>

---

## Built on Kraken

Bottled Kraken is a graphical front end. The actual OCR is done by
**[Kraken](https://github.com/mittagessen/kraken)**, the OCR engine developed by
**Benjamin Kiessling ([@mittagessen](https://github.com/mittagessen))**. All
credit for the recognition and segmentation quality belongs to that project and
its contributors.

This repository adds an interface around it: image preparation, line and box
editing, correction tools, and export formats. Without Kraken there would be
nothing to wrap.

> Kraken is available at **<https://github.com/mittagessen/kraken>** and is
> worth using directly if you are comfortable on the command line.

Also used: **[faster-whisper](https://github.com/SYSTRAN/faster-whisper)** for
line-level dictation, and OCR models from the
**[Zenodo OCR model community](https://zenodo.org/communities/ocr_models/)**.

---

## What it is for

Most OCR tools stop the moment recognition finishes. Bottled Kraken is built for
what happens **between raw OCR output and a usable text**:

- when segmentation still needs correcting
- when line structure carries meaning
- when forms or archival pages need manual work
- when everything should stay local and transparent

That makes it particularly suited to **historical prints, manuscripts, forms**
and other layouts where a purely automatic pass is rarely enough.

<p align="center">
  <img src="Bottled%20Kraken%20Screenshot%20v3.4.png" alt="Bottled Kraken interface" width="900">
</p>

---

## Features

**Recognition**

- OCR through Kraken with separate recognition and segmentation models
- `blla` segmentation as the preferred path when a segmentation model is present
- Images and PDFs as input
- Queue-based batch workflow across multiple files
- Hardware selection for CPU, CUDA, ROCm and MPS

**Editing**

- Interactive display of detected lines
- Editable overlay boxes and line structure
- Move, swap, insert, delete, split and reorder lines
- Configurable reading order
- Import lines from TXT or JSON
- Save and load projects as JSON

**Correction**

- Optional revision through a local language model (OpenAI-compatible endpoint)
- Optional per-line dictation through faster-whisper

**Interface**

- 16 interface languages
- Light and dark mode and custom UI templates

---

## Image preparation

A preprocessing layer sits in front of recognition, because scan quality decides
more about the result than any model choice:

| Tool | Typical use |
| --- | --- |
| Rotation | skewed scans |
| Crop region | oversized or badly trimmed pages |
| Split bar | double pages and divided layouts |
| Grayscale | colour noise on old paper |
| Contrast | faded or low-contrast originals |
| White margin | pages cut too close to the text block |
| Smart splitting | automatic separation of page halves |

---

## Workflow

1. Load an image or PDF
2. Prepare the page with the editing tools if needed
3. Load a **recognition model**
4. Load a **segmentation model**
5. Run Kraken OCR
6. Review the detected lines and boxes
7. Correct manually, through a local LM, or by voice
8. Export

---

## Local language model revision

OCR lines can be smoothed or normalised through a **local LM server**, as long as
it exposes an **OpenAI-compatible base URL**. Nothing leaves the machine.

| Server | Typical base URL |
| --- | --- |
| LM Studio | `http://localhost:1234/v1` |
| Ollama | `http://localhost:11434/v1` |
| Jan | `http://127.0.0.1:1337/v1` |
| GPT4All | `http://localhost:4891/v1` |
| text-generation-webui | `http://127.0.0.1:5000/v1` |
| LocalAI | `http://localhost:8080/v1` |
| vLLM | `http://HOST:8000/v1` |

If the server runs on another machine and is bound to `127.0.0.1` there, reach it
through an SSH tunnel:

```bash
ssh -L 1234:127.0.0.1:1234 user@192.168.1.50
```

Then point Bottled Kraken at `http://127.0.0.1:1234/v1`.

---

## Voice correction

faster-whisper is used for **line-scoped** microphone correction — useful when a
line is badly damaged, or when a name is faster spoken than typed. It is not
meant for transcribing long recordings.

Dictation runs in a separate process that starts in UTF-8 mode and returns
ASCII-safe JSON, so umlauts, non-ASCII device names and model paths do not depend
on the terminal or system locale. Temporary WAV and log files live in a private
short-lived runtime folder and are removed afterwards.

---

## Local eScriptorium

Under the **eScriptorium** menu entry, Bottled Kraken can install and run a local
eScriptorium server. Installation and startup are deliberately separate steps.
Docker is not used.

Supported targets:

- Fedora Linux
- Linux Mint
- Windows 10/11 with WSL2

On Windows a dedicated Ubuntu 24.04 distribution is imported into WSL2; the
services are controlled through `wsl.exe` and systemd, while the browser stays
native and reaches the server over localhost. PostgreSQL, Redis, Python, Kraken,
Celery, Django and the web front end are configured in the background, with live
output instead of a silent buffer. A cancelled or failed first run leaves no
completion marker — running the installer again repairs the setup.

Default locations:

```
Windows: %LOCALAPPDATA%\BottledKraken\escriptorium\platforms\windows_wsl\
WSL:     \\wsl.localhost\BottledKraken-eScriptorium\opt\bottled-kraken-escriptorium
```

`BOTTLED_KRAKEN_USER_DIR` overrides the base folder, `BOTTLED_KRAKEN_ESCRIPTORIUM_REF`
pins the source revision (default `26.04.1`). Stopping the server shuts down
services only — projects, databases, models and media are left untouched.

**If WSL2 is missing:** run `wsl --install` in an administrative PowerShell,
restart Windows, and make sure virtualisation is enabled in BIOS/UEFI.

---

## Export formats

| Category | Formats |
| --- | --- |
| Plain text | `txt` |
| Structured data | `csv`, `json` |
| OCR formats | `ALTO XML`, `hOCR` |
| Images | `png`, `jpg`, `bmp` |
| PDF | searchable PDF with image plus invisible text layer |

The same run can therefore serve both a readable result and structured
downstream processing.

---

## Models

Bottled Kraken ships **no OCR models**. You load the ones that match your
material — usually a **recognition model**, and optionally a **segmentation
model** for `blla`.

A good public source is the Zenodo OCR model community:
<https://zenodo.org/communities/ocr_models/>

As a rule of thumb: a model trained on historical prints will beat a general
model on historical prints by a wide margin. The same holds for handwriting and
form-heavy material.

---

## Running from source

### Requirements

- Windows 10 or 11, 64-bit
- Python 3.13 x64 recommended (3.12 x64 also accepted by the build script)
- PowerShell 5.1 or PowerShell 7
- A working Kraken / PyTorch CPU environment

### Setup

```powershell
git clone https://github.com/Testatost/Bottled-Kraken.git
cd Bottled-Kraken

Set-ExecutionPolicy -Scope Process Bypass
.\check_windows_10_11_build_environment.ps1

py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1

python -m pip install --upgrade pip setuptools wheel
python -m pip install -r requirements-lock-windows.txt
python -m pip install --no-deps kraken==7.0.3

python main.py
```

`requirements.txt` describes the Windows dependencies in readable form;
`requirements-lock-windows.txt` is what reproducible release builds use. Kraken
is installed with `--no-deps` because its CoreML dependency is not part of the
Windows target.

### Building a binary

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\build_windows_10_11.ps1
```

The onefile build lands in `dist\Bottled Kraken.exe`.

---

## Updating Kraken

**Hints → Kraken → Update Kraken** pulls the latest stable release from the
official `mittagessen/kraken` repository. The updater resolves the release tag to
a concrete commit, downloads that exact source archive into a private user
folder, and verifies the modules Bottled Kraken depends on. Only after a
successful check is the new state activated atomically; it takes effect on the
next application start.

The bundled Kraken version is kept as a fallback. The updated version is loaded
ahead of it at runtime, including inside a PyInstaller build. Set
`BOTTLED_KRAKEN_DISABLE_KRAKEN_OVERLAY=1` to skip the external version for one
run. No separate Git, Python or `pip` installation is required.

---

## License

Original Bottled Kraken code is **MIT** licensed. Dependencies and optional
downloads keep their own licenses.

---

## Acknowledgements

- **[Kraken](https://github.com/mittagessen/kraken)** by Benjamin Kiessling
  ([@mittagessen](https://github.com/mittagessen)) — the OCR engine this project
  is built around
- **[faster-whisper](https://github.com/SYSTRAN/faster-whisper)** by SYSTRAN
- **[eScriptorium](https://gitlab.com/scripta/escriptorium)** — the annotation
  platform integrated for local use
- The **[Zenodo OCR model community](https://zenodo.org/communities/ocr_models/)**
  for publicly available models
