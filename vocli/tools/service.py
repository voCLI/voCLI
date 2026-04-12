"""Service tool — manage STT/TTS server processes."""

import asyncio
import os
import shutil
import signal
import subprocess
import sys
from typing import Literal

from vocli.server import mcp


@mcp.tool()
async def service(
    action: Literal["start", "stop", "restart", "status"] = "status",
    target: Literal["all", "stt", "tts"] = "all",
) -> str:
    """Manage VOCLI STT and TTS server processes.

    Args:
        action: What to do — start, stop, restart, or check status.
        target: Which server — all, stt, or tts.

    Returns:
        Result of the action.
    """
    from vocli import config as cfg
    from vocli.clients import check_stt_health, check_tts_health

    targets = ["stt", "tts"] if target == "all" else [target]
    results = []

    for t in targets:
        if action == "status":
            if t == "stt":
                ok, info = await check_stt_health()
                results.append(f"STT: {'running' if ok else 'stopped'} ({info})")
            else:
                ok, info = await check_tts_health()
                results.append(f"TTS: {'running' if ok else 'stopped'} ({info})")

        elif action == "start":
            result = await _start_server(t)
            results.append(result)

        elif action == "stop":
            result = await _stop_server(t)
            results.append(result)

        elif action == "restart":
            await _stop_server(t)
            await asyncio.sleep(1)
            result = await _start_server(t)
            results.append(result)

    return "\n".join(results)


async def _server_healthy(server_type: str) -> bool:
    """Check if a server is responding via HTTP health check."""
    from vocli.clients import check_stt_health, check_tts_health
    if server_type == "stt":
        ok, _ = await check_stt_health()
    else:
        ok, _ = await check_tts_health()
    return ok


async def _start_server(server_type: str) -> str:
    """Start a server process in the background."""
    from vocli import config as cfg

    if cfg.SERVER_MODE == "remote":
        return f"{server_type.upper()}: remote mode — servers managed externally"

    if server_type == "stt":
        port = cfg.STT_PORT
        script = _get_server_script("stt_server")
        env_vars = {
            "WHISPER_PORT": str(port),
            "WHISPER_MODEL": cfg.WHISPER_MODEL,
            "WHISPER_LANGUAGE": cfg.WHISPER_LANGUAGE,
            "VOCLI_WHISPER_COMPUTE_TYPE": cfg.WHISPER_COMPUTE_TYPE,
        }
    else:
        port = cfg.TTS_PORT
        script = _get_server_script("tts_server")
        env_vars = {
            "TTS_PORT": str(port),
            "KOKORO_MODEL": cfg.KOKORO_MODEL,
            "KOKORO_VOICES": cfg.KOKORO_VOICES,
        }

    if not script:
        return f"{server_type.upper()}: server script not found"

    if await _server_healthy(server_type):
        return f"{server_type.upper()}: already running on port {port}"

    # Only pass necessary env vars to child process, not secrets
    safe_keys = {"PATH", "HOME", "USER", "LANG", "LC_ALL", "TMPDIR", "SHELL"}
    env = {k: v for k, v in os.environ.items() if k in safe_keys}
    env.update(env_vars)

    log_dir = cfg.VOCLI_DIR / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / f"{server_type}.log"

    # Use the Python path saved during install (where deps are installed)
    conf = cfg.get_config()
    python = conf.get("python_path") or shutil.which("python3") or sys.executable

    with open(log_file, "a") as log:
        subprocess.Popen(
            [python, str(script)],
            env=env,
            stdout=log,
            stderr=log,
        )

    await asyncio.sleep(2)
    if await _server_healthy(server_type):
        return f"{server_type.upper()}: started on port {port}"
    else:
        return f"{server_type.upper()}: failed to start. Check {log_file}"


async def _stop_server(server_type: str) -> str:
    """Stop a server process by finding it on its port."""
    from vocli import config as cfg

    if cfg.SERVER_MODE == "remote":
        return f"{server_type.upper()}: remote mode — manage servers on your local machine"

    port = cfg.STT_PORT if server_type == "stt" else cfg.TTS_PORT

    try:
        if sys.platform == "darwin":
            result = await asyncio.to_thread(
                subprocess.run,
                ["lsof", "-ti", f":{port}"],
                capture_output=True, text=True,
            )
            pids = [p for p in result.stdout.strip().split("\n") if p]
        else:
            result = await asyncio.to_thread(
                subprocess.run,
                ["fuser", f"{port}/tcp"],
                capture_output=True, text=True,
            )
            pids = result.stdout.strip().split()

        # Validate PIDs are numeric
        valid_pids = []
        for p in pids:
            try:
                pid_int = int(p)
                if pid_int > 0:
                    valid_pids.append(pid_int)
            except ValueError:
                continue

        if not valid_pids:
            return f"{server_type.upper()}: not running"
        for pid in valid_pids:
            os.kill(pid, signal.SIGTERM)
        return f"{server_type.upper()}: stopped (pid {', '.join(str(p) for p in valid_pids)})"
    except FileNotFoundError:
        return f"{server_type.upper()}: could not find process (lsof/fuser not available)"
    except Exception as e:
        return f"{server_type.upper()}: error stopping — {e}"


def _get_server_script(name: str):
    """Get path to a server script."""
    from pathlib import Path
    script = Path(__file__).parent.parent / "servers" / f"{name}.py"
    return script if script.exists() else None
