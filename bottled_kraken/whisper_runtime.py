from __future__ import annotations

import argparse
import json
import locale
import os
import sys
import traceback
from pathlib import Path
from typing import Sequence

from bottled_kraken.runtime_cli import application_cli_command


def utf8_child_environment(base: dict[str, str] | None = None) -> dict[str, str]:
    """Build an environment that enables UTF-8 before the child interpreter starts."""
    env = dict(os.environ if base is None else base)
    env["PYTHONUTF8"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"
    if os.name != "nt":
        current = str(env.get("LC_ALL") or env.get("LC_CTYPE") or env.get("LANG") or "")
        if "UTF-8" not in current.upper() and "UTF8" not in current.upper():
            env["LC_ALL"] = "C.UTF-8"
            env["LANG"] = "C.UTF-8"
    return env


def whisper_transcription_command(
    *,
    model_dir: str,
    wav_path: str,
    device: str,
    compute_type: str,
    language: str | None = None,
) -> list[str]:
    command = application_cli_command(
        [
            "--bk-whisper-transcribe",
            "--model",
            os.path.abspath(model_dir),
            "--wav",
            os.path.abspath(wav_path),
            "--device",
            str(device or "cpu"),
            "--compute-type",
            str(compute_type or "int8"),
        ]
    )
    if language:
        command.extend(["--language", str(language)])
    return command


def _enable_utf8_locale() -> None:
    os.environ["PYTHONUTF8"] = "1"
    os.environ["PYTHONIOENCODING"] = "utf-8"
    if os.name == "nt":
        return
    for candidate in ("C.UTF-8", "C.utf8", "en_US.UTF-8", "de_DE.UTF-8", ""):
        try:
            locale.setlocale(locale.LC_CTYPE, candidate)
            return
        except (locale.Error, ValueError):
            continue


def _close_frozen_splash() -> None:
    try:
        import pyi_splash

        pyi_splash.close()
    except Exception:
        pass


def _emit(payload: dict) -> None:
    # ASCII-only JSON makes the parent-side transport independent of locale.
    sys.stdout.write(json.dumps(payload, ensure_ascii=True, separators=(",", ":")) + "\n")
    sys.stdout.flush()


def run_whisper_transcription_cli(argv: Sequence[str]) -> int:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--model", required=True)
    parser.add_argument("--wav", required=True)
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--compute-type", default="int8")
    parser.add_argument("--language", default=None)
    args = parser.parse_args(list(argv))

    _close_frozen_splash()
    _enable_utf8_locale()
    model_path = str(Path(args.model).resolve())
    wav_path = str(Path(args.wav).resolve())

    try:
        from faster_whisper import WhisperModel

        active_device = args.device
        active_compute = args.compute_type
        kwargs = {
            "beam_size": 5,
            "vad_filter": False,
            "condition_on_previous_text": False,
            "task": "transcribe",
            "language": args.language or None,
        }
        try:
            model = WhisperModel(model_path, device=active_device, compute_type=active_compute)
            segments, info = model.transcribe(wav_path, **kwargs)
        except Exception as exc:
            lowered = str(exc).lower()
            if active_device == "cuda" and ("out of memory" in lowered or "cuda failed" in lowered):
                try:
                    import torch

                    if torch.cuda.is_available():
                        torch.cuda.empty_cache()
                except Exception:
                    pass
                active_device = "cpu"
                active_compute = "int8"
                model = WhisperModel(model_path, device=active_device, compute_type=active_compute)
                segments, info = model.transcribe(wav_path, **kwargs)
            else:
                raise

        text_parts: list[str] = []
        for segment in segments:
            value = getattr(segment, "text", "")
            if isinstance(value, bytes):
                value = value.decode("utf-8", errors="replace")
            else:
                value = str(value or "")
            value = value.strip()
            if value:
                text_parts.append(value)
        _emit(
            {
                "ok": True,
                "text": " ".join(text_parts).strip(),
                "language": str(getattr(info, "language", "") or ""),
                "device": active_device,
                "compute_type": active_compute,
            }
        )
        return 0
    except Exception as exc:
        _emit(
            {
                "ok": False,
                "error": str(exc),
                "exception": type(exc).__name__,
                "traceback": traceback.format_exc(),
            }
        )
        return 2


def parse_whisper_subprocess_output(raw: bytes | str) -> dict:
    if isinstance(raw, bytes):
        text = raw.decode("utf-8", errors="replace")
    else:
        text = str(raw or "")
    for line in reversed(text.splitlines()):
        candidate = line.strip()
        if not candidate.startswith("{"):
            continue
        try:
            value = json.loads(candidate)
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict) and "ok" in value:
            return value
    return {
        "ok": False,
        "error": text.strip() or "Whisper subprocess returned no result.",
        "traceback": text.strip(),
    }


__all__ = [
    "parse_whisper_subprocess_output",
    "run_whisper_transcription_cli",
    "utf8_child_environment",
    "whisper_transcription_command",
]
