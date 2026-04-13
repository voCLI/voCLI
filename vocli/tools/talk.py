"""Talk tool — voice conversation with TTS playback and STT transcription."""

import asyncio
import json
import sys

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
        voice: TTS voice name (default "af_heart").

    Returns:
        If wait_for_response: the transcribed user speech.
        Otherwise: confirmation that the message was spoken.
    """
    from vocli import config as cfg
    from vocli.clients import check_stt_health, check_tts_health

    # Re-read config in case user changed settings
    cfg.load_runtime_config()

    # Check if config exists
    conf = cfg.get_config()
    if not conf.get("assistant_name"):
        return "VOCLI is not configured yet. Run /vocli:config to set up your assistant name and preferences."

    speed = speed if speed is not None else conf.get("tts_speed", cfg.TTS_SPEED)
    voice = voice if voice is not None else conf.get("voice", conf.get("tts_voice", cfg.TTS_VOICE))

    # Auto-start servers if not running, restart TTS if engine changed
    tts_ok, tts_info = await check_tts_health()
    stt_ok, _ = await check_stt_health()

    # Check if TTS engine matches config — restart if mismatched
    if tts_ok and cfg.SERVER_MODE == "local":
        try:
            health = json.loads(tts_info)
            running_engine = health.get("engine", "")
            if running_engine != cfg.TTS_ENGINE:
                from vocli.tools.service import _stop_server, _start_server
                await _stop_server("tts")
                await asyncio.sleep(1)
                await _start_server("tts")
                for _ in range(12):
                    await asyncio.sleep(5)
                    tts_ok, tts_info = await check_tts_health()
                    if tts_ok:
                        # Confirm new engine is correct
                        try:
                            new_health = json.loads(tts_info)
                            if new_health.get("engine") == cfg.TTS_ENGINE:
                                break
                        except (ValueError, KeyError):
                            break
        except (ValueError, KeyError):
            pass

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
        for _ in range(12):
            await asyncio.sleep(5)
            tts_ok, _ = await check_tts_health()
            stt_ok, _ = await check_stt_health()
            if tts_ok and stt_ok:
                break

        if not tts_ok or not stt_ok:
            errors = []
            if not tts_ok:
                errors.append(f"TTS server failed to start. {_check_server_log('tts')}")
            if not stt_ok:
                errors.append(f"STT server failed to start. {_check_server_log('stt')}")
            return "Servers could not start.\n" + "\n".join(errors) + "\n\nRun /vocli:install to fix, or ask Claude to help troubleshoot."

    if cfg.SERVER_MODE == "remote":
        return await _talk_remote(message, wait_for_response, voice, speed, conf, cfg)
    else:
        return await _talk_local(message, wait_for_response, voice, speed, conf)


async def _talk_remote(message, wait_for_response, voice, speed, conf, cfg):
    """Voice conversation via remote servers — audio stays on the remote machine."""
    import httpx

    # 1. Speak: send text to TTS server which plays it locally on the remote machine
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                f"{cfg.TTS_URL}/v1/audio/speak",
                json={"input": message, "voice": voice, "speed": speed},
            )
            resp.raise_for_status()
    except Exception as e:
        return f"TTS error: {e}"

    if not wait_for_response:
        return f"Spoke: {message}"

    # 2. Listen: TTS server records from mic and transcribes via STT
    try:
        async with httpx.AsyncClient(timeout=90) as client:
            resp = await client.post(
                f"{cfg.TTS_URL}/v1/audio/listen",
                json={"stt_port": cfg.STT_PORT},
            )
            resp.raise_for_status()
            result = resp.json()
            text = result.get("text", "")
    except Exception as e:
        return f"Listen error: {e}"

    if not text or not text.strip():
        return "[no speech detected]"

    if _is_wait_phrase(text):
        import asyncio
        wait_duration = conf.get("wait_duration", 30)
        await asyncio.sleep(wait_duration)
        try:
            async with httpx.AsyncClient(timeout=90) as client:
                resp = await client.post(
                    f"{cfg.TTS_URL}/v1/audio/listen",
                    json={"stt_port": cfg.STT_PORT},
                )
                resp.raise_for_status()
                result = resp.json()
                text = result.get("text", "")
        except Exception as e:
            return f"Error after wait: {e}"

    return text


async def _talk_local(message, wait_for_response, voice, speed, conf):
    """Voice conversation with local audio — mic and speakers on this machine."""
    from vocli.clients import synthesize, transcribe
    from vocli.audio import play_audio, record_audio, play_chime

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
        if sys.platform == "darwin":
            hint = "Check microphone access in System Settings > Privacy & Security > Microphone."
        else:
            hint = "Check that your microphone is connected and accessible (run: arecord -l to list devices)."
        return f"Recording error: {e}. {hint}"

    if not audio_bytes:
        return "No audio detected. Check your microphone connection."

    # 4. Transcribe
    try:
        text = await transcribe(audio_bytes)
    except Exception as e:
        return f"STT error: {e}"

    if not text or not text.strip():
        return "[no speech detected]"

    # 5. Wait phrase detection — pause and re-listen instead of returning
    if _is_wait_phrase(text):
        wait_duration = conf.get("wait_duration", 30)
        await asyncio.sleep(wait_duration)
        await play_chime()
        try:
            audio_bytes = await record_audio()
            if not audio_bytes:
                return "No audio detected after wait."
            text = await transcribe(audio_bytes)
        except Exception as e:
            return f"Error after wait: {e}"

    return text


WAIT_PHRASES = {
    "hang on", "hold on", "one sec", "one second", "give me a sec",
    "give me a second", "give me a moment", "just a moment", "just a sec",
    "wait", "wait a moment", "wait a sec", "wait a second",
    "one moment", "one minute", "brb",
}


def _is_wait_phrase(text: str) -> bool:
    """Check if transcribed text is a wait/pause phrase."""
    cleaned = text.strip().lower().rstrip(".!,?")
    return cleaned in WAIT_PHRASES


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
