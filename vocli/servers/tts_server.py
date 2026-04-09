"""OpenAI-compatible TTS server with switchable engines: piper or say."""

import json
import os
import subprocess
import sys
import tempfile
from http.server import HTTPServer, BaseHTTPRequestHandler

ENGINE = os.environ.get("TTS_ENGINE", "piper")
PORT = int(os.environ.get("TTS_PORT", "8880"))
BIND_HOST = os.environ.get("VOCLI_BIND_HOST", "127.0.0.1")
MAX_TEXT_LENGTH = 5000  # Max characters for TTS input
MAX_BODY_BYTES = 64 * 1024  # 64KB max request body
SAY_VOICE = os.environ.get("SAY_VOICE", "Reed (English (US))")
PIPER_MODEL = os.environ.get(
    "PIPER_MODEL",
    os.path.expanduser("~/.vocli/models/piper/en_US-ryan-high.onnx"),
)

SAY_VOICE_MAP = {
    "alloy": "Samantha",
    "nova": "Karen",
    "echo": "Daniel",
    "fable": "Daniel",
    "onyx": "Fred",
    "shimmer": "Shelley (English (US))",
}


def synth_say(text, voice):
    """Generate audio using macOS say."""
    mac_voice = SAY_VOICE_MAP.get(voice, SAY_VOICE)
    with tempfile.NamedTemporaryFile(suffix=".aiff", delete=False) as f:
        aiff_path = f.name
    wav_path = aiff_path.replace(".aiff", ".wav")
    try:
        subprocess.run(
            ["say", "-v", mac_voice, "-o", aiff_path, text],
            check=True, timeout=30,
        )
        subprocess.run(
            ["ffmpeg", "-y", "-i", aiff_path, wav_path],
            check=True, timeout=30,
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        with open(wav_path, "rb") as f:
            return f.read()
    finally:
        for p in [aiff_path, wav_path]:
            try:
                os.unlink(p)
            except OSError:
                pass


def synth_piper(text, voice, speed=1.0):
    """Generate audio using Piper TTS."""
    length_scale = 1.0 / speed if speed > 0 else 1.0
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        wav_path = f.name
    try:
        proc = subprocess.run(
            ["piper", "--model", PIPER_MODEL, "--output_file", wav_path,
             "--length_scale", str(length_scale)],
            input=text, capture_output=True, text=True, timeout=30,
        )
        if proc.returncode != 0:
            print(f"[vocli-tts] Piper error: {proc.stderr}")
            return None
        with open(wav_path, "rb") as f:
            return f.read()
    finally:
        try:
            os.unlink(wav_path)
        except OSError:
            pass


class TTSHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path in ("/v1/audio/speech", "/audio/speech"):
            length = int(self.headers.get("Content-Length", 0))
            if length > MAX_BODY_BYTES:
                self._respond(413, {"error": f"Request too large (max {MAX_BODY_BYTES // 1024}KB)"})
                return

            try:
                body = json.loads(self.rfile.read(length)) if length else {}
            except (json.JSONDecodeError, ValueError):
                self._respond(400, {"error": "Invalid JSON"})
                return

            text = body.get("input", "")
            if len(text) > MAX_TEXT_LENGTH:
                self._respond(400, {"error": f"Text too long (max {MAX_TEXT_LENGTH} chars)"})
                return

            voice = body.get("voice", "alloy")

            try:
                speed = float(body.get("speed", 0.9))
            except (ValueError, TypeError):
                self._respond(400, {"error": "Invalid speed value"})
                return
            if speed <= 0 or speed > 5.0:
                self._respond(400, {"error": "Speed must be between 0.1 and 5.0"})
                return

            if ENGINE == "piper":
                data = synth_piper(text, voice, speed)
            elif ENGINE == "say" and sys.platform == "darwin":
                data = synth_say(text, voice)
            else:
                self._respond(500, {"error": f"Engine '{ENGINE}' not available on this platform. Use piper."})
                return

            if data:
                self.send_response(200)
                self.send_header("Content-Type", "application/octet-stream")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)
            else:
                self._respond(500, {"error": "TTS synthesis failed"})
        else:
            self._respond(404, {"error": "not found"})

    def do_GET(self):
        if self.path == "/health":
            self._respond(200, {"status": "ok", "engine": ENGINE})
        elif self.path in ("/v1/models", "/models"):
            self._respond(200, {
                "data": [{"id": "tts-1", "object": "model"}],
                "object": "list",
            })
        else:
            self._respond(404, {"error": "not found"})

    def _respond(self, code, data):
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def log_message(self, fmt, *args):
        print(f"[vocli-tts:{ENGINE}] {args[0]}")


if __name__ == "__main__":
    if ENGINE == "say" and sys.platform != "darwin":
        print("[vocli-tts] WARNING: 'say' engine only works on macOS. Falling back to piper.")
        ENGINE = "piper"
    if ENGINE == "piper":
        if not PIPER_MODEL.endswith(".onnx"):
            print(f"[vocli-tts] ERROR: Model path must be an .onnx file, got: {PIPER_MODEL}")
            sys.exit(1)
        if not os.path.isfile(PIPER_MODEL):
            print(f"[vocli-tts] ERROR: Model file not found: {PIPER_MODEL}")
            sys.exit(1)
        print(f"[vocli-tts] Model: {PIPER_MODEL}")
    print(f"[vocli-tts] Starting on {BIND_HOST}:{PORT}, engine={ENGINE}")
    server = HTTPServer((BIND_HOST, PORT), TTSHandler)
    print(f"[vocli-tts] Ready at http://{BIND_HOST}:{PORT}")
    server.serve_forever()
