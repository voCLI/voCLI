---
description: Configure VOCLI preferences
---

First, check if VOCLI is already configured:
```bash
cat ~/.vocli/config.json 2>/dev/null || echo "NOT_CONFIGURED"
```

**If already configured:** Show current settings and ask what the user wants to change. Only update the specific setting they request — don't re-run the full setup.

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

Confirm setup and suggest `/vocli:talk`. Servers start automatically — no manual step needed.
