---
description: Configure VOCLI preferences
---

First, check if VOCLI is already configured:
```bash
cat ~/.vocli/config.json 2>/dev/null || echo "NOT_CONFIGURED"
```

**If already configured:** Show current settings and ask what the user wants to change. Only update the specific setting they request — don't re-run the full setup.

### When user wants to change voice:
Show available Kokoro voices and let them pick:

- **American Female:** af_alloy, af_aoede, af_bella, af_heart, af_jessica, af_kore, af_nicole, af_nova, af_river, af_sarah (default), af_sky
- **American Male:** am_adam, am_echo, am_eric, am_fenrir, am_liam, am_michael, am_onyx, am_puck
- **British Female:** bf_alice, bf_emma, bf_isabella, bf_lily
- **British Male:** bm_daniel, bm_fable, bm_george, bm_lewis

Save the chosen voice as `voice` in config.json. The change takes effect on the next `talk` call — no restart needed.

### When user wants to change audio devices:
List available devices by running:
```bash
~/.vocli/venv/bin/python -c "
import sounddevice as sd
for i, d in enumerate(sd.query_devices()):
    io = []
    if d['max_input_channels'] > 0: io.append('IN')
    if d['max_output_channels'] > 0: io.append('OUT')
    print(f'  [{i}] {d[\"name\"]} ({\", \".join(io)})')
"
```
If `~/.vocli/venv/bin/python` doesn't exist (user hasn't run `/vocli:install` yet), fall back to system `python3`.

Show the list and let the user pick an input device (mic) and output device (speakers/headphones).
Save as `input_device` and `output_device` in config.json. Use the device name (not index). Set to `"default"` to use system default.

**If first time (NOT_CONFIGURED):** Ask these questions one at a time, waiting for each answer:

1. **"What should I be called?"** — Assistant name (e.g., "Friday", "Jarvis")
2. **"What should I call you?"** — User's name (e.g., "Boss", "Chief")
3. **"Auto-approve voice tools?"** — Recommend yes. No permission prompts during voice. (yes/no)

Save config:
```bash
python3 -c "
import json
from pathlib import Path
config = {
    'assistant_name': '<answer>',
    'user_name': '<answer>',
    'hooks': {'auto_approve': True}
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
