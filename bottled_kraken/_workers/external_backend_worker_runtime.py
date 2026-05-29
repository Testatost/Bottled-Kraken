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
warnings.filterwarnings("ignore", category=SyntaxWarning, module=r"coremltools(\.|$)")
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
MAX_KRAKEN_OCR_LINES = 500
Point = Tuple[float, float]
ONLY_SYMBOL_LINE_RE = re.compile(r'^[\(\)\{\}\?\!\/\\\""„“\$\%\&\[\]\=,\.\-—_:;><\|\+\*#\'~`´\^°]+$')
NOISE_REPEAT_RE = re.compile(r'^([aäeéiioöuü])(?:[\s\.\,\-_:;]*\1){2,}$', re.IGNORECASE)
DOTS_ONLY_RE = re.compile(r'^(?:\.\s*){3,}$')
def emit(event: str, **payload):
    payload["event"] = event
    print(json.dumps(payload, ensure_ascii=False), flush=True)
def parse_auto_revision_replacements(value):
    default = [("ſ", "s"), ("⸗", "-"), ("±", "+/-")]
    if value is None: return default
    out = []
    for raw in str(value).splitlines():
        line = raw.strip()
        if not line or line.startswith("#"): continue
        sep = "=>" if "=>" in line else "=" if "=" in line else None
        if not sep: continue
        src, dst = [part.strip() for part in line.split(sep, 1)]
        if src: out.append((src, dst))
    return out or default
def apply_auto_revision_replacements(text, replacements=None):
    txt = clean_text(text)
    for src, dst in parse_auto_revision_replacements(replacements): txt = txt.replace(src, dst)
    return re.sub(r"[ \t\r\f\v]+", " ", txt).strip()
def clean_text(text: Any) -> str:
    if text is None:
        return ""
    txt = str(text).replace("\r\n", "\n").replace("\r", "\n")
    txt = re.sub(r"[\t\u00a0]+", " ", txt)
    txt = re.sub(r"[ \f\v]+", " ", txt)
    txt = re.sub(r"\n{3,}", "\n\n", txt)
    return txt.strip()
def display_ocr_text(text: Any, auto_revision_enabled: bool = False, auto_revision_replacements=None) -> str:
    return apply_auto_revision_replacements(text, auto_revision_replacements) if bool(auto_revision_enabled) else clean_text(text)
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
            seg.baselines = new_baselines[:MAX_KRAKEN_OCR_LINES]
            seg.lines = new_lines[:MAX_KRAKEN_OCR_LINES]
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
def ocr_preset_boxes(img_path, im, boxes, rec_model, seg_model, device, reading_direction, file_idx, total_files, auto_revision_enabled=False, auto_revision_replacements=None):
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
                txt = display_ocr_text(getattr(rec, "prediction", None), auto_revision_enabled, auto_revision_replacements)
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
def ocr_page(img_path, rec_model, seg_model, device, reading_direction, file_idx, total_files, preset_boxes=None, auto_revision_enabled=False, auto_revision_replacements=None):
    im_orig = None
    im = None
    try:
        im_orig = load_image_gray(img_path)
        orig_w, orig_h = im_orig.size
        if preset_boxes:
            return ocr_preset_boxes(img_path, im_orig, preset_boxes, rec_model, seg_model, device, reading_direction, file_idx, total_files, auto_revision_enabled, auto_revision_replacements)
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
            txt = display_ocr_text(getattr(r, "prediction", None), auto_revision_enabled, auto_revision_replacements)
            if is_effectively_empty(txt) or is_symbol_only_line(txt) or is_noise_line(txt):
                continue
            bb = expand_bbox(rescale(record_bbox(r)), page_w, page_h)
            split_done = False
            if bb:
                x0, y0, x1, y1 = bb
                if (x1 - x0) > int(page_w * 0.80) and not is_header_like(bb, txt):
                    parts = two_col_splitter.split(txt, maxsplit=1)
                    if len(parts) == 2:
                        left_txt, right_txt = [display_ocr_text(part, auto_revision_enabled, auto_revision_replacements) for part in parts]
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
    auto_revision_enabled = bool(job.get("auto_revision_enabled", False))
    auto_revision_replacements = str(job.get("auto_revision_replacements", "") or "")
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
            text, records = ocr_page(img_path, rec_model, seg_model, device, reading_direction, idx, total, preset_boxes=preset_boxes, auto_revision_enabled=auto_revision_enabled, auto_revision_replacements=auto_revision_replacements)
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
