import os
from pathlib import Path
from typing import Optional

OUTPUT_DIR = Path(__file__).resolve().parent.parent.parent / "output"


def ensure_output_dir(subdir: Optional[str] = None) -> Path:
    path = OUTPUT_DIR
    if subdir:
        path = path / subdir
    path.mkdir(parents=True, exist_ok=True)
    return path


def safe_filename(name: str) -> str:
    invalid_chars = '<>:"/\\|?*'
    for c in invalid_chars:
        name = name.replace(c, "_")
    return name.strip()
