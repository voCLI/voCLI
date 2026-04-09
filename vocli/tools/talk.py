"""Talk tool — voice conversation with TTS playback and STT transcription."""

from vocli.server import mcp


@mcp.tool()
async def talk(
    message: str,
    wait_for_response: bool = True,
    speed: float | None = None,
    voice: str | None = None,
) -> str:
    """Speak a message aloud and optionally listen for a voice response.

    Args:
        message: Text to speak aloud via TTS.
        wait_for_response: If True, listen for user's voice reply after speaking.
        speed: TTS speech speed (default 0.9). Lower is slower.
        voice: TTS voice name (default "alloy").

    Returns:
        If wait_for_response: the transcribed user speech.
        Otherwise: confirmation that the message was spoken.
    """
    from vocli import config as cfg
    from vocli.clients import synthesize, transcribe, check_stt_health, check_tts_health
    from vocli.audio import play_audio, record_audio, play_chime

    # Check if config exists
    conf = cfg.get_config()
    if not conf.get("assistant_name"):
        return "VOCLI is not configured yet. Run /vocli:config to set up your assistant name and preferences."

    speed = speed or conf.get("tts_speed", cfg.TTS_SPEED)
    voice = voice or conf.get("tts_voice", cfg.TTS_VOICE)

    # Auto-start servers if not running
    tts_ok, _ = await check_tts_health()
    stt_ok, _ = await check_stt_health()
    if not tts_ok or not stt_ok:
        if cfg.SERVER_MODE == "remote":
            unreachable = []
            if not tts_ok:
                unreachable.append(f"TTS at {cfg.TTS_URL}")
            if not stt_ok:
                unreachable.append(f"STT at {cfg.STT_URL}")
            return "Remote servers unreachable:\n" + "\n".join(f"  - {u}" for u in unreachable) + "\n\nCheck that serve.sh is running on your local machine."

        from vocli.tools.service import _start_server
        if not tts_ok:
            await _start_server("tts")
        if not stt_ok:
            await _start_server("stt")
        # Wait for startup (STT loads whisper model, can take a while)
        import asyncio
        for i in range(12):  # up to ~60 seconds
            await asyncio.sleep(5)
            tts_ok, _ = await check_tts_health()
            stt_ok, _ = await check_stt_health()
            if tts_ok and stt_ok:
                break

        if not tts_ok or not stt_ok:
            errors = []
            if not tts_ok:
                log_hint = _check_server_log("tts")
                errors.append(f"TTS server failed to start. {log_hint}")
            if not stt_ok:
                log_hint = _check_server_log("stt")
                errors.append(f"STT server failed to start. {log_hint}")
            return "Servers could not start.\n" + "\n".join(errors) + "\n\nRun /vocli:install to fix, or ask Claude to help troubleshoot."

    # 1. Synthesize and play the message
    try:
        wav_bytes = await synthesize(message, voice=voice, speed=speed)
        await play_audio(wav_bytes)
    except Exception as e:
        return f"TTS error: {e}"

    if not wait_for_response:
        return f"Spoke: {message}"

    # 2. Play chime to signal "start speaking"
    await play_chime()

    # 3. Record user's voice
    try:
        audio_bytes = await record_audio()
    except Exception as e:
        import sys as _sys
        if _sys.platform == "darwin":
            hint = "Check microphone access in System Settings > Privacy & Security > Microphone."
        else:
            hint = "Check that your microphone is connected and accessible (run: arecord -l to list devices)."
        return f"Recording error: {e}. {hint}"

    # 4. Transcribe
    try:
        text = await transcribe(audio_bytes)
    except Exception as e:
        return f"STT error: {e}"

    return text


def _check_engines_installed() -> str | None:
    """Check if required engines (faster-whisper, piper) are installed.
    Checks the system python3 (where servers run), not the MCP server's Python.
    Returns an error message if something is missing, None if all good."""
    import shutil
    import subprocess

    missing = []

    # Check faster-whisper in the system python3 (where STT server runs)
    python = shutil.which("python3")
    if python:
        result = subprocess.run(
            [python, "-c", "import faster_whisper"],
            capture_output=True, timeout=10,
        )
        if result.returncode != 0:
            missing.append("faster-whisper (speech-to-text)")
    else:
        missing.append("python3 not found on PATH")

    if not shutil.which("piper"):
        missing.append("piper-tts (text-to-speech)")

    if not shutil.which("ffmpeg"):
        missing.append("ffmpeg (audio processing)")

    from vocli import config as cfg
    from pathlib import Path
    if not Path(cfg.PIPER_MODEL).exists():
        missing.append("Piper voice model")

    if missing:
        items = "\n".join(f"  - {m}" for m in missing)
        return f"Missing dependencies:\n{items}\n\nRun /vocli:install to set everything up."

    return None


def _check_server_log(server_type: str) -> str:
    """Read the last few lines of a server log to give a helpful hint."""
    from vocli import config as cfg

    log_file = cfg.VOCLI_DIR / "logs" / f"{server_type}.log"
    if not log_file.exists():
        return "No log file found."

    try:
        lines = log_file.read_text().strip().split("\n")
        last_lines = lines[-5:]
        for line in reversed(last_lines):
            if "ModuleNotFoundError" in line:
                module = line.split("'")[1] if "'" in line else "unknown"
                return f"Missing Python package: {module}. Run /vocli:install."
            if "FileNotFoundError" in line:
                return "A required file is missing. Run /vocli:install."
            if "Error" in line or "error" in line:
                return f"Error: {line.strip()}"
        return f"Check log: {log_file}"
    except Exception:
        return f"Check log: {log_file}"
