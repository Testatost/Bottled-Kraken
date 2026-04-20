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
  <img src="Bottled Kraken Screenshot.png" alt="Bottled Kraken Screenshot" width="1000">
</p>

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

Bottled Kraken supports export to multiple output formats:

| Category | Formats |
|---|---|
| plain text | `txt` |
| structured data | `csv`, `json` |
| OCR formats | `ALTO XML`, `hOCR` |
| images | `png`, `jpg`, `bmp` |
| PDF | searchable PDF with image + invisible text layer |

This makes it possible to use the same OCR pass both for readable end results and for structured downstream processing.

---

## Run from Source

### Requirements

- Windows, Linux, or macOS
- recommended: **Python 3.10 or 3.11**
- a working Kraken / PyTorch environment

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

Since Bottled Kraken is currently provided as a source-based desktop application, the Python packages required by the current code should be installed in your local environment.

A practical starting point is:

```bash
pip install --upgrade pip
pip install pillow pyside6 reportlab torch kraken pymupdf numpy sounddevice huggingface_hub
```

Depending on your setup, additional packages for audio, GPU support, or Faster-Whisper may also be required.

### Start the Application

```bash
python main.py
```

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
