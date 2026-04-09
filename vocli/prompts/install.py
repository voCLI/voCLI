"""Install prompt — guides through VOCLI dependency setup."""

from vocli.server import mcp


@mcp.prompt()
def install() -> str:
    """Set up VOCLI — install all dependencies, models, and configure hooks."""
    return """You are helping the user set up VOCLI, a local voice layer for Claude Code.

VOCLI's MCP server is already running (that's how you're seeing this prompt). Now we need to install the heavy dependencies that run outside the MCP server: the STT engine (faster-whisper), TTS engine (piper), and voice models.

Walk through these steps one at a time, confirming each succeeds before moving on:

## Step 1: Check Python version
Run `python3 --version` and verify it's 3.10 or higher.

## Step 2: Check ffmpeg
Run `ffmpeg -version`. If not installed, suggest: `brew install ffmpeg` (macOS) or `sudo apt install ffmpeg` (Linux).

## Step 3: Install STT and TTS engines
These install into the system Python (where the STT/TTS servers run):
```bash
python3 -m pip install faster-whisper piper-tts
```

## Step 4: Create VOCLI directories
```bash
mkdir -p ~/.vocli/models/piper ~/.vocli/models/whisper ~/.vocli/logs
```

## Step 5: Download Piper voice model
```bash
curl -L -o ~/.vocli/models/piper/en_GB-northern_english_male-medium.onnx "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_GB/northern_english_male/medium/en_GB-northern_english_male-medium.onnx"
curl -L -o ~/.vocli/models/piper/en_GB-northern_english_male-medium.onnx.json "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_GB/northern_english_male/medium/en_GB-northern_english_male-medium.onnx.json"
```

## Step 6: Download Whisper model
This downloads the model on first run (~500MB for 'small'):
```bash
python3 -c "from faster_whisper import WhisperModel; m = WhisperModel('small', compute_type='int8'); print('Whisper model ready')"
```

## Step 7: Verify
```bash
python3 -c "import faster_whisper; print('faster-whisper OK')"
which piper && echo "piper OK"
ls ~/.vocli/models/piper/*.onnx && echo "Piper model OK"
```

## Step 8: Configure VOCLI
Installation done! Now proceed directly to configuration — ask the user:

1. "What should I be called?" (assistant name, e.g., "Jarvis", "Nova")
2. "What should I call you?" (user name)
3. "Auto-approve voice tools?" (yes/no, recommend yes)
4. "Enable task completion chime?" (yes/no)

Save to `~/.vocli/config.json` and add vocli tools to `~/.claude/settings.json` permissions.allow if auto-approve is enabled:
- `mcp__plugin_vocli_vocli__talk`

After each step, report success or any errors. If something fails, help troubleshoot before continuing.

## IMPORTANT: When everything is done, say EXACTLY this and NOTHING else:
"Setup complete! Default voice: **Northern English Male (medium)**. Run `/vocli:talk` to start a voice conversation!"
Do NOT summarize settings, do NOT list STT/TTS details, do NOT say "you're all set". Just the message above."""
