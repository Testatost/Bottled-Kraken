from __future__ import annotations

import os
import tempfile
import zipfile
from pathlib import Path


def _project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _has_release_integrity_test(project_root: Path) -> bool:
    return (project_root / "tests" / "run_release_zip_integrity_tests.py").exists()


def _skip_path(path: Path, project_root: Path) -> bool:
    try:
        rel_parts = path.relative_to(project_root).parts
    except ValueError:
        return True
    blocked_dirs = {
        ".git",
        ".idea",
        ".mypy_cache",
        ".pytest_cache",
        ".ruff_cache",
        ".venv",
        "__pycache__",
        "build",
        "dist",
        "venv",
    }
    if any(part in blocked_dirs for part in rel_parts):
        return True
    name = path.name
    if name.endswith((".pyc", ".pyo", ".pyd", "~", ".tmp", ".bak", ".orig")):
        return True
    if name.lower().endswith(".zip"):
        return True
    return False


def _include_file(path: Path, project_root: Path) -> bool:
    if not path.is_file() or _skip_path(path, project_root):
        return False
    rel = path.relative_to(project_root).as_posix()
    if rel in {"main.py", "README.md", "LICENSE", "LICENSE.txt"}:
        return True
    if rel.startswith("bottled_kraken/"):
        return path.suffix in {".py", ".json", ".txt", ".md", ".png", ".svg", ".ico"}
    return False


def ensure_release_zip_for_tests() -> None:
    if os.environ.get("BK_DISABLE_AUTO_RELEASE_ZIP"):
        return
    project_root = _project_root()
    if not _has_release_integrity_test(project_root):
        return
    output_path = project_root.parent / "bottled_kraken_autorelease_source.zip"
    fd, tmp_name = tempfile.mkstemp(
        prefix="bottled_kraken_autorelease_",
        suffix=".zip",
        dir=str(project_root.parent),
    )
    os.close(fd)
    tmp_path = Path(tmp_name)
    try:
        with zipfile.ZipFile(tmp_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            for path in sorted(project_root.rglob("*")):
                if not _include_file(path, project_root):
                    continue
                zf.write(path, path.relative_to(project_root).as_posix())
        tmp_path.replace(output_path)
    finally:
        if tmp_path.exists():
            try:
                tmp_path.unlink()
            except OSError:
                pass
