"""Systemweite GPU- und Treibererkennung ohne Abhängigkeit von PyTorch.

Der System-Check darf nicht davon abhängen, ob die mit Bottled Kraken
installierte Torch-Version CUDA oder ROCm unterstützt. Dieses Modul fragt die
vom Betriebssystem bzw. von installierten Grafiktreibern bereitgestellten
Werkzeuge ab und liefert alle gefundenen Grafikadapter zurück.
"""
from __future__ import annotations

import csv
import json
import os
import platform
import re
import shutil
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Callable, Iterable, Sequence


CommandRunner = Callable[[Sequence[str], float], str]


@dataclass
class GPUDevice:
    name: str
    vendor: str = "unknown"
    driver_name: str = ""
    driver_version: str = ""
    vram_bytes: int = 0
    pci_id: str = ""
    compute_api: str = ""
    driver_loaded: bool = False
    source: str = ""

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def _no_console_kwargs() -> dict[str, object]:
    if os.name != "nt":
        return {}
    kwargs: dict[str, object] = {}
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


def _run_command(args: Sequence[str], timeout: float = 6.0) -> str:
    child_env = None
    if os.name != "nt":
        # In PyInstaller-Bundles zeigt LD_LIBRARY_PATH in das Bundle;
        # Systemtools wie lspci/nvidia-smi wuerden damit falsche
        # Bibliotheken laden und fehlschlagen oder abstuerzen.
        try:
            from bottled_kraken.subprocess_env import bk_clean_child_env
            child_env = bk_clean_child_env()
        except Exception:
            child_env = None
    try:
        completed = subprocess.run(
            list(args),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            check=False,
            env=child_env,
            **_no_console_kwargs(),
        )
    except (OSError, subprocess.SubprocessError):
        return ""
    if completed.returncode != 0:
        return ""
    return (completed.stdout or "").strip()


def _clean_text(value: object) -> str:
    return " ".join(str(value or "").replace("\x00", " ").split()).strip()


def _vendor_from_text(*values: object) -> str:
    text = " ".join(_clean_text(value).lower() for value in values)
    if any(token in text for token in ("nvidia", "ven_10de", "[10de:")):
        return "nvidia"
    if any(token in text for token in ("advanced micro devices", "amd", "ati ", "ven_1002", "[1002:")):
        return "amd"
    if any(token in text for token in ("intel", "ven_8086", "[8086:")):
        return "intel"
    if any(token in text for token in ("apple", "ven_106b", "[106b:")):
        return "apple"
    if any(token in text for token in ("microsoft", "ven_1414", "[1414:")):
        return "microsoft"
    return "unknown"


def _parse_size_bytes(value: object, default_unit: str = "bytes") -> int:
    if isinstance(value, (int, float)):
        number = float(value)
        unit = default_unit.lower()
    else:
        text = _clean_text(value).replace(",", ".")
        if not text:
            return 0
        match = re.search(r"(-?\d+(?:\.\d+)?)\s*([kmgt]i?b|bytes?|b)?", text, re.I)
        if not match:
            return 0
        try:
            number = float(match.group(1))
        except ValueError:
            return 0
        unit = (match.group(2) or default_unit).lower()
    if number <= 0:
        return 0
    multipliers = {
        "b": 1,
        "byte": 1,
        "bytes": 1,
        "kb": 1000,
        "kib": 1024,
        "mb": 1000 ** 2,
        "mib": 1024 ** 2,
        "gb": 1000 ** 3,
        "gib": 1024 ** 3,
        "tb": 1000 ** 4,
        "tib": 1024 ** 4,
    }
    return int(number * multipliers.get(unit, 1))


def _parse_nvidia_smi_csv(text: str) -> list[GPUDevice]:
    devices: list[GPUDevice] = []
    for row in csv.reader(text.splitlines()):
        if not row or len(row) < 3:
            continue
        name = _clean_text(row[0])
        if not name:
            continue
        devices.append(
            GPUDevice(
                name=name,
                vendor="nvidia",
                driver_name="NVIDIA",
                driver_version=_clean_text(row[2]),
                vram_bytes=_parse_size_bytes(row[1], "mib"),
                compute_api="CUDA",
                driver_loaded=True,
                source="nvidia-smi",
            )
        )
    return devices


def _parse_windows_video_controllers(text: str) -> list[GPUDevice]:
    try:
        payload = json.loads(text)
    except (TypeError, ValueError, json.JSONDecodeError):
        return []
    rows = payload if isinstance(payload, list) else [payload]
    devices: list[GPUDevice] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        name = _clean_text(row.get("Name"))
        if not name:
            continue
        pnp_id = _clean_text(row.get("PNPDeviceID"))
        vendor = _vendor_from_text(name, pnp_id, row.get("AdapterCompatibility"))
        status = _clean_text(row.get("Status")).lower()
        driver_version = _clean_text(row.get("DriverVersion"))
        devices.append(
            GPUDevice(
                name=name,
                vendor=vendor,
                driver_name=_clean_text(row.get("AdapterCompatibility")) or vendor.upper(),
                driver_version=driver_version,
                vram_bytes=_parse_size_bytes(row.get("AdapterRAM"), "bytes"),
                pci_id=pnp_id,
                compute_api="CUDA" if vendor == "nvidia" else ("ROCm/DirectML" if vendor == "amd" else "DirectML"),
                driver_loaded=bool(driver_version or status == "ok"),
                source="Win32_VideoController",
            )
        )
    return devices


def _parse_lspci(text: str) -> list[GPUDevice]:
    devices: list[GPUDevice] = []
    current: GPUDevice | None = None
    gpu_header_pattern = re.compile(
        r"^(?P<slot>[0-9a-fA-F:.]+)\s+"
        r"(?P<class>VGA compatible controller|3D controller|Display controller)"
        r"(?:\s*\[[^]]+\])?:\s*(?P<name>.+)$",
        re.I,
    )
    # Jede nicht eingerückte lspci-Zeile beginnt einen neuen PCI-Geräteblock.
    # Ohne diese Blockgrenze konnte z. B. der Treiber eines direkt folgenden
    # NVMe-Controllers fälschlich der zuvor gelisteten GPU zugeordnet werden.
    pci_header_pattern = re.compile(r"^[0-9a-fA-F:.]+\s+\S")

    for raw_line in text.splitlines():
        line = raw_line.rstrip()
        is_pci_header = bool(line and not line[0].isspace() and pci_header_pattern.match(line))
        if is_pci_header:
            if current is not None:
                devices.append(current)
                current = None
            header = gpu_header_pattern.match(line)
            if header:
                name = _clean_text(header.group("name"))
                current = GPUDevice(
                    name=name,
                    vendor=_vendor_from_text(name),
                    pci_id=_clean_text(header.group("slot")),
                    source="lspci",
                )
            continue

        if current is None:
            continue
        driver = re.match(r"^\s*Kernel driver in use:\s*(.+)$", line, re.I)
        if driver:
            current.driver_name = _clean_text(driver.group(1))
            current.driver_loaded = bool(current.driver_name)
            lower = current.driver_name.lower()
            if lower == "nvidia":
                current.compute_api = "CUDA"
            elif lower in {"amdgpu", "radeon"}:
                current.compute_api = "ROCm/OpenCL"
            elif lower in {"i915", "xe"}:
                current.compute_api = "OpenCL/Level Zero"
    if current is not None:
        devices.append(current)
    return devices


def _parse_system_profiler(text: str, os_version: str = "") -> list[GPUDevice]:
    try:
        payload = json.loads(text)
    except (TypeError, ValueError, json.JSONDecodeError):
        return []
    rows = payload.get("SPDisplaysDataType", []) if isinstance(payload, dict) else []
    devices: list[GPUDevice] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        name = _clean_text(row.get("sppci_model") or row.get("_name"))
        if not name:
            continue
        vendor_text = row.get("spdisplays_vendor") or row.get("spdisplays_vendor-id")
        vendor = _vendor_from_text(name, vendor_text)
        vram = row.get("spdisplays_vram") or row.get("spdisplays_vram_shared") or 0
        metal = _clean_text(row.get("spdisplays_metal"))
        devices.append(
            GPUDevice(
                name=name,
                vendor=vendor,
                driver_name="macOS graphics driver",
                driver_version=_clean_text(os_version),
                vram_bytes=_parse_size_bytes(vram),
                pci_id=_clean_text(row.get("spdisplays_device-id")),
                compute_api="Metal" if metal else "",
                driver_loaded=True,
                source="system_profiler",
            )
        )
    return devices


def _mapping_value(mapping: dict, *needles: str) -> object:
    for key, value in mapping.items():
        normalized = re.sub(r"[^a-z0-9]+", "", str(key).lower())
        if all(re.sub(r"[^a-z0-9]+", "", needle.lower()) in normalized for needle in needles):
            return value
    return ""


def _walk_dicts(value: object) -> Iterable[dict]:
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from _walk_dicts(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk_dicts(child)


def _parse_amd_json(text: str) -> list[GPUDevice]:
    """Parst sowohl rocm-smi- als auch amd-smi-JSON tolerant."""
    try:
        payload = json.loads(text)
    except (TypeError, ValueError, json.JSONDecodeError):
        return []
    devices: list[GPUDevice] = []
    seen_names: set[str] = set()
    for mapping in _walk_dicts(payload):
        name = _clean_text(
            _mapping_value(mapping, "card", "series")
            or _mapping_value(mapping, "product", "name")
            or _mapping_value(mapping, "market", "name")
            or _mapping_value(mapping, "asic", "name")
        )
        if not name or name.lower() in seen_names:
            continue
        if _vendor_from_text(name) not in {"amd", "unknown"}:
            continue
        driver_version = _clean_text(
            _mapping_value(mapping, "driver", "version")
            or _mapping_value(mapping, "driver")
        )
        vram = (
            _mapping_value(mapping, "vram", "total")
            or _mapping_value(mapping, "total", "memory")
            or _mapping_value(mapping, "memory", "total")
        )
        seen_names.add(name.lower())
        devices.append(
            GPUDevice(
                name=name,
                vendor="amd",
                driver_name="amdgpu",
                driver_version=driver_version,
                vram_bytes=_parse_size_bytes(vram),
                compute_api="ROCm",
                driver_loaded=True,
                source="amd-smi/rocm-smi",
            )
        )
    return devices


def _linux_driver_version(driver_name: str) -> str:
    driver = re.sub(r"[^a-zA-Z0-9_-]", "", driver_name or "")
    if not driver:
        return ""
    candidates = [
        Path("/sys/module") / driver / "version",
        Path("/proc/driver/nvidia/version") if driver == "nvidia" else Path("/__not_used__"),
    ]
    for path in candidates:
        try:
            text = path.read_text(encoding="utf-8", errors="replace").strip()
        except OSError:
            continue
        if driver == "nvidia":
            match = re.search(r"Kernel Module\s+([0-9.]+)", text)
            if match:
                return match.group(1)
        if text:
            return text.splitlines()[0].strip()
    return ""


def _normalized_name(name: str) -> str:
    text = _clean_text(name).lower()
    text = re.sub(r"\[[0-9a-f]{4}:[0-9a-f]{4}\]", " ", text)
    text = re.sub(r"\brev\s+[0-9a-f]+\b", " ", text)
    text = re.sub(r"\b(nvidia|amd|ati|intel|corporation|inc\.?|advanced micro devices)\b", " ", text)
    text = re.sub(r"\(r\)|\(tm\)", " ", text)
    return re.sub(r"[^a-z0-9]+", "", text)


def _same_device(left: GPUDevice, right: GPUDevice) -> bool:
    if left.pci_id and right.pci_id:
        left_id = left.pci_id.lower()
        right_id = right.pci_id.lower()
        if left_id == right_id or left_id in right_id or right_id in left_id:
            return True
    if left.vendor != "unknown" and right.vendor != "unknown" and left.vendor != right.vendor:
        return False
    left_name = _normalized_name(left.name)
    right_name = _normalized_name(right.name)
    if not left_name or not right_name:
        return False
    return left_name == right_name or left_name in right_name or right_name in left_name


def _driver_source_priority(source: str) -> int:
    parts = {part.strip().lower() for part in (source or "").split(",") if part.strip()}
    if "nvidia-smi" in parts or "amd-smi/rocm-smi" in parts:
        return 100
    if "win32_videocontroller" in parts or "system_profiler" in parts:
        return 90
    if "lspci" in parts:
        return 60
    if "torch-fallback" in parts:
        return 20
    return 0


def _merge_devices(devices: Iterable[GPUDevice]) -> list[GPUDevice]:
    merged: list[GPUDevice] = []
    for device in devices:
        if not _clean_text(device.name):
            continue
        existing = next((item for item in merged if _same_device(item, device)), None)
        if existing is None:
            merged.append(device)
            continue
        if existing.vendor == "unknown" and device.vendor != "unknown":
            existing.vendor = device.vendor
        if len(_clean_text(device.name)) < len(_clean_text(existing.name)) and device.vendor != "unknown":
            existing.name = device.name

        # Herstellerwerkzeuge liefern verlässlichere Treiberdaten als die
        # generische PCI-Auflistung. So überschreibt nvidia-smi beispielsweise
        # eine unvollständige oder fehlerhafte lspci-Zuordnung.
        incoming_is_authoritative = _driver_source_priority(device.source) > _driver_source_priority(existing.source)
        if device.driver_name and (not existing.driver_name or incoming_is_authoritative):
            existing.driver_name = device.driver_name
        if device.driver_version and (not existing.driver_version or incoming_is_authoritative):
            existing.driver_version = device.driver_version
        if device.vram_bytes > existing.vram_bytes:
            existing.vram_bytes = device.vram_bytes
        if not existing.pci_id and device.pci_id:
            existing.pci_id = device.pci_id
        if device.compute_api and (not existing.compute_api or incoming_is_authoritative):
            existing.compute_api = device.compute_api
        existing.driver_loaded = existing.driver_loaded or device.driver_loaded
        sources = [part for part in (existing.source + "," + device.source).split(",") if part]
        existing.source = ",".join(dict.fromkeys(sources))
    return merged


def _find_executable(name: str, extra_paths: Iterable[Path] = ()) -> str:
    found = shutil.which(name)
    if found:
        return found
    for path in extra_paths:
        try:
            if path.is_file():
                return str(path)
        except OSError:
            continue
    return ""


def _detect_windows(runner: CommandRunner) -> list[GPUDevice]:
    devices: list[GPUDevice] = []
    powershell = _find_executable("powershell") or _find_executable("pwsh")
    if powershell:
        script = (
            "Get-CimInstance Win32_VideoController | "
            "Select-Object Name,AdapterRAM,DriverVersion,PNPDeviceID,AdapterCompatibility,Status | "
            "ConvertTo-Json -Compress"
        )
        devices.extend(_parse_windows_video_controllers(runner([powershell, "-NoProfile", "-Command", script], 8.0)))
    program_files = Path(os.environ.get("ProgramFiles", r"C:\Program Files"))
    system_root = Path(os.environ.get("SystemRoot", r"C:\Windows"))
    nvidia_smi = _find_executable(
        "nvidia-smi",
        (
            program_files / "NVIDIA Corporation" / "NVSMI" / "nvidia-smi.exe",
            system_root / "System32" / "nvidia-smi.exe",
        ),
    )
    if nvidia_smi:
        devices.extend(
            _parse_nvidia_smi_csv(
                runner(
                    [
                        nvidia_smi,
                        "--query-gpu=name,memory.total,driver_version",
                        "--format=csv,noheader,nounits",
                    ],
                    8.0,
                )
            )
        )
    return devices


def _detect_linux(runner: CommandRunner) -> list[GPUDevice]:
    devices: list[GPUDevice] = []
    lspci = _find_executable("lspci")
    if lspci:
        devices.extend(_parse_lspci(runner([lspci, "-D", "-nnk"], 8.0)))
    nvidia_smi = _find_executable("nvidia-smi", (Path("/usr/lib/wsl/lib/nvidia-smi"),))
    if nvidia_smi:
        devices.extend(
            _parse_nvidia_smi_csv(
                runner(
                    [
                        nvidia_smi,
                        "--query-gpu=name,memory.total,driver_version",
                        "--format=csv,noheader,nounits",
                    ],
                    8.0,
                )
            )
        )
    for executable, arguments in (
        ("amd-smi", ["static", "--gpu", "--vram", "--driver", "--json"]),
        ("rocm-smi", ["--showproductname", "--showmeminfo", "vram", "--showdriverversion", "--json"]),
    ):
        path = _find_executable(executable)
        if path:
            devices.extend(_parse_amd_json(runner([path, *arguments], 8.0)))
    for device in devices:
        if device.driver_name and not device.driver_version:
            device.driver_version = _linux_driver_version(device.driver_name)
    return devices


def _detect_macos(runner: CommandRunner) -> list[GPUDevice]:
    profiler = _find_executable("system_profiler", (Path("/usr/sbin/system_profiler"),))
    if not profiler:
        return []
    text = runner([profiler, "SPDisplaysDataType", "-json"], 10.0)
    return _parse_system_profiler(text, platform.mac_ver()[0])


def _detect_torch_fallback() -> list[GPUDevice]:
    """Letzter Fallback; die normale Erkennung bleibt vollständig torch-frei."""
    try:
        import torch
    except Exception:
        return []
    try:
        if not torch.cuda.is_available() or torch.cuda.device_count() <= 0:
            return []
    except Exception:
        return []
    devices: list[GPUDevice] = []
    hip_version = _clean_text(getattr(getattr(torch, "version", None), "hip", ""))
    cuda_version = _clean_text(getattr(getattr(torch, "version", None), "cuda", ""))
    for index in range(int(torch.cuda.device_count())):
        try:
            name = _clean_text(torch.cuda.get_device_name(index)) or f"GPU {index + 1}"
            props = torch.cuda.get_device_properties(index)
            vram = int(getattr(props, "total_memory", 0) or 0)
        except Exception:
            continue
        vendor = _vendor_from_text(name)
        devices.append(
            GPUDevice(
                name=name,
                vendor=vendor,
                driver_name="PyTorch CUDA/HIP runtime",
                driver_version=hip_version or cuda_version,
                vram_bytes=vram,
                compute_api="ROCm" if hip_version else "CUDA",
                driver_loaded=True,
                source="torch-fallback",
            )
        )
    return devices


def detect_system_gpu_devices(
    *,
    runner: CommandRunner | None = None,
    platform_name: str | None = None,
    include_torch_fallback: bool = True,
) -> list[GPUDevice]:
    """Ermittelt alle sichtbaren Grafikadapter und zugehörige Treiber.

    ``runner`` und ``platform_name`` sind absichtlich injizierbar, damit die
    Erkennung in Tests ohne echte GPU vollständig simuliert werden kann.
    """
    command_runner = runner or _run_command
    system = (platform_name or platform.system()).strip().lower()
    if system.startswith("win"):
        devices = _detect_windows(command_runner)
    elif system in {"darwin", "mac", "macos"}:
        devices = _detect_macos(command_runner)
    else:
        devices = _detect_linux(command_runner)
    if include_torch_fallback:
        devices.extend(_detect_torch_fallback())
    return _merge_devices(devices)


def detect_system_gpus(**kwargs) -> list[dict[str, object]]:
    """JSON-/UI-freundliche Variante von :func:`detect_system_gpu_devices`."""
    return [device.to_dict() for device in detect_system_gpu_devices(**kwargs)]


__all__ = [
    "GPUDevice",
    "detect_system_gpu_devices",
    "detect_system_gpus",
]
