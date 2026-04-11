"""OpenAI-compatible TTS server with switchable engines: kokoro, piper, or say."""

import io
import json
import os
import subprocess
import sys
import tempfile
from http.server import HTTPServer, BaseHTTPRequestHandler

ENGINE = os.environ.get("TTS_ENGINE", "kokoro")
PORT = int(os.environ.get("TTS_PORT", "8880"))
BIND_HOST = os.environ.get("VOCLI_BIND_HOST", "127.0.0.1")
MAX_TEXT_LENGTH = 5000  # Max characters for TTS input
MAX_BODY_BYTES = 64 * 1024  # 64KB max request body
SAY_VOICE = os.environ.get("SAY_VOICE", "Reed (English (US))")
PIPER_MODEL = os.environ.get(
    "PIPER_MODEL",
    os.path.expanduser("~/.vocli/models/piper/en_US-ryan-high.onnx"),
)
KOKORO_MODEL = os.environ.get(
    "KOKORO_MODEL",
    os.path.expanduser("~/.vocli/models/kokoro/kokoro-v1.0.onnx"),
)
KOKORO_VOICES = os.environ.get(
    "KOKORO_VOICES",
    os.path.expanduser("~/.vocli/models/kokoro/voices-v1.0.bin"),
)

_kokoro = None

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


def get_kokoro():
    """Lazy-load Kokoro model."""
    global _kokoro
    if _kokoro is None:
        from kokoro_onnx import Kokoro
        print(f"[vocli-tts] Loading Kokoro model...")
        _kokoro = Kokoro(KOKORO_MODEL, KOKORO_VOICES)
        print(f"[vocli-tts] Kokoro loaded.")
    return _kokoro


def synth_kokoro(text, voice, speed=1.0):
    """Generate audio using Kokoro ONNX TTS."""
    import numpy as np
    kokoro = get_kokoro()
    samples, sample_rate = kokoro.create(text, voice=voice, speed=speed, lang="en-us")
    # Clamp to [-1, 1] to prevent clipping noise, then convert to 16-bit PCM WAV
    samples = np.clip(samples, -1.0, 1.0)
    buf = io.BytesIO()
    import wave
    pcm = (samples * 32767).astype(np.int16)
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(pcm.tobytes())
    return buf.getvalue()


def play_wav(wav_bytes):
    """Play WAV audio through the local speakers."""
    import numpy as np
    import sounddevice as sd
    import wave

    buf = io.BytesIO(wav_bytes)
    with wave.open(buf, "rb") as wf:
        sample_rate = wf.getframerate()
        frames = wf.readframes(wf.getnframes())
        dtype = np.int16 if wf.getsampwidth() == 2 else np.int32
        data = np.frombuffer(frames, dtype=dtype).astype(np.float32)
        if dtype == np.int16:
            data /= 32768.0
        elif dtype == np.int32:
            data /= 2147483648.0
    sd.play(data, samplerate=sample_rate)
    sd.wait()


def record_and_transcribe(stt_port):
    """Record from mic and send to STT server for transcription."""
    import numpy as np
    import sounddevice as sd
    import wave
    import urllib.request

    sample_rate = 16000
    frame_duration_ms = 30
    frame_samples = int(sample_rate * frame_duration_ms / 1000)
    max_duration = 60.0
    silence_threshold_ms = 800
    min_duration = 0.5

    # Play chime
    t = np.linspace(0, 0.15, int(sample_rate * 0.15), endpoint=False)
    chime = np.sin(2 * np.pi * 880 * t).astype(np.float32)
    fade = int(sample_rate * 0.02)
    chime[:fade] *= np.linspace(0, 1, fade)
    chime[-fade:] *= np.linspace(1, 0, fade)
    chime *= 0.3
    sd.play(chime, samplerate=sample_rate)
    sd.wait()

    # Record with VAD
    frames = []
    silent_ms = 0
    speech_detected = False
    import time
    start_time = time.time()

    def callback(indata, frame_count, time_info, status):
        frames.append(indata.copy())

    try:
        import webrtcvad
        vad = webrtcvad.Vad(2)
    except ImportError:
        vad = None

    with sd.InputStream(samplerate=sample_rate, channels=1, dtype="int16",
                        blocksize=frame_samples, callback=callback):
        while (time.time() - start_time) < max_duration:
            time.sleep(frame_duration_ms / 1000)
            if not vad or len(frames) == 0:
                continue
            raw = frames[-1].tobytes()
            chunk = raw[:frame_samples * 2]
            if len(chunk) < frame_samples * 2:
                continue
            if vad.is_speech(chunk, sample_rate):
                speech_detected = True
                silent_ms = 0
            else:
                silent_ms += frame_duration_ms
            if speech_detected and silent_ms >= silence_threshold_ms:
                break
            if (time.time() - start_time) < min_duration:
                continue

    if not frames:
        return ""

    audio_data = np.concatenate(frames, axis=0)
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(audio_data.tobytes())
    wav_bytes = buf.getvalue()

    # Send to STT server
    req = urllib.request.Request(
        f"http://127.0.0.1:{stt_port}/v1/audio/transcriptions",
        method="POST",
    )
    import uuid
    boundary = uuid.uuid4().hex
    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="file"; filename="audio.wav"\r\n'
        f"Content-Type: audio/wav\r\n\r\n"
    ).encode() + wav_bytes + (
        f"\r\n--{boundary}\r\n"
        f'Content-Disposition: form-data; name="model"\r\n\r\nwhisper-1\r\n'
        f"--{boundary}--\r\n"
    ).encode()
    req.add_header("Content-Type", f"multipart/form-data; boundary={boundary}")
    req.data = body
    resp = urllib.request.urlopen(req, timeout=30)
    result = json.loads(resp.read())
    return result.get("text", "")


class TTSHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path == "/v1/audio/speak":
            # Synthesize AND play locally — for remote mode
            length = int(self.headers.get("Content-Length", 0))
            if length > MAX_BODY_BYTES:
                self._respond(413, {"error": f"Request too large"})
                return
            try:
                body = json.loads(self.rfile.read(length)) if length else {}
            except (json.JSONDecodeError, ValueError):
                self._respond(400, {"error": "Invalid JSON"})
                return

            text = body.get("input", "")
            if not text.strip():
                self._respond(400, {"error": "Input text is required"})
                return
            if len(text) > MAX_TEXT_LENGTH:
                self._respond(400, {"error": f"Text too long"})
                return
            voice = body.get("voice", "alloy")
            try:
                speed = float(body.get("speed", 1.0))
            except (ValueError, TypeError):
                speed = 1.0
            if speed <= 0 or speed > 5.0:
                speed = 1.0

            try:
                if ENGINE == "kokoro":
                    data = synth_kokoro(text, voice, speed)
                elif ENGINE == "piper":
                    data = synth_piper(text, voice, speed)
                elif ENGINE == "say" and sys.platform == "darwin":
                    data = synth_say(text, voice)
                else:
                    self._respond(500, {"error": f"Engine not available"})
                    return
            except Exception as e:
                self._respond(500, {"error": f"TTS error: {e}"})
                return

            if data:
                try:
                    play_wav(data)
                    self._respond(200, {"status": "played"})
                except Exception as e:
                    self._respond(500, {"error": f"Playback error: {e}"})
            else:
                self._respond(500, {"error": "TTS synthesis failed"})

        elif self.path == "/v1/audio/listen":
            # Record from mic + transcribe via STT — for remote mode
            length = int(self.headers.get("Content-Length", 0))
            try:
                body = json.loads(self.rfile.read(length)) if length else {}
            except (json.JSONDecodeError, ValueError):
                body = {}
            stt_port = body.get("stt_port", 2022)
            try:
                text = record_and_transcribe(stt_port)
                self._respond(200, {"text": text})
            except Exception as e:
                self._respond(500, {"error": f"Listen error: {e}"})

        elif self.path in ("/v1/audio/speech", "/audio/speech"):
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
            if not text.strip():
                self._respond(400, {"error": "Input text is required"})
                return
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

            try:
                if ENGINE == "kokoro":
                    data = synth_kokoro(text, voice, speed)
                elif ENGINE == "piper":
                    data = synth_piper(text, voice, speed)
                elif ENGINE == "say" and sys.platform == "darwin":
                    data = synth_say(text, voice)
                else:
                    self._respond(500, {"error": f"Engine '{ENGINE}' not available on this platform. Use kokoro or piper."})
                    return
            except Exception as e:
                self._respond(500, {"error": f"TTS synthesis error: {e}"})
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
        print("[vocli-tts] WARNING: 'say' engine only works on macOS. Falling back to kokoro.")
        ENGINE = "kokoro"
    if ENGINE == "kokoro":
        if not os.path.isfile(KOKORO_MODEL):
            print(f"[vocli-tts] ERROR: Kokoro model not found: {KOKORO_MODEL}")
            sys.exit(1)
        if not os.path.isfile(KOKORO_VOICES):
            print(f"[vocli-tts] ERROR: Kokoro voices not found: {KOKORO_VOICES}")
            sys.exit(1)
        print(f"[vocli-tts] Model: {KOKORO_MODEL}")
        get_kokoro()  # Preload model
    elif ENGINE == "piper":
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
