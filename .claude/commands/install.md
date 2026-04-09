---
description: Install VOCLI dependencies and configure
---

VOCLI's MCP server is already running. Now install the heavy dependencies (STT/TTS engines and models).

Walk through these steps one at a time, confirming each succeeds:

## Step 1: Check Python version
Run `python3 --version` — needs 3.10 or higher.

## Step 2: Check ffmpeg
Run `ffmpeg -version`. If missing: `brew install ffmpeg` (macOS) or `sudo apt install ffmpeg` (Linux).

## Step 3: Install STT and TTS engines
```bash
python3 -m pip install faster-whisper piper-tts
```

## Step 4: Create VOCLI directories
```bash
mkdir -p ~/.vocli/models/piper ~/.vocli/models/whisper ~/.vocli/logs
```

## Step 5: Detect architecture
```bash
python3 -c "import platform; m=platform.machine(); ct='float16' if m in ('arm64','aarch64') else 'int8'; print(f'{m}|{ct}')"
```
Tell the user what was detected (e.g., "Detected Apple Silicon (arm64) — will use float16 for faster performance" or "Detected Intel (x86_64) — using int8").

## Step 6: Choose Whisper model size
Ask: "What speech recognition model size? `tiny` (fastest, less accurate) or `small` (default, good balance)?"
Default to `small` if the user doesn't have a preference.

## Step 7: Download Piper voice model
```bash
curl -L -o ~/.vocli/models/piper/en_GB-northern_english_male-medium.onnx "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_GB/northern_english_male/medium/en_GB-northern_english_male-medium.onnx"
curl -L -o ~/.vocli/models/piper/en_GB-northern_english_male-medium.onnx.json "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_GB/northern_english_male/medium/en_GB-northern_english_male-medium.onnx.json"
```

## Step 8: Download Whisper model
Use the chosen model and detected compute type:
```bash
python3 -c "from faster_whisper import WhisperModel; m = WhisperModel('<model>', compute_type='<compute_type>'); print('Whisper model ready')"
```

## Step 9: Verify
```bash
python3 -c "import faster_whisper; print('faster-whisper OK')"
which piper && echo "piper OK"
ls ~/.vocli/models/piper/*.onnx && echo "Piper model OK"
```

## Step 10: Configure VOCLI
Ask the user:

1. "What should I be called?" (assistant name, e.g., "Jarvis", "Nova")
2. "What should I call you?" (user name)
3. "Auto-approve voice tools?" (yes/no, recommend yes)
4. "Enable task completion chime?" (yes/no)

Save to `~/.vocli/config.json` including `whisper_model` and `whisper_compute_type`. If auto-approve enabled, add to `~/.claude/settings.json` permissions.allow:
- `mcp__plugin_vocli_vocli__talk`

After each step, report success or troubleshoot errors.

## IMPORTANT: When everything is done, say EXACTLY this and NOTHING else:
"Setup complete! Default voice: **Northern English Male (medium)**. Run `/vocli:talk` to start a voice conversation!"
Do NOT summarize settings, do NOT list STT/TTS details, do NOT say "you're all set". Just the message above.
