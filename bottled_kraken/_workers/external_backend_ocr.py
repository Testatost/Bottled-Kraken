"""External OCR backend integration for Bottled Kraken.

This module lets the CPU one-file application discover and use separately
installed GPU backends such as the NVIDIA CUDA or AMD ROCm backend installers.
The main application remains CPU-capable; GPU OCR is delegated to a worker
process in the external backend environment.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from ..shared import QThread, Signal, OCRJob, RecordView, BBox


BACKEND_APP_DIR_NAME = "BottledKraken"
BACKEND_CACHE_TTL_SECONDS = 20.0

def _no_console_kwargs() -> Dict[str, object]:
    """Verhindert kurz aufpoppende CMD-Fenster bei subprocess-Aufrufen unter Windows."""
    if not sys.platform.startswith("win"):
        return {}

    kwargs: Dict[str, object] = {}

    if hasattr(subprocess, "CREATE_NO_WINDOW"):
        kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW

    try:
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = 0
        kwargs["startupinfo"] = startupinfo
    except Exception:
        pass

    return kwargs


@dataclass
class ExternalOCRBackend:
    kind: str
    name: str
    base_dir: str
    python: str
    worker: str
    info_path: str
    ok: bool = False
    detail: str = ""
    raw_info: Optional[Dict[str, Any]] = None
    self_test: Optional[Dict[str, Any]] = None


_BACKEND_CACHE: Dict[str, Tuple[float, Optional[ExternalOCRBackend]]] = {}


def _default_backend_root() -> Path:
    custom = os.environ.get("BOTTLED_KRAKEN_BACKENDS_DIR", "").strip()
    if custom:
        return Path(custom).expanduser()

    if sys.platform.startswith("win"):
        local = os.environ.get("LOCALAPPDATA", "").strip()
        if local:
            return Path(local) / BACKEND_APP_DIR_NAME / "backends"
        return Path.home() / "AppData" / "Local" / BACKEND_APP_DIR_NAME / "backends"

    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / BACKEND_APP_DIR_NAME / "backends"

    xdg = os.environ.get("XDG_DATA_HOME", "").strip()
    if xdg:
        return Path(xdg).expanduser() / BACKEND_APP_DIR_NAME / "backends"
    return Path.home() / ".local" / "share" / BACKEND_APP_DIR_NAME / "backends"


def _backend_dir_for_kind(kind: str) -> Path:
    return _default_backend_root() / kind


def _safe_read_backend_info(kind: str) -> Optional[Dict[str, Any]]:
    info_path = _backend_dir_for_kind(kind) / "backend_info.json"
    if not info_path.is_file():
        return None
    try:
        data = json.loads(info_path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            return None
        return data
    except Exception:
        return None


def _backend_info_to_obj(kind: str, data: Dict[str, Any]) -> Optional[ExternalOCRBackend]:
    base = _backend_dir_for_kind(kind)
    py = str(data.get("python") or "").strip()
    worker = str(data.get("worker") or "").strip()
    if not py:
        py = str(base / ".venv" / "bin" / "python")
    if not worker:
        worker = str(base / "worker_kraken_backend.py")
    if not Path(py).is_file() or not Path(worker).is_file():
        return None
    return ExternalOCRBackend(
        kind=kind,
        name=str(data.get("name") or kind),
        base_dir=str(base),
        python=py,
        worker=worker,
        info_path=str(base / "backend_info.json"),
        raw_info=data,
    )


def _run_backend_self_test(backend: ExternalOCRBackend, timeout: int = 40) -> ExternalOCRBackend:
    def _probe_backend_vram() -> Dict[str, Any]:
        """
        Zusätzliche VRAM-Probe direkt in der externen Backend-Python-Umgebung.

        Hintergrund:
        Ältere installierte Backend-Worker melden zwar CUDA/HIP und Gerätename,
        aber noch keinen VRAM. Die Hardware-Anzeige im Hinweise-Dialog soll trotzdem
        sofort nach einer Backend-Installation korrekt aktualisieren, ohne dass der
        Nutzer das Backend zwingend neu installieren muss.
        """
        code = (
            "import json, torch\n"
            "out = {}\n"
            "try:\n"
            "    ok = bool(torch.cuda.is_available() and torch.cuda.device_count() > 0)\n"
            "    out['cuda_available'] = ok\n"
            "    out['cuda_device_count'] = int(torch.cuda.device_count()) if hasattr(torch, 'cuda') else 0\n"
            "    if ok:\n"
            "        props = torch.cuda.get_device_properties(0)\n"
            "        total = int(getattr(props, 'total_memory', 0) or 0)\n"
            "        out['device_name'] = torch.cuda.get_device_name(0)\n"
            "        out['cuda_device_total_memory'] = total\n"
            "        out['cuda_device_total_memory_gb'] = round(total / (1024 ** 3), 1) if total else 0.0\n"
            "except Exception as exc:\n"
            "    out['vram_probe_error'] = repr(exc)\n"
            "print(json.dumps(out, ensure_ascii=False), flush=True)\n"
        )

        try:
            env = os.environ.copy()
            env.setdefault("PYTHONUTF8", "1")
            env.setdefault("PYTHONIOENCODING", "utf-8")

            p2 = subprocess.run(
                [backend.python, "-c", code],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=20,
                env=env,
                **_no_console_kwargs(),
            )

            raw = (p2.stdout or "").strip()
            if raw:
                start = raw.find("{")
                end = raw.rfind("}")
                if start >= 0 and end >= start:
                    data2 = json.loads(raw[start:end + 1])
                    return data2 if isinstance(data2, dict) else {}

        except Exception:
            pass

        return {}

    try:
        cmd = [backend.python, backend.worker, "--self-test", "--backend-kind", backend.kind]

        env = os.environ.copy()
        env.setdefault("PYTHONUTF8", "1")
        env.setdefault("PYTHONIOENCODING", "utf-8")

        p = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            env=env,
            **_no_console_kwargs(),
        )

        text = (p.stdout or "").strip()
        data = None

        if text:
            # The worker prints JSON only, but be tolerant of warnings before/after it.
            start = text.find("{")
            end = text.rfind("}")
            if start >= 0 and end >= start:
                data = json.loads(text[start:end + 1])

        if not isinstance(data, dict):
            data = {
                "ok": False,
                "error": (p.stderr or p.stdout or "No JSON self-test output").strip(),
            }

        # VRAM-Daten nachziehen, falls der Worker sie nicht selbst liefert.
        if data.get("ok") or data.get("cuda_available"):
            if not data.get("cuda_device_total_memory") and not data.get("cuda_device_total_memory_gb"):
                probe = _probe_backend_vram()
                for key, value in probe.items():
                    data.setdefault(key, value)

        backend.self_test = data
        backend.ok = bool(data.get("ok") or data.get("cuda_available"))

        if backend.ok:
            dev = str(data.get("device_name") or data.get("backend_kind") or backend.kind)

            if backend.kind == "nvidia-cuda":
                cuda = data.get("cuda_version")
                backend.detail = f"{dev} (CUDA {cuda})" if cuda else f"{dev} (CUDA)"

            elif backend.kind == "amd-rocm":
                hip = data.get("hip_version")
                backend.detail = f"{dev} (HIP {hip})" if hip else f"{dev} (ROCm)"

            else:
                backend.detail = dev

        else:
            backend.detail = str(data.get("error") or p.stderr or "Backend self-test failed").strip()

    except Exception as exc:
        backend.ok = False
        backend.detail = repr(exc)
        backend.self_test = {"ok": False, "error": repr(exc)}

    return backend

def get_external_ocr_backend(kind: str, *, refresh: bool = False) -> Optional[ExternalOCRBackend]:
    """Return an installed external OCR backend after a quick self-test."""
    kind = str(kind or "").strip().lower()
    if kind not in ("nvidia-cuda", "amd-rocm"):
        return None
    now = time.time()
    if not refresh:
        cached = _BACKEND_CACHE.get(kind)
        if cached and (now - cached[0]) <= BACKEND_CACHE_TTL_SECONDS:
            return cached[1]

    data = _safe_read_backend_info(kind)
    backend = _backend_info_to_obj(kind, data) if data else None
    if backend is not None:
        backend = _run_backend_self_test(backend)
    _BACKEND_CACHE[kind] = (now, backend)
    return backend


def get_external_ocr_backends(*, refresh: bool = False) -> Dict[str, ExternalOCRBackend]:
    out: Dict[str, ExternalOCRBackend] = {}
    for kind in ("nvidia-cuda", "amd-rocm"):
        b = get_external_ocr_backend(kind, refresh=refresh)
        if b is not None:
            out[kind] = b
    return out


def clear_external_ocr_backend_cache():
    _BACKEND_CACHE.clear()


EXTERNAL_KRAKEN_WORKER_SOURCE = r'''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Bottled Kraken external Kraken OCR worker.

This worker is written/updated by the Bottled Kraken CPU application when an
external GPU backend is used. It communicates with the main application through
line-delimited JSON on stdout.
"""

import argparse
import gc
import json
import math
import os
import re
import statistics
import sys
import traceback
import warnings
from typing import Any, List, Optional, Tuple

os.environ.setdefault("PYTHONUTF8", "1")
os.environ.setdefault("PYTHONIOENCODING", "utf-8")
os.environ.setdefault("LANG", "C.UTF-8")
os.environ.setdefault("LC_ALL", "C.UTF-8")

from PIL import Image
import torch
from kraken import blla, rpred
from kraken.lib import models, vgsl

warnings.filterwarnings("ignore", message=r"`blla\.segment\(\)` is deprecated.*", category=DeprecationWarning)
warnings.filterwarnings("ignore", message=r"`rpred\..*` is deprecated.*", category=DeprecationWarning)
warnings.filterwarnings("ignore", message=r"`TorchVGSLModel\.load_model` is deprecated.*", category=DeprecationWarning)

READING_TB_LR = 0
READING_TB_RL = 1
READING_BT_LR = 2
READING_BT_RL = 3
BBox = Tuple[int, int, int, int]
Point = Tuple[float, float]

ONLY_SYMBOL_LINE_RE = re.compile(r'^[\(\)\{\}\?\!\/\\\""„“\$\%\&\[\]\=,\.\-—_:;><\|\+\*#\'~`´\^°]+$')
NOISE_REPEAT_RE = re.compile(r'^([aäeéiioöuü])(?:[\s\.\,\-_:;]*\1){2,}$', re.IGNORECASE)
DOTS_ONLY_RE = re.compile(r'^(?:\.\s*){3,}$')

def emit(event: str, **payload):
    payload["event"] = event
    print(json.dumps(payload, ensure_ascii=False), flush=True)

def clean_text(text: Any) -> str:
    if text is None:
        return ""
    txt = str(text).replace("\r\n", "\n").replace("\r", "\n")
    txt = re.sub(r"[\t\u00a0]+", " ", txt)
    txt = re.sub(r"[ \f\v]+", " ", txt)
    txt = re.sub(r"\n{3,}", "\n\n", txt)
    return txt.strip()

def is_symbol_only_line(text: Any) -> bool:
    txt = clean_text(text)
    return bool(txt and ONLY_SYMBOL_LINE_RE.fullmatch(txt))

def is_noise_line(text: Any) -> bool:
    txt = clean_text(text)
    if not txt:
        return False
    return bool(NOISE_REPEAT_RE.fullmatch(txt) or DOTS_ONLY_RE.fullmatch(txt))

def is_effectively_empty(text: Any) -> bool:
    return clean_text(text) == ""

def coerce_points(obj: Any) -> List[Point]:
    if obj is None:
        return []
    if isinstance(obj, (list, tuple)):
        if not obj:
            return []
        first = obj[0]
        if isinstance(first, (list, tuple)) and len(first) == 2 and isinstance(first[0], (int, float)):
            try:
                return [(float(x), float(y)) for x, y in obj]
            except Exception:
                return []
        if isinstance(first, (list, tuple)) and first and isinstance(first[0], (list, tuple)) and len(first[0]) == 2:
            pts: List[Point] = []
            for contour in obj:
                pts.extend(coerce_points(contour))
            return pts
    return []

def bbox_from_points(points: List[Point], pad: int = 0) -> Optional[BBox]:
    if not points:
        return None
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    x0 = int(min(xs)) - pad
    y0 = int(min(ys)) - pad
    x1 = int(max(xs)) + pad
    y1 = int(max(ys)) + pad
    if x1 <= x0 or y1 <= y0:
        return None
    return x0, y0, x1, y1

def record_bbox(r: Any) -> Optional[BBox]:
    bbox = getattr(r, "bbox", None)
    if bbox:
        try:
            x0, y0, x1, y1 = [int(v) for v in bbox]
            if x1 > x0 and y1 > y0:
                return x0, y0, x1, y1
        except Exception:
            pass
    for attr in ("boundary", "polygon"):
        boundary = getattr(r, attr, None)
        if boundary:
            bb = bbox_from_points(coerce_points(boundary), pad=2)
            if bb:
                return bb
    baseline = getattr(r, "baseline", None)
    if baseline:
        bb = bbox_from_points(coerce_points(baseline), pad=2)
        if bb:
            x0, y0, x1, y1 = bb
            return x0, y0 - 14, x1, y1 + 14
    return None

def baseline_length(bl) -> float:
    pts = coerce_points(bl)
    if len(pts) < 2:
        return 0.0
    x1, y1 = pts[0]
    x2, y2 = pts[-1]
    return math.hypot(x2 - x1, y2 - y1)

def clamp_bbox(bb: BBox, w: int, h: int) -> Optional[BBox]:
    x0, y0, x1, y1 = bb
    x0 = max(0, min(w - 1, int(x0)))
    y0 = max(0, min(h - 1, int(y0)))
    x1 = max(0, min(w, int(x1)))
    y1 = max(0, min(h, int(y1)))
    if x1 <= x0 or y1 <= y0:
        return None
    return x0, y0, x1, y1

def expand_bbox(bb: Optional[BBox], image_width: int, image_height: int) -> Optional[BBox]:
    if not bb:
        return None
    x0, y0, x1, y1 = bb
    bh = max(1, y1 - y0)
    pad_x = max(2, int(round(bh * 0.10)))
    pad_y = max(1, int(round(bh * 0.08)))
    return clamp_bbox((x0 - pad_x, y0 - pad_y, x1 + pad_x, y1 + pad_y), image_width, image_height)

def sort_records(records, image_width: int, image_height: int, reading_mode: int):
    items = []
    for r in records:
        bb = record_bbox(r)
        if not bb:
            continue
        x0, y0, x1, y1 = bb
        items.append((r, bb, (x0 + x1) / 2.0, (y0 + y1) / 2.0, y0, x0))
    if not items:
        return list(records)
    heights = [max(1, bb[3] - bb[1]) for _, bb, *_ in items]
    med_h = statistics.median(heights) if heights else 20.0
    row_tol = max(6.0, med_h * 0.60)
    items.sort(key=lambda t: t[3])
    rows = []
    for item in items:
        placed = False
        for row in rows:
            if abs(item[3] - row["cy"]) <= row_tol:
                row["items"].append(item)
                row["cy"] = statistics.mean([x[3] for x in row["items"]])
                placed = True
                break
        if not placed:
            rows.append({"cy": item[3], "items": [item]})
    rev_y = reading_mode in (READING_BT_LR, READING_BT_RL)
    rev_x = reading_mode in (READING_TB_RL, READING_BT_RL)
    rows.sort(key=lambda row: row["cy"], reverse=rev_y)
    out = []
    for row in rows:
        row["items"].sort(key=lambda t: t[2], reverse=rev_x)
        out.extend([x[0] for x in row["items"]])
    return out

def kraken_device_arg(device: Any = None) -> str:
    if device is None:
        return "cpu"
    try:
        if isinstance(device, torch.device):
            if device.index is not None:
                return f"{device.type}:{device.index}"
            return str(device.type or "cpu")
    except Exception:
        pass
    text = str(device or "cpu").strip()
    return text or "cpu"

def load_rec_model(path: str, device: Any):
    dev = kraken_device_arg(device)
    try:
        return models.load_any(path, device=dev)
    except TypeError:
        return models.load_any(path)

def load_seg_model(path: str):
    return vgsl.TorchVGSLModel.load_model(path)

def segment(im: Image.Image, model: Any, device: Any):
    dev = kraken_device_arg(device)
    try:
        return blla.segment(im, model=model, device=dev, text_direction="horizontal-lr")
    except TypeError:
        try:
            return blla.segment(im, model=model, device=dev)
        except TypeError:
            return blla.segment(im, model=model)

def recognize(rec_model: Any, im: Image.Image, seg: Any):
    return rpred.rpred(rec_model, im, seg)

def filter_short_baselines(seg: Any):
    try:
        if hasattr(seg, "baselines") and hasattr(seg, "lines") and seg.baselines and seg.lines:
            new_baselines = []
            new_lines = []
            for bl, ln in zip(seg.baselines, seg.lines):
                if baseline_length(bl) >= 5.0:
                    new_baselines.append(bl)
                    new_lines.append(ln)
            seg.baselines = new_baselines
            seg.lines = new_lines
    except Exception:
        pass
    return seg

def load_image_gray(path: str) -> Image.Image:
    return Image.open(path).convert("L")

def expected_lines(seg: Any) -> Optional[int]:
    for attr in ("lines", "baselines"):
        v = getattr(seg, attr, None)
        if v is not None:
            try:
                return len(v)
            except Exception:
                pass
    return None

def choose_device(kind: str):
    kind = (kind or "").lower().strip()
    if kind in ("nvidia-cuda", "amd-rocm", "cuda", "rocm") and torch.cuda.is_available():
        return torch.device("cuda")
    return torch.device("cpu")

def device_label(kind: str, device):
    try:
        if device.type == "cuda":
            name = torch.cuda.get_device_name(0) if torch.cuda.device_count() > 0 else "GPU"
            cuda_ver = getattr(torch.version, "cuda", None)
            hip_ver = getattr(torch.version, "hip", None)
            if kind in ("amd-rocm", "rocm") or hip_ver:
                return name + (f" (HIP {hip_ver})" if hip_ver else " (ROCm)")
            return name + (f" (CUDA {cuda_ver})" if cuda_ver else " (CUDA)")
    except Exception:
        pass
    return "CPU"

def ocr_preset_boxes(img_path, im, boxes, rec_model, seg_model, device, reading_direction, file_idx, total_files):
    page_w, page_h = im.size
    valid = []
    for bb in boxes or []:
        if not bb:
            continue
        try:
            clamped = clamp_bbox(tuple(int(v) for v in bb), page_w, page_h)
            if clamped:
                valid.append(clamped)
        except Exception:
            pass
    out = []
    total = max(1, len(valid))
    for i, bb in enumerate(valid):
        x0, y0, x1, y1 = bb
        crop = im.crop((x0, y0, x1, y1))
        crop_records = []
        try:
            with torch.no_grad():
                seg = filter_short_baselines(segment(crop, seg_model, device))
                for rec in recognize(rec_model, crop, seg):
                    crop_records.append(rec)
            crop_records = sort_records(crop_records, crop.size[0], crop.size[1], reading_direction)
            parts = []
            for rec in crop_records:
                txt = clean_text(getattr(rec, "prediction", None))
                if txt and not is_symbol_only_line(txt) and not is_noise_line(txt):
                    parts.append(txt)
            final_text = " ".join(parts).strip()
        except Exception:
            final_text = ""
        finally:
            try:
                crop.close()
            except Exception:
                pass
        out.append({"idx": len(out), "text": final_text, "bbox": list(bb)})
        emit("progress", value=int(((file_idx + ((i + 1) / total)) / max(1, total_files)) * 100))
    return "\n".join(x["text"] for x in out).strip(), out

def ocr_page(img_path, rec_model, seg_model, device, reading_direction, file_idx, total_files, preset_boxes=None):
    im_orig = None
    im = None
    try:
        im_orig = load_image_gray(img_path)
        orig_w, orig_h = im_orig.size
        if preset_boxes:
            return ocr_preset_boxes(img_path, im_orig, preset_boxes, rec_model, seg_model, device, reading_direction, file_idx, total_files)
        im = im_orig
        scale_factor = 1.0
        min_dim = min(im.size)
        if min_dim < 1200:
            scale_factor = 2 if min_dim >= 700 else 3
            im = im.resize((im.size[0] * scale_factor, im.size[1] * scale_factor), Image.BICUBIC)
        with torch.no_grad():
            seg = filter_short_baselines(segment(im, seg_model, device))
        exp = expected_lines(seg)
        records = []
        done = 0
        with torch.no_grad():
            for rec in recognize(rec_model, im, seg):
                records.append(rec)
                done += 1
                if exp and exp > 0:
                    emit("progress", value=int(((file_idx + min(1.0, done / exp)) / max(1, total_files)) * 100))
        records = sort_records(records, im.size[0], im.size[1], reading_direction)
        rec_model_name = os.path.basename(str(rec_model)).lower()
        two_col_splitter = re.compile(r"\s{4,}")
        out = []
        lines = []
        page_w, page_h = orig_w, orig_h
        def rescale(bb):
            if not bb or scale_factor == 1.0:
                return bb
            x0, y0, x1, y1 = bb
            return (int(round(x0 / scale_factor)), int(round(y0 / scale_factor)), int(round(x1 / scale_factor)), int(round(y1 / scale_factor)))
        def is_header_like(bb, txt):
            x0, y0, x1, y1 = bb
            w = x1 - x0
            cx = (x0 + x1) / 2.0
            if w < 0.72 * page_w:
                return False
            if abs(cx - (page_w / 2.0)) > 0.20 * page_w:
                return False
            if y0 > 0.45 * page_h:
                return False
            if len((txt or "").strip()) > 90:
                return False
            return True
        rev_x = reading_direction in (READING_TB_RL, READING_BT_RL)
        for r in records:
            txt = clean_text(getattr(r, "prediction", None))
            if is_effectively_empty(txt) or is_symbol_only_line(txt) or is_noise_line(txt):
                continue
            bb = expand_bbox(rescale(record_bbox(r)), page_w, page_h)
            split_done = False
            if bb:
                x0, y0, x1, y1 = bb
                if (x1 - x0) > int(page_w * 0.80) and not is_header_like(bb, txt):
                    parts = two_col_splitter.split(txt, maxsplit=1)
                    if len(parts) == 2:
                        left_txt, right_txt = map(clean_text, parts)
                        mid = page_w // 2
                        left_bb = clamp_bbox((0, y0, mid, y1), page_w, page_h)
                        right_bb = clamp_bbox((mid, y0, page_w, y1), page_w, page_h)
                        parts_in_order = []
                        if left_bb and left_txt:
                            parts_in_order.append((left_txt, left_bb))
                        if right_bb and right_txt:
                            parts_in_order.append((right_txt, right_bb))
                        if rev_x:
                            parts_in_order.reverse()
                        for txt_part, bb_part in parts_in_order:
                            out.append({"idx": len(out), "text": txt_part, "bbox": list(bb_part)})
                            lines.append(txt_part)
                        split_done = bool(parts_in_order)
            if split_done:
                continue
            out.append({"idx": len(out), "text": txt, "bbox": list(bb) if bb else None})
            lines.append(txt)
        emit("progress", value=int(((file_idx + 1.0) / max(1, total_files)) * 100))
        return "\n".join(lines).strip(), out
    finally:
        try:
            if im is not None and im is not im_orig:
                im.close()
        except Exception:
            pass
        try:
            if im_orig is not None:
                im_orig.close()
        except Exception:
            pass
        gc.collect()
        try:
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        except Exception:
            pass

def self_test(kind: str) -> int:
    result = {
        "ok": False,
        "backend_kind": kind,
        "python": sys.version,
        "platform": sys.platform,
    }
    try:
        import torchvision
        result.update({
            "torch": getattr(torch, "__version__", "unknown"),
            "torchvision": getattr(torchvision, "__version__", "unknown"),
            "cuda_version": getattr(torch.version, "cuda", None),
            "hip_version": getattr(torch.version, "hip", None),
            "cuda_available": bool(torch.cuda.is_available()),
            "cuda_device_count": int(torch.cuda.device_count()) if hasattr(torch, "cuda") else 0,
        })
        if torch.cuda.is_available():
            result["device_name"] = torch.cuda.get_device_name(0)
            try:
                props = torch.cuda.get_device_properties(0)
                total_memory = int(getattr(props, "total_memory", 0) or 0)
                result["cuda_device_total_memory"] = total_memory
                result["cuda_device_total_memory_gb"] = round(total_memory / (1024 ** 3), 1) if total_memory else 0.0
            except Exception as exc:
                result["vram_probe_error"] = repr(exc)
        result["ok"] = bool(torch.cuda.is_available())
    except Exception as exc:
        result["error"] = repr(exc)
    print(json.dumps(result, ensure_ascii=False, indent=2), flush=True)
    return 0 if result.get("ok") else 1

def run_job(job_path: str, backend_kind: str) -> int:
    with open(job_path, "r", encoding="utf-8") as f:
        job = json.load(f)
    input_paths = list(job.get("input_paths") or [])
    rec_path = str(job.get("recognition_model_path") or "")
    seg_path = str(job.get("segmentation_model_path") or "")
    reading_direction = int(job.get("reading_direction") or 0)
    preset_by_path = job.get("preset_bboxes_by_path") or {}
    if not input_paths:
        emit("failed", message="No input paths.")
        return 2
    if not os.path.exists(rec_path):
        emit("failed", message="Recognition model not found.")
        return 2
    if not os.path.exists(seg_path):
        emit("failed", message="blla segmentation model not found.")
        return 2
    device = choose_device(backend_kind)
    emit("device_resolved", value=f"{backend_kind} -> {device}")
    emit("gpu_info", value=device_label(backend_kind, device))
    rec_model = load_rec_model(rec_path, device)
    seg_model = load_seg_model(seg_path)
    total = len(input_paths)
    for idx, img_path in enumerate(input_paths):
        emit("file_started", path=img_path)
        try:
            preset_boxes = preset_by_path.get(img_path) or []
            text, records = ocr_page(img_path, rec_model, seg_model, device, reading_direction, idx, total, preset_boxes=preset_boxes)
            emit("file_done", path=img_path, text=text, records=records)
        except Exception:
            emit("file_error", path=img_path, message=traceback.format_exc())
    emit("finished")
    return 0

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--backend-kind", default="nvidia-cuda")
    parser.add_argument("--job-json", default="")
    args = parser.parse_args()
    if args.self_test:
        return self_test(args.backend_kind)
    if args.job_json:
        try:
            return run_job(args.job_json, args.backend_kind)
        except Exception:
            emit("failed", message=traceback.format_exc())
            return 1
    print(json.dumps({"ok": False, "error": "Use --self-test or --job-json."}, ensure_ascii=False), flush=True)
    return 2

if __name__ == "__main__":
    raise SystemExit(main())
'''


def ensure_external_worker_script(backend: ExternalOCRBackend) -> bool:
    """Install or update the backend worker script in the external backend dir."""
    try:
        worker_path = Path(backend.worker)
        worker_path.parent.mkdir(parents=True, exist_ok=True)
        current = worker_path.read_text(encoding="utf-8") if worker_path.is_file() else ""
        if "--job-json" not in current or "Bottled Kraken external Kraken OCR worker" not in current:
            worker_path.write_text(EXTERNAL_KRAKEN_WORKER_SOURCE, encoding="utf-8")
            try:
                worker_path.chmod(0o755)
            except Exception:
                pass
        return True
    except Exception:
        return False


class ExternalBackendOCRWorker(QThread):
    file_started = Signal(str)
    file_done = Signal(str, str, list, object, list)
    file_error = Signal(str, str)
    progress = Signal(int)
    finished_batch = Signal()
    failed = Signal(str)
    device_resolved = Signal(str)
    gpu_info = Signal(str)

    def __init__(self, job: OCRJob, backend: ExternalOCRBackend):
        super().__init__()
        self.job = job
        self.backend = backend
        self._proc: Optional[subprocess.Popen] = None
        self._job_file: Optional[Path] = None

    def requestInterruption(self):  # type: ignore[override]
        super().requestInterruption()
        proc = self._proc
        if proc and proc.poll() is None:
            try:
                proc.terminate()
            except Exception:
                pass

    def _write_job_file(self) -> Path:
        import tempfile
        payload = {
            "input_paths": list(self.job.input_paths or []),
            "recognition_model_path": self.job.recognition_model_path,
            "segmentation_model_path": self.job.segmentation_model_path,
            "device": self.job.device,
            "reading_direction": self.job.reading_direction,
            "preset_bboxes_by_path": self.job.preset_bboxes_by_path or {},
        }
        fd, path = tempfile.mkstemp(prefix="bk_backend_job_", suffix=".json")
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False)
        self._job_file = Path(path)
        return self._job_file

    def _handle_event(self, data: Dict[str, Any]):
        event = data.get("event")
        if event == "file_started":
            self.file_started.emit(str(data.get("path") or ""))
        elif event == "file_done":
            path = str(data.get("path") or "")
            text = str(data.get("text") or "")
            records = []
            for idx, item in enumerate(data.get("records") or []):
                if not isinstance(item, dict):
                    continue
                raw_bb = item.get("bbox")
                bbox: Optional[BBox] = None
                if isinstance(raw_bb, (list, tuple)) and len(raw_bb) == 4:
                    try:
                        bbox = tuple(int(v) for v in raw_bb)  # type: ignore[assignment]
                    except Exception:
                        bbox = None
                records.append(RecordView(len(records), str(item.get("text") or ""), bbox))
            self.file_done.emit(path, text, [], None, records)
        elif event == "file_error":
            self.file_error.emit(str(data.get("path") or ""), str(data.get("message") or ""))
        elif event == "progress":
            try:
                self.progress.emit(max(0, min(100, int(data.get("value") or 0))))
            except Exception:
                pass
        elif event == "device_resolved":
            self.device_resolved.emit(str(data.get("value") or ""))
        elif event == "gpu_info":
            self.gpu_info.emit(str(data.get("value") or ""))
        elif event == "failed":
            self.failed.emit(str(data.get("message") or "External backend failed."))

    def run(self):
        try:
            if not ensure_external_worker_script(self.backend):
                raise RuntimeError("External backend worker could not be written or updated.")
            job_file = self._write_job_file()
            cmd = [
                self.backend.python,
                self.backend.worker,
                "--backend-kind",
                self.backend.kind,
                "--job-json",
                str(job_file),
            ]
            env = os.environ.copy()
            env.setdefault("PYTHONUTF8", "1")
            env.setdefault("PYTHONIOENCODING", "utf-8")
            self._proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                stdin=subprocess.DEVNULL,
                text=True,
                encoding="utf-8",
                errors="replace",
                bufsize=1,
                env=env,
                **_no_console_kwargs(),
            )
            assert self._proc.stdout is not None
            for line in self._proc.stdout:
                if self.isInterruptionRequested():
                    break
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                except Exception:
                    continue
                if isinstance(data, dict):
                    self._handle_event(data)
            if self.isInterruptionRequested():
                try:
                    if self._proc and self._proc.poll() is None:
                        self._proc.terminate()
                except Exception:
                    pass
                return
            rc = self._proc.wait(timeout=10) if self._proc else 1
            if rc != 0:
                self.failed.emit(f"External backend exited with code {rc}.")
                return
            self.progress.emit(100)
            self.finished_batch.emit()
        except Exception as exc:
            import traceback
            self.failed.emit(traceback.format_exc() if os.environ.get("BOTTLED_KRAKEN_DEBUG") else str(exc))
        finally:
            try:
                if self._job_file and self._job_file.exists():
                    self._job_file.unlink()
            except Exception:
                pass
