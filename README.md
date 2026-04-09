<p align="center">
  <h1 align="center">VOCLI</h1>
  <p align="center">
    <strong>Local voice layer for AI coding tools</strong>
  </p>
  <p align="center">
    Talk to Claude Code with your voice. 100% local, 100% private.
  </p>
  <p align="center">
    <a href="#-quick-start"><img src="https://img.shields.io/badge/Get_Started-blue?style=for-the-badge" alt="Get Started"></a>
    <a href="#-remote-mode"><img src="https://img.shields.io/badge/Remote_Mode-purple?style=for-the-badge" alt="Remote Mode"></a>
    <a href="https://github.com/shubham-lohar/vocli/blob/main/LICENSE"><img src="https://img.shields.io/badge/License-MIT-green?style=for-the-badge" alt="MIT License"></a>
  </p>
</p>

---

## What is VOCLI?

> You speak. Claude listens. Claude responds. You hear it.

VOCLI adds a **voice layer** to Claude Code. Everything runs locally on your machine — no audio is sent to the cloud, ever.

```
You speak --> Mic --> faster-whisper (STT) --> Text to Claude
Claude responds --> Piper TTS --> Audio plays through speakers
```

### Highlights

- **Privacy-first** — all audio processing stays on your machine
- **Works offline** — after initial model download, no internet needed
- **Personalized** — set your name and the assistant's name
- **Smart performance** — auto-detects Apple Silicon vs Intel for optimal speed
- **Remote-ready** — use voice even when Claude Code runs on a remote VM

---

## Quick Start

### Recommended: Claude Code Plugin Marketplace

The easiest way to install VOCLI:

```bash
# Step 1: Add the marketplace
/plugin marketplace add shubham-lohar/vocli

# Step 2: Install the plugin
/plugin install vocli@vocli

# Step 3: Run the setup wizard
/vocli:install

# Step 4: Start talking!
/vocli:talk
```

> The install wizard walks you through everything: dependencies, models, and configuration.

### Alternative: Manual Install via UV

```bash
# Install UV package manager (if needed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Add VOCLI as an MCP server
claude mcp add --scope user vocli -- uvx --refresh vocli

# Restart Claude Code, then run:
/vocli:install
```

---

## Local Install

For running Claude Code and VOCLI on the **same machine** (Mac or Linux with mic/speakers).

The `/vocli:install` wizard handles everything:

| Step | What happens |
|------|-------------|
| 1 | Checks Python 3.10+ and ffmpeg |
| 2 | Installs `faster-whisper` and `piper-tts` |
| 3 | Downloads voice model (~100MB) and Whisper model (~500MB) |
| 4 | Detects your CPU architecture (Apple Silicon / Intel / ARM) |
| 5 | Lets you choose model size (`tiny` for speed, `small` for accuracy) |
| 6 | Asks for your name, assistant name, and preferences |

**Performance note:** On Apple Silicon (M1/M2/M3), VOCLI automatically uses `float16` for faster speech recognition. On Intel, it uses `int8`.

---

## Remote Mode

For running Claude Code on a **remote VM** while keeping voice on your local machine.

### Why?

Remote VMs have no microphone or speakers. VOCLI's remote mode runs the audio servers on your local machine and connects them to Claude Code on the VM via the network.

### How it works

```
Your Mac/Linux (local)              Remote VM
+------------------+               +------------------+
|  STT Server      | <-- network   |  Claude Code     |
|  (port 2022)     | ----------->  |  + VOCLI Plugin  |
|                  |               |                  |
|  TTS Server      | <-- network   |  /vocli:talk     |
|  (port 8880)     | ----------->  |  just works!     |
|                  |               |                  |
|  Mic + Speakers  |               |  No audio deps   |
+------------------+               +------------------+
```

### Setup

**Step 1 — On your local machine** (with mic/speakers):

```bash
curl -sL https://raw.githubusercontent.com/shubham-lohar/vocli/main/scripts/serve.sh | bash
```

This installs dependencies, downloads models, and starts the STT/TTS servers. It prints the URLs when ready.

**Step 2 — On the remote VM** (where Claude Code runs):

```bash
# Install the plugin (if not already)
/plugin marketplace add shubham-lohar/vocli
/plugin install vocli@vocli

# Run remote setup
/vocli:remote-install
```

Paste the URLs from Step 1 when prompted. Done!

> **Tip:** If your VM can't reach your local machine directly, use SSH port forwarding:
> ```bash
> ssh -R 2022:localhost:2022 -R 8880:localhost:8880 your-vm
> ```
> Then use `http://localhost:2022` and `http://localhost:8880` as the URLs.

---

## Commands

| Command | Description |
|---------|-------------|
| `/vocli:install` | Install dependencies, download models, configure (local mode) |
| `/vocli:remote-install` | Set up remote mode with external STT/TTS servers |
| `/vocli:config` | Change assistant name, your name, preferences |
| `/vocli:talk` | Start a voice conversation |

---

## MCP Tools

VOCLI runs as an MCP server with three tools:

| Tool | What it does |
|------|-------------|
| `talk` | Speak a message and optionally listen for a reply. Auto-starts servers if needed. |
| `status` | Check health of STT/TTS servers and show current config. |
| `service` | Start, stop, or restart STT/TTS servers. |

---

## Architecture

```
+-----------------------------------+
|        VOCLI MCP Server           |
|     (FastMCP, stdio transport)    |
|                                   |
|   Tools: talk, status, service    |
+--------+--------------+----------+
         |              |
   +-----v------+ +-----v------+
   | STT Server | | TTS Server |
   | port 2022  | | port 8880  |
   | faster-    | | Piper TTS  |
   | whisper    | |            |
   +------------+ +------------+
         |              |
     [local or remote servers]
```

**Local mode:** Servers run on the same machine as Claude Code.
**Remote mode:** Servers run on your local machine; Claude Code connects over the network.

---

## Requirements

| Requirement | Details |
|-------------|---------|
| Python | 3.10 or higher |
| OS | macOS (Apple Silicon or Intel) or Linux |
| ffmpeg | `brew install ffmpeg` (macOS) or `sudo apt install ffmpeg` (Linux) |
| Disk space | ~700MB for models |
| Audio | Microphone + speakers (local mode only) |

---

## License

MIT
