"""OpenAI-compatible STT server using faster-whisper."""

import io
import json
import os
import tempfile
from http.server import HTTPServer, BaseHTTPRequestHandler

PORT = int(os.environ.get("WHISPER_PORT", "2022"))
BIND_HOST = os.environ.get("VOCLI_BIND_HOST", "127.0.0.1")
MODEL = os.environ.get("WHISPER_MODEL", "small")
LANGUAGE = os.environ.get("WHISPER_LANGUAGE", "en")
COMPUTE_TYPE = os.environ.get("VOCLI_WHISPER_COMPUTE_TYPE", "int8")

_model = None


def get_model():
    global _model
    if _model is None:
        from faster_whisper import WhisperModel
        print(f"[vocli-stt] Loading model '{MODEL}' (compute_type={COMPUTE_TYPE})...")
        _model = WhisperModel(MODEL, compute_type=COMPUTE_TYPE)
        print(f"[vocli-stt] Model loaded.")
    return _model


def parse_multipart(handler):
    """Parse multipart form data from request."""
    content_type = handler.headers.get("Content-Type", "")
    content_length = int(handler.headers.get("Content-Length", 0))
    body = handler.rfile.read(content_length)

    if "multipart/form-data" not in content_type:
        return {}, None

    boundary = content_type.split("boundary=")[1].strip()
    parts = body.split(f"--{boundary}".encode())

    fields = {}
    file_data = None

    for part in parts:
        if b"Content-Disposition" not in part:
            continue
        header_end = part.find(b"\r\n\r\n")
        if header_end == -1:
            continue
        header = part[:header_end].decode("utf-8", errors="replace")
        data = part[header_end + 4:]
        if data.endswith(b"\r\n"):
            data = data[:-2]

        if 'name="file"' in header:
            file_data = data
        else:
            for line in header.split("\r\n"):
                if "Content-Disposition" in line:
                    for param in line.split(";"):
                        param = param.strip()
                        if param.startswith("name="):
                            name = param.split("=")[1].strip('"')
                            fields[name] = data.decode("utf-8", errors="replace")
    return fields, file_data


class STTHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path in ("/v1/audio/transcriptions", "/audio/transcriptions"):
            fields, file_data = parse_multipart(self)
            if not file_data:
                self._respond(400, {"error": "No audio file provided"})
                return

            lang = fields.get("language", LANGUAGE)
            if lang in ("auto", ""):
                lang = "en"
            response_format = fields.get("response_format", "json")

            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                f.write(file_data)
                tmp_path = f.name

            try:
                m = get_model()
                segments, info = m.transcribe(tmp_path, language=lang)
                text = " ".join(s.text for s in segments).strip()

                if response_format == "text":
                    self.send_response(200)
                    self.send_header("Content-Type", "text/plain")
                    self.end_headers()
                    self.wfile.write(text.encode())
                else:
                    self._respond(200, {"text": text})
            finally:
                os.unlink(tmp_path)
        else:
            self._respond(404, {"error": "not found"})

    def do_GET(self):
        if self.path == "/health":
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(b"ok")
        elif self.path in ("/v1/models", "/models"):
            self._respond(200, {
                "data": [{"id": "whisper-1", "object": "model"}],
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
        print(f"[vocli-stt] {args[0]}")


if __name__ == "__main__":
    print(f"[vocli-stt] Starting on {BIND_HOST}:{PORT}, model={MODEL}, compute={COMPUTE_TYPE}")
    get_model()
    server = HTTPServer((BIND_HOST, PORT), STTHandler)
    print(f"[vocli-stt] Ready at http://{BIND_HOST}:{PORT}")
    server.serve_forever()
