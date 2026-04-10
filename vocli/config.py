"""VOCLI configuration — env vars + ~/.vocli/config.json."""

import json
import os
import platform
from pathlib import Path

# Base directory
VOCLI_DIR = Path(os.environ.get("VOCLI_DIR", Path.home() / ".vocli"))

# Server URLs
STT_HOST = os.environ.get("VOCLI_STT_HOST", "127.0.0.1")
STT_PORT = int(os.environ.get("VOCLI_STT_PORT", "2022"))
STT_URL = os.environ.get("VOCLI_STT_URL", f"http://{STT_HOST}:{STT_PORT}")

TTS_HOST = os.environ.get("VOCLI_TTS_HOST", "127.0.0.1")
TTS_PORT = int(os.environ.get("VOCLI_TTS_PORT", "8880"))
TTS_URL = os.environ.get("VOCLI_TTS_URL", f"http://{TTS_HOST}:{TTS_PORT}")

# Audio
SAMPLE_RATE = int(os.environ.get("VOCLI_SAMPLE_RATE", "16000"))
CHANNELS = 1

# VAD
VAD_AGGRESSIVENESS = int(os.environ.get("VOCLI_VAD_AGGRESSIVENESS", "2"))
SILENCE_THRESHOLD_MS = int(os.environ.get("VOCLI_SILENCE_THRESHOLD_MS", "800"))
MAX_RECORDING_DURATION = float(os.environ.get("VOCLI_MAX_RECORDING", "60.0"))
MIN_RECORDING_DURATION = float(os.environ.get("VOCLI_MIN_RECORDING", "0.5"))

# TTS defaults
TTS_SPEED = float(os.environ.get("VOCLI_TTS_SPEED", "0.9"))
TTS_VOICE = os.environ.get("VOCLI_TTS_VOICE", "am_echo")
TTS_ENGINE = os.environ.get("VOCLI_TTS_ENGINE", "kokoro")

# STT defaults
WHISPER_MODEL = os.environ.get("VOCLI_WHISPER_MODEL", "small")
WHISPER_LANGUAGE = os.environ.get("VOCLI_WHISPER_LANGUAGE", "en")


def detect_compute_type() -> str:
    """Auto-detect optimal whisper compute_type based on CPU architecture."""
    machine = platform.machine().lower()
    if machine in ("arm64", "aarch64"):
        return "float16"
    return "int8"


WHISPER_COMPUTE_TYPE = os.environ.get("VOCLI_WHISPER_COMPUTE_TYPE", detect_compute_type())

# Server mode: "local" (default) or "remote"
SERVER_MODE = "local"

# Piper model path
PIPER_MODEL = os.environ.get(
    "VOCLI_PIPER_MODEL",
    str(VOCLI_DIR / "models" / "piper" / "en_US-ryan-high.onnx"),
)

# Kokoro model paths
KOKORO_MODEL = os.environ.get(
    "VOCLI_KOKORO_MODEL",
    str(VOCLI_DIR / "models" / "kokoro" / "kokoro-v1.0.onnx"),
)
KOKORO_VOICES = os.environ.get(
    "VOCLI_KOKORO_VOICES",
    str(VOCLI_DIR / "models" / "kokoro" / "voices-v1.0.bin"),
)

# Config file
CONFIG_FILE = VOCLI_DIR / "config.json"


def get_config() -> dict:
    """Load config from ~/.vocli/config.json."""
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE) as f:
            return json.load(f)
    return {}


def save_config(config: dict) -> None:
    """Save config to ~/.vocli/config.json."""
    VOCLI_DIR.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)


def update_config(**kwargs) -> dict:
    """Update specific config keys and save."""
    config = get_config()
    config.update(kwargs)
    save_config(config)
    return config


ALLOWED_WHISPER_MODELS = {"tiny", "base", "small", "medium", "large-v2", "large-v3"}
ALLOWED_COMPUTE_TYPES = {"int8", "float16", "float32"}
ALLOWED_SERVER_MODES = {"local", "remote"}


def load_runtime_config() -> None:
    """Patch module globals from config.json. Env vars take precedence."""
    global STT_URL, TTS_URL, SERVER_MODE, WHISPER_MODEL, WHISPER_COMPUTE_TYPE, TTS_ENGINE
    c = get_config()
    mode = c.get("server_mode", "local")
    if mode in ALLOWED_SERVER_MODES:
        SERVER_MODE = mode
    if "VOCLI_STT_URL" not in os.environ and "stt_url" in c:
        url = c["stt_url"]
        if isinstance(url, str) and url.startswith("http"):
            STT_URL = url
    if "VOCLI_TTS_URL" not in os.environ and "tts_url" in c:
        url = c["tts_url"]
        if isinstance(url, str) and url.startswith("http"):
            TTS_URL = url
    if "VOCLI_WHISPER_MODEL" not in os.environ and "whisper_model" in c:
        model = c["whisper_model"]
        if model in ALLOWED_WHISPER_MODELS:
            WHISPER_MODEL = model
    if "VOCLI_WHISPER_COMPUTE_TYPE" not in os.environ and "whisper_compute_type" in c:
        ct = c["whisper_compute_type"]
        if ct in ALLOWED_COMPUTE_TYPES:
            WHISPER_COMPUTE_TYPE = ct
    if "VOCLI_TTS_ENGINE" not in os.environ and "tts_engine" in c:
        engine = c["tts_engine"]
        if engine in {"kokoro", "piper", "say"}:
            TTS_ENGINE = engine


load_runtime_config()
