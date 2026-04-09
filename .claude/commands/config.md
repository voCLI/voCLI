---
description: Configure VOCLI preferences
---

First, check if VOCLI is already configured:
```bash
cat ~/.vocli/config.json 2>/dev/null || echo "NOT_CONFIGURED"
```

**If already configured:** Show current settings and ask what the user wants to change. Only update the specific setting they request — don't re-run the full setup. Users can switch TTS engine by setting `tts_engine` to `kokoro` (natural, high quality) or `piper` (fast, lightweight).

### When user switches TTS engine:
**If switching to `piper`:** Check if piper is installed and model exists:
```bash
which piper && ls ~/.vocli/models/piper/en_US-ryan-high.onnx 2>/dev/null && echo "PIPER_READY" || echo "PIPER_MISSING"
```
If `PIPER_MISSING`, install it:
```bash
python3 -m pip install piper-tts
mkdir -p ~/.vocli/models/piper
curl -L -o ~/.vocli/models/piper/en_US-ryan-high.onnx "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/ryan/high/en_US-ryan-high.onnx"
curl -L -o ~/.vocli/models/piper/en_US-ryan-high.onnx.json "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/ryan/high/en_US-ryan-high.onnx.json"
```

**If switching to `kokoro`:** Check if kokoro-onnx is installed and model exists:
```bash
python3 -c "import kokoro_onnx" 2>/dev/null && ls ~/.vocli/models/kokoro/kokoro-v1.0.onnx 2>/dev/null && echo "KOKORO_READY" || echo "KOKORO_MISSING"
```
If `KOKORO_MISSING`, install it:
```bash
python3 -m pip install kokoro-onnx soundfile
mkdir -p ~/.vocli/models/kokoro
curl -L -o ~/.vocli/models/kokoro/kokoro-v1.0.onnx "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.onnx"
curl -L -o ~/.vocli/models/kokoro/voices-v1.0.bin "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin"
```

After installing, save `tts_engine` to config.json and restart the TTS server.

**If first time (NOT_CONFIGURED):** Ask these questions one at a time, waiting for each answer:

1. **"What should I be called?"** — Assistant name (e.g., "Jarvis", "Nova", "Friday")
2. **"What should I call you?"** — User's name (e.g., "Boss", "Chief")
3. **"Auto-approve voice tools?"** — Recommend yes. No permission prompts during voice. (yes/no)
4. **"Enable task completion chime?"** — Sound when Claude finishes a task. (yes/no)

Save config:
```bash
python3 -c "
import json
from pathlib import Path
config = {
    'assistant_name': '<answer>',
    'user_name': '<answer>',
    'hooks': {'auto_approve': True, 'notify_chime': True}
}
config_dir = Path.home() / '.vocli'
config_dir.mkdir(parents=True, exist_ok=True)
with open(config_dir / 'config.json', 'w') as f:
    json.dump(config, f, indent=2)
print('Saved')
"
```

If auto-approve enabled, add these to `~/.claude/settings.json` under `permissions.allow`:
- `mcp__plugin_vocli_vocli__talk`
- `mcp__plugin_vocli_vocli__status`

Confirm setup and suggest `/vocli:talk`. Servers start automatically — no manual step needed.
