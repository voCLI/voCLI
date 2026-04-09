#!/usr/bin/env bash
set -e

# VOCLI Standalone Server — run on your local machine with mic/speakers.
# Starts STT (Whisper) and TTS (Piper) servers for remote Claude Code usage.

STT_PORT="${VOCLI_STT_PORT:-2022}"
TTS_PORT="${VOCLI_TTS_PORT:-8880}"
WHISPER_MODEL="${VOCLI_WHISPER_MODEL:-small}"
VOCLI_DIR="${HOME}/.vocli"
STT_PID=""
TTS_PID=""

cleanup() {
    echo ""
    echo "[vocli] Shutting down..."
    [ -n "$STT_PID" ] && kill "$STT_PID" 2>/dev/null
    [ -n "$TTS_PID" ] && kill "$TTS_PID" 2>/dev/null
    wait 2>/dev/null
    echo "[vocli] Stopped."
    exit 0
}
trap cleanup SIGINT SIGTERM

echo "============================================"
echo "  VOCLI Standalone Server"
echo "============================================"
echo ""

# --- Step 1: Check Python ---
if ! command -v python3 &>/dev/null; then
    echo "[ERROR] python3 not found. Install Python 3.10+ first."
    exit 1
fi

PY_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
PY_MAJOR=$(echo "$PY_VERSION" | cut -d. -f1)
PY_MINOR=$(echo "$PY_VERSION" | cut -d. -f2)
if [ "$PY_MAJOR" -lt 3 ] || { [ "$PY_MAJOR" -eq 3 ] && [ "$PY_MINOR" -lt 10 ]; }; then
    echo "[ERROR] Python 3.10+ required (found $PY_VERSION)."
    exit 1
fi
echo "[OK] Python $PY_VERSION"

# --- Step 2: Check ffmpeg ---
if ! command -v ffmpeg &>/dev/null; then
    if [[ "$OSTYPE" == "darwin"* ]]; then
        echo "[ERROR] ffmpeg not found. Install with: brew install ffmpeg"
    else
        echo "[ERROR] ffmpeg not found. Install with: sudo apt install ffmpeg"
    fi
    exit 1
fi
echo "[OK] ffmpeg found"

# --- Step 3: Install Python packages ---
echo "[...] Installing faster-whisper and piper-tts..."
python3 -m pip install -q faster-whisper piper-tts 2>/dev/null
echo "[OK] Python packages installed"

# --- Step 4: Create directories ---
mkdir -p "$VOCLI_DIR/models/piper" "$VOCLI_DIR/models/whisper" "$VOCLI_DIR/logs"

# --- Step 5: Download Piper model ---
PIPER_MODEL="$VOCLI_DIR/models/piper/en_US-ryan-high.onnx"
PIPER_CONFIG="$PIPER_MODEL.json"
if [ ! -f "$PIPER_MODEL" ]; then
    echo "[...] Downloading Piper voice model..."
    curl -sL -o "$PIPER_MODEL" "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/ryan/high/en_US-ryan-high.onnx"
    curl -sL -o "$PIPER_CONFIG" "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/ryan/high/en_US-ryan-high.onnx.json"
    echo "[OK] Piper model downloaded"
else
    echo "[OK] Piper model found"
fi

# --- Step 6: Pre-download Whisper model ---
echo "[...] Loading Whisper model '$WHISPER_MODEL' (this may take a moment)..."

# Detect compute type
ARCH=$(uname -m)
if [ "$ARCH" = "arm64" ] || [ "$ARCH" = "aarch64" ]; then
    COMPUTE_TYPE="float16"
else
    COMPUTE_TYPE="int8"
fi

WHISPER_MODEL="$WHISPER_MODEL" VOCLI_WHISPER_COMPUTE_TYPE="$COMPUTE_TYPE" \
    python3 -c "import os; from faster_whisper import WhisperModel; m=os.environ['WHISPER_MODEL']; ct=os.environ['VOCLI_WHISPER_COMPUTE_TYPE']; WhisperModel(m, compute_type=ct); print(f'[OK] Whisper model ready ({ct})')"

# --- Step 7: Detect local IP ---
if [[ "$OSTYPE" == "darwin"* ]]; then
    LOCAL_IP=$(ipconfig getifaddr en0 2>/dev/null || ipconfig getifaddr en1 2>/dev/null || echo "127.0.0.1")
else
    LOCAL_IP=$(hostname -I 2>/dev/null | awk '{print $1}')
    [ -z "$LOCAL_IP" ] && LOCAL_IP="127.0.0.1"
fi

# --- Step 8: Find server scripts ---
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_DIR="$(dirname "$SCRIPT_DIR")"
STT_SCRIPT="$REPO_DIR/vocli/servers/stt_server.py"
TTS_SCRIPT="$REPO_DIR/vocli/servers/tts_server.py"

if [ ! -f "$STT_SCRIPT" ] || [ ! -f "$TTS_SCRIPT" ]; then
    # Try pip-installed location
    STT_SCRIPT=$(python3 -c "from pathlib import Path; import vocli; print(Path(vocli.__file__).parent / 'servers' / 'stt_server.py')" 2>/dev/null)
    TTS_SCRIPT=$(python3 -c "from pathlib import Path; import vocli; print(Path(vocli.__file__).parent / 'servers' / 'tts_server.py')" 2>/dev/null)
    if [ ! -f "$STT_SCRIPT" ] || [ ! -f "$TTS_SCRIPT" ]; then
        echo "[ERROR] Could not find server scripts. Make sure you're running from the vocli repo or have vocli installed."
        exit 1
    fi
fi

# --- Step 9: Start servers ---
echo ""
echo "[...] Starting servers..."

export VOCLI_BIND_HOST="0.0.0.0"
export VOCLI_WHISPER_COMPUTE_TYPE="$COMPUTE_TYPE"

WHISPER_PORT="$STT_PORT" WHISPER_MODEL="$WHISPER_MODEL" \
    python3 "$STT_SCRIPT" >> "$VOCLI_DIR/logs/stt.log" 2>&1 &
STT_PID=$!

TTS_PORT="$TTS_PORT" TTS_ENGINE="piper" PIPER_MODEL="$PIPER_MODEL" \
    python3 "$TTS_SCRIPT" >> "$VOCLI_DIR/logs/tts.log" 2>&1 &
TTS_PID=$!

# Wait for servers to be ready
echo "[...] Waiting for servers to start..."
for i in $(seq 1 30); do
    STT_OK=$(curl -s "http://127.0.0.1:$STT_PORT/health" 2>/dev/null || true)
    TTS_OK=$(curl -s "http://127.0.0.1:$TTS_PORT/health" 2>/dev/null || true)
    if [ -n "$STT_OK" ] && [ -n "$TTS_OK" ]; then
        break
    fi
    sleep 2
done

if [ -z "$STT_OK" ] || [ -z "$TTS_OK" ]; then
    echo "[ERROR] Servers failed to start. Check logs:"
    echo "  STT: $VOCLI_DIR/logs/stt.log"
    echo "  TTS: $VOCLI_DIR/logs/tts.log"
    cleanup
    exit 1
fi

echo ""
echo "============================================"
echo "  VOCLI Servers Running"
echo "============================================"
echo ""
echo "  STT: http://${LOCAL_IP}:${STT_PORT}"
echo "  TTS: http://${LOCAL_IP}:${TTS_PORT}"
echo ""
echo "  Now go to your Claude Code session and run:"
echo ""
echo "    /vocli:remote-install"
echo ""
echo "  When prompted, enter these URLs:"
echo "    STT URL: http://${LOCAL_IP}:${STT_PORT}"
echo "    TTS URL: http://${LOCAL_IP}:${TTS_PORT}"
echo ""
echo "  Press Ctrl+C to stop servers."
echo "============================================"
echo ""

# Keep running
wait
