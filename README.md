<p align="center">
  <img src="logo.png" alt="Bottled Kraken Logo" width="260"> <br>
  <img src="splash.png" alt="Splash" width="260">
</p>

# Bottled Kraken

[Kraken](https://github.com/mittagessen/kraken) · [faster-whisper](https://github.com/SYSTRAN/faster-whisper) · [Zenodo OCR-Modelle](https://zenodo.org/communities/ocr_models/)

Bottled Kraken is a desktop OCR workbench based on **Kraken**.  
The project is aimed at anyone who does not just need some quick OCR text, but a **traceable and editable workflow** instead:

- prepare difficult scans
- run OCR
- review lines
- correct segmentation
- post-edit text
- and export results in useful formats

Bottled Kraken is especially useful for **historical prints, manuscripts, forms**, and other page layouts where a purely automatic OCR pass is often not enough.

<p align="center">
  <img src="Bottled Kraken Screenshot v3.1.png" alt="Bottled Kraken Screenshot" width="1000">
</p>

---

## Current Release Model

Bottled Kraken v3.1 is designed as a **CPU-first desktop application**.

The standard release already includes the core Kraken OCR workflow. Optional GPU support can be installed later from inside the application. This keeps the main executable smaller and avoids bundling very large CUDA or ROCm packages into the default release.

The intended release structure is:

- **Bottled Kraken CPU**  
  Standard version with Kraken OCR and all core features.

- **Optional NVIDIA CUDA Backend**  
  Installed separately when NVIDIA GPU acceleration is needed.

- **Optional AMD ROCm Backend**  
  Installed separately when ROCm acceleration is needed.

The optional GPU backends are installed into a separate user directory and do **not** modify the Bottled Kraken executable.

Typical backend locations are:

```text
Windows:
%LOCALAPPDATA%\BottledKraken\backends\

Linux:
~/.local/share/BottledKraken/backends/
```

The backend installation does not remove or modify system-wide NVIDIA, CUDA, ROCm, or driver installations.

---

## Approach

Bottled Kraken combines several processing steps that would otherwise often be spread across different tools:

- **preprocessing for difficult source images**
- **layout-aware OCR with Kraken**
- **interactive editing of lines and overlay boxes**
- **optional local LM post-editing**
- **optional microphone-based correction with Faster-Whisper**
- **structured export formats** for downstream processing

OCR is therefore not treated here as a one-time black-box click, but as an **editable working process**. That is exactly the core idea of the project.

---

## Features

- OCR with **Kraken** using separate recognition and segmentation models
- support for **images and PDFs**
- queue-based batch workflow for multiple files
- interactive display of recognized lines
- editable **overlay boxes** and line structure
- line operations such as **move, swap, add, delete, split, and reorder**
- configurable **reading direction**
- integrated **image editing** before OCR
- optional **local LM post-editing** via OpenAI-compatible servers
- optional **speech correction with Faster-Whisper**
- import of lines from **TXT** or **JSON**
- save / load projects via **JSON project files**
- multilingual interface (**German, English, French**)
- light and dark mode
- hardware selection for **CPU, CUDA, ROCm, and MPS**
- optional external backend installation for GPU acceleration
- hardware overview in the help dialog

---

## Image Editing

Bottled Kraken includes a preprocessing layer for documents that need more than just a simple OCR pass.

Available tools include:

- rotation
- crop area
- separator bars for double pages or split layouts
- grayscale
- contrast adjustment
- add white border
- smart splitting

This is especially helpful for poorly cropped scans, double pages, archive material, form pages, and low-contrast historical sources.

---

## OCR Workflow

A typical workflow in Bottled Kraken looks like this:

1. load an image or PDF
2. optionally prepare the page with image editing
3. load the **recognition model**
4. load the **segmentation model**
5. start Kraken OCR
6. review recognized lines and boxes
7. correct lines manually, with a local LM, or by voice input
8. export the result

Bottled Kraken uses Kraken directly from Python and is strongly built around the idea that OCR quality depends heavily on clean segmentation. That is why working with **`blla`** is the preferred approach whenever a suitable segmentation model is available.

---

## Overlay Boxes and Manual Segmentation

Bottled Kraken allows recognized line boxes to be edited manually.

This is useful when:

- automatic segmentation does not match the page structure
- individual lines need to be corrected
- historical forms or tables need manual box placement
- double pages or rotated scans require additional control

If needed, overlay boxes can be drawn or adjusted manually per line. This makes the OCR workflow more transparent and easier to correct than a fully automatic black-box process.

---

## Optional GPU Backends

The standard Bottled Kraken release is CPU-based. GPU support can be added later from inside the application.

The GPU backend installer can be started from:

```text
Options → CPU/GPU
```

Available backend targets include:

```text
CUDA (NVIDIA)
ROCm (AMD)
MPS (Apple Silicon, platform-dependent)
```

For NVIDIA CUDA and AMD ROCm, Bottled Kraken installs a separate backend environment outside the main executable. This backend contains its own Python environment and the required OCR runtime packages.

The main application remains unchanged.

This design has several advantages:

- the default release remains smaller
- users without GPU support do not need large GPU packages
- CUDA and ROCm can be installed only when needed
- backend installations stay isolated from the operating system
- system-wide CUDA, ROCm, and driver installations are not removed or modified

---

## Local LM Post-Editing

Bottled Kraken can post-process OCR results with a **local language model server**, as long as it provides an **OpenAI-compatible base URL**.

Typical local setups include:

| Server | Typical Base URL |
|---|---|
| LM Studio | `http://localhost:1234/v1` |
| Ollama | `http://localhost:11434/v1` |
| Jan | `http://127.0.0.1:1337/v1` |
| GPT4All | `http://localhost:4891/v1` |
| text-generation-webui | `http://127.0.0.1:5000/v1` |
| LocalAI | `http://localhost:8080/v1` |
| vLLM | `http://HOST:8000/v1` |

This post-editing is intended for local workflows in which OCR lines should be linguistically smoothed, standardized, or reviewed without moving the entire workflow into a cloud service.

---

## LM Page OCR and Manual Boxes

Bottled Kraken also contains LM-based page OCR helpers.

If the result does not match the visual line structure well enough, manual overlay boxes can be drawn per line by right-clicking a line. This allows the user to guide the OCR/post-processing workflow manually when automatic segmentation is not sufficient.

---

## Remote Access via SSH Tunnel

If your local LM server is running on another machine but is only bound to `127.0.0.1`, you can still use it via an SSH tunnel.

Example:

```bash
ssh -L 1234:127.0.0.1:1234 user@192.168.1.50
```

Then simply use the following in Bottled Kraken:

```text
http://127.0.0.1:1234/v1
```

---

## Speech Correction with Faster-Whisper

Bottled Kraken can use **Faster-Whisper** for line-based microphone correction.

This is useful when:

- an OCR line is heavily damaged
- individual fields or names are faster to speak than to type
- or a correction should intentionally remain limited to exactly one line

So this is not about full transcription of long audio files, but about **targeted corrections within the OCR workflow**.

---

## Export Formats

Bottled Kraken supports export to multiple output formats.

| Category | Formats |
|---|---|
| plain text | `txt` |
| structured data | `csv`, `json` |
| OCR formats | `ALTO XML`, `hOCR` |
| PDF | searchable PDF with image + invisible text layer |

This makes it possible to use the same OCR pass both for readable end results and for structured downstream processing.

---

## Project Files

Bottled Kraken can save and load project states as JSON project files.

This is useful when OCR work should be continued later, checked again, or transferred between machines. Project files can contain the loaded page structure, recognized text, line information, and related workflow data.

---

## Run from Source

### Requirements

- Windows, Linux, or macOS
- recommended: **Python 3.10 to 3.13**
- a working Python virtual environment
- a working Kraken / PyTorch CPU environment

The standard source setup installs the CPU baseline. Optional GPU backends can be installed separately from inside Bottled Kraken.

### Clone the Repository

```bash
git clone https://github.com/Testatost/Bottled-Kraken.git
cd Bottled-Kraken
```

### Create a Virtual Environment

```bash
python -m venv .venv
```

Activate it:

```bash
# Linux / macOS
source .venv/bin/activate

# Windows PowerShell
.venv\Scripts\Activate.ps1
```

### Install Dependencies

Install the runtime dependencies from `requirements.txt`:

```bash
python -m pip install --upgrade pip setuptools wheel
python -m pip install -r requirements.txt
```

The requirements file is intended for the CPU baseline. GPU support should be installed through the optional backend system inside Bottled Kraken.

### Start the Application

```bash
python main.py
```

---

## Build with PyInstaller

Bottled Kraken can be built with PyInstaller.

A typical build command is:

```bash
python -m PyInstaller --clean --noconfirm main.spec
```

On Windows PowerShell, a clean rebuild can be done with:

```powershell
Remove-Item -Recurse -Force build, dist
python -m PyInstaller --clean --noconfirm main.spec
```

On Linux:

```bash
rm -rf build dist
python -m PyInstaller --clean --noconfirm main.spec
```

The exact build result depends on the platform-specific `main.spec`.

---

## Model Management

Bottled Kraken does not ship with OCR models directly. Instead, you load the models that fit your material.

In practice, you will usually need:

- a **recognition model** for the script and source material
- and optionally a **segmentation model** for `blla`

A good public source for Kraken-compatible models is the Zenodo collection:

- <https://zenodo.org/communities/ocr_models/>

As a rule of thumb, a model trained on historical prints is usually much better for historical prints than a general-purpose model. The same applies to handwriting and form-heavy material.

---

## Hardware Notes

Bottled Kraken can run on CPU only. GPU acceleration is optional.

The help dialog contains a hardware overview that checks the current system and installed external backends. This check is meant as a practical orientation, not as a strict compatibility guarantee.

General notes:

- CPU mode is the default and most portable mode.
- NVIDIA CUDA can be added through the optional CUDA backend.
- AMD ROCm can be added through the optional ROCm backend.
- Apple Silicon MPS support depends on the macOS/PyTorch environment.
- GPU backends are installed separately from the main application.

---

## Why Bottled Kraken?

Many OCR tools stop after recognition. Bottled Kraken focuses exactly on the phase **between OCR and the finished final text**:

- when segmentation still needs correction
- when line structure matters
- when forms or archive pages require post-processing
- and when the work should remain as local and transparent as possible

If you are looking for a GUI around Kraken that does not just run OCR, but treats it as an editable workflow, then Bottled Kraken is built exactly for that use case.

---

## License

This repository is licensed under **MIT**.  
Please also note the licenses of the external models and libraries you use together with the application.
