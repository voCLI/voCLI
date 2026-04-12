---
description: Install VOCLI dependencies and configure
---

This command sets up everything VOCLI needs: the `uv` package manager (for running the MCP server), Python engines for STT/TTS, voice models, and user config. The MCP server itself runs via `uvx vocli serve`, which requires `uv` to be installed on the machine.

Walk through these steps one at a time, confirming each succeeds. If any step installs something new that affects the MCP server (notably `uv`), note that the user will need to restart Claude Code at the end for the MCP server to connect.

## Step 1: Check `uv` package manager
Run `uv --version`. If `uv` is missing or the command fails:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```
Then re-check with `uv --version`. If it still fails, tell the user to open a new terminal or source their shell profile (e.g. `source ~/.zshrc` or `source ~/.bashrc`) and retry. **Remember whether `uv` was freshly installed in this step — you will need to tell the user to restart Claude Code at the end if so, otherwise the MCP server won't pick it up.**

## Step 2: Find and save Python path
Run this to find and save the Python path that will be used for STT/TTS engines:
```bash
python3 -c "import sys; print(sys.executable)"
```
Save this path — ALL pip installs and verification steps below must use this exact path. This will also be saved to config later as `python_path`. Note: this Python is **separate** from the one that runs the MCP server (which runs via `uvx`). Its only job is to host `faster-whisper` and `kokoro-onnx` for the STT/TTS subprocesses.

## Step 3: Check Python version
Run `python3 --version` — needs 3.10 or higher.

## Step 4: Check ffmpeg
Run `ffmpeg -version`. If missing: `brew install ffmpeg` (macOS) or `sudo apt install ffmpeg` (Linux).

## Step 5: Install STT and TTS engines
```bash
python3 -m pip install faster-whisper kokoro-onnx soundfile
```

## Step 6: Create VOCLI directories
```bash
mkdir -p ~/.vocli/models/kokoro ~/.vocli/models/piper ~/.vocli/models/whisper ~/.vocli/logs
```

## Step 7: Detect architecture
```bash
python3 -c "import platform; m=platform.machine(); ct='float16' if m in ('arm64','aarch64') else 'int8'; print(f'{m}|{ct}')"
```
Tell the user what was detected (e.g., "Detected Apple Silicon (arm64) — will use float16 for faster performance" or "Detected Intel (x86_64) — using int8").

## Step 8: Choose Whisper model size
Ask: "What speech recognition model size? `tiny` (fastest, less accurate) or `small` (default, good balance)?"
Default to `small` if the user doesn't have a preference.

## Step 9: Download Kokoro voice model
```bash
curl -L -o ~/.vocli/models/kokoro/kokoro-v1.0.onnx "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.onnx"
curl -L -o ~/.vocli/models/kokoro/voices-v1.0.bin "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin"
```

## Step 10: Download Whisper model
Use the chosen model and detected compute type:
```bash
python3 -c "from faster_whisper import WhisperModel; m = WhisperModel('<model>', compute_type='<compute_type>'); print('Whisper model ready')"
```

## Step 11: Verify
```bash
python3 -c "import faster_whisper; print('faster-whisper OK')"
python3 -c "from kokoro_onnx import Kokoro; print('kokoro-onnx OK')"
ls ~/.vocli/models/kokoro/kokoro-v1.0.onnx && echo "Kokoro model OK"
```

## Step 12: Configure VOCLI
Ask the user:

1. "What should I be called?" (assistant name, e.g., "Friday", "Jarvis")
2. "What should I call you?" (user name)
3. "Auto-approve voice tools?" (yes/no, recommend yes)

Note: The default voice is **female (Sarah)**. Tell the user: "You can change the voice anytime — run `/vocli:config` and ask to change voice. There are 54 voices to choose from (male, female, American, British, and more)."

Save to `~/.vocli/config.json` including `whisper_model`, `whisper_compute_type`, and `python_path` (the path from Step 1). If auto-approve enabled, add to `~/.claude/settings.json` permissions.allow:
- `mcp__plugin_vocli_vocli__talk`
- `mcp__plugin_vocli_vocli__status`

After each step, report success or troubleshoot errors.

## IMPORTANT: When everything is done, say EXACTLY ONE of these and NOTHING else:

**If `uv` was freshly installed in Step 1**, say:
"Setup complete! Voice engine: **Kokoro** (high quality). I just installed `uv`, so you'll need to **restart Claude Code** once for the MCP server to pick it up. Then type **let's talk** or run `/vocli:talk` to start a voice conversation! If voice feels slow, run `/vocli:config` and switch to `piper` for faster performance."

**Otherwise** (uv was already installed), say:
"Setup complete! Voice engine: **Kokoro** (high quality). Just type **let's talk** or run `/vocli:talk` to start a voice conversation! If voice feels slow, run `/vocli:config` and switch to `piper` for faster performance."

Do NOT summarize settings, do NOT list STT/TTS details, do NOT say "you're all set". Just one of the messages above.
