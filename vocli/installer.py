"""VOCLI installer — check and install dependencies."""

import shutil
import subprocess
import sys
from pathlib import Path

from vocli import config as cfg


def check_python_version() -> tuple[bool, str]:
    """Check Python >= 3.10."""
    v = sys.version_info
    ok = v >= (3, 10)
    return ok, f"Python {v.major}.{v.minor}.{v.micro}"


def check_ffmpeg() -> tuple[bool, str]:
    """Check if ffmpeg is installed."""
    path = shutil.which("ffmpeg")
    if path:
        return True, f"ffmpeg found at {path}"
    if sys.platform == "darwin":
        hint = "Install with: brew install ffmpeg"
    else:
        hint = "Install with: sudo apt install ffmpeg (or your distro's package manager)"
    return False, f"ffmpeg not found. {hint}"


def check_piper() -> tuple[bool, str]:
    """Check if piper-tts is installed."""
    path = shutil.which("piper")
    if path:
        return True, f"piper found at {path}"
    return False, "piper not found. Install with: pip install piper-tts"


def check_piper_model() -> tuple[bool, str]:
    """Check if the default Piper model exists."""
    model_path = Path(cfg.PIPER_MODEL)
    if model_path.exists():
        return True, f"Model at {model_path}"
    return False, f"Model not found at {model_path}"


def check_whisper() -> tuple[bool, str]:
    """Check if faster-whisper is importable."""
    try:
        import faster_whisper  # noqa: F401
        return True, "faster-whisper installed"
    except ImportError:
        return False, "faster-whisper not found. Install with: pip install faster-whisper"


def create_directories() -> tuple[bool, str]:
    """Create ~/.vocli directory structure."""
    dirs = [
        cfg.VOCLI_DIR / "models" / "piper",
        cfg.VOCLI_DIR / "models" / "whisper",
        cfg.VOCLI_DIR / "logs",
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
    return True, f"Created {cfg.VOCLI_DIR}"


def run_all_checks() -> list[tuple[str, bool, str]]:
    """Run all installation checks."""
    checks = [
        ("Python version", *check_python_version()),
        ("ffmpeg", *check_ffmpeg()),
        ("piper-tts", *check_piper()),
        ("Piper model", *check_piper_model()),
        ("faster-whisper", *check_whisper()),
        ("Directories", *create_directories()),
    ]
    return checks
