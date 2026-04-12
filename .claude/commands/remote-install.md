---
description: Set up VOCLI with remote STT/TTS servers
---

You are setting up VOCLI in **remote mode** — the STT and TTS servers run on the user's local machine (with mic/speakers), while Claude Code runs here on a remote VM. The VOCLI MCP server runs on this VM via `uvx vocli serve`, which requires `uv` to be installed here.

## Step 1: Check `uv` package manager on this VM
Run `uv --version`. If `uv` is missing or the command fails:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```
Then re-check with `uv --version`. If it still fails, tell the user to source their shell profile (e.g. `source ~/.bashrc`) and retry. **Remember whether `uv` was freshly installed here — you will need to tell the user to restart Claude Code at the end if so, otherwise the MCP server won't pick it up.**

## Step 2: Tell the user to start servers on their local machine

Show them this command to run on their **local machine** (Mac or Linux with audio):

```
curl -sL https://raw.githubusercontent.com/voCLI/voCLI/main/scripts/serve.sh | bash
```

Or if they have the repo cloned locally:
```
./scripts/serve.sh
```

Tell them: "Run this on your local machine. Once it's running, it will print STT and TTS URLs. Paste those URLs here."

## Step 3: Get the URLs

Wait for the user to provide the two URLs. They should look like:
- STT: `http://<ip>:2022`
- TTS: `http://<ip>:8880`

## Step 4: Validate connectivity

Test both URLs from this machine:
```bash
curl -s <stt_url>/health && echo " STT OK" || echo " STT FAILED"
curl -s <tts_url>/health && echo " TTS OK" || echo " TTS FAILED"
```

If either fails, help troubleshoot (firewall, SSH tunnel, wrong IP).

## Step 5: Configure

Ask the user:
1. "What should I be called?" (assistant name)
2. "What should I call you?" (user name)
3. "Auto-approve voice tools?" (yes/no, recommend yes)
4. "Enable task completion chime?" (yes/no)

## Step 6: Save config

Save everything to `~/.vocli/config.json`:
```bash
python3 -c "
import json
from pathlib import Path
config = {
    'server_mode': 'remote',
    'stt_url': '<stt_url>',
    'tts_url': '<tts_url>',
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

If auto-approve enabled, add to `~/.claude/settings.json` permissions.allow:
- `mcp__plugin_vocli_vocli__talk`
- `mcp__plugin_vocli_vocli__status`

## IMPORTANT: When done, say EXACTLY ONE of these and NOTHING else:

**If `uv` was freshly installed in Step 1**, say:
"Remote setup complete! I just installed `uv` on this VM, so you'll need to **restart Claude Code** once for the MCP server to pick it up. Then type **let's talk** or run `/vocli:talk` to start a voice conversation! You can change the voice anytime — run `/vocli:config` and ask to change voice. There are 54 voices to choose from."

**Otherwise** (uv was already installed), say:
"Remote setup complete! Just type **let's talk** or run `/vocli:talk` to start a voice conversation! You can change the voice anytime — run `/vocli:config` and ask to change voice. There are 54 voices to choose from."

Do NOT summarize settings, do NOT list STT/TTS details, do NOT say "you're all set". Just one of the messages above.
