<p align="center">
  <h1 align="center">voCLI</h1><strong>voice + CLI</strong>
  <p align="center">
    Talk to Claude Code with your voice.
  </p>
  <p align="center">
    <a href="#-quick-start"><img src="https://img.shields.io/badge/Get_Started-blue?style=for-the-badge" alt="Get Started"></a>
    <a href="#-remote-mode"><img src="https://img.shields.io/badge/Remote_Mode-purple?style=for-the-badge" alt="Remote Mode"></a>
    <a href="https://github.com/shubham-lohar/vocli/blob/main/LICENSE"><img src="https://img.shields.io/badge/License-MIT-green?style=for-the-badge" alt="MIT License"></a>
  </p>
</p>

---

## What is voCLI?

> You speak. Claude listens. Claude responds. You hear it.

voCLI adds a **voice layer** to Claude Code. Everything runs locally on your machine — no audio is sent to the cloud, ever.

```
You speak --> Mic --> faster-whisper (STT) --> Text to Claude
Claude responds --> Kokoro TTS --> Audio plays through speakers
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

The easiest way to install voCLI:

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

# Add voCLI as an MCP server
claude mcp add --scope user vocli -- uvx --refresh vocli

# Restart Claude Code, then run:
/vocli:install
```

---

## Local Install

For running Claude Code and voCLI on the **same machine** (Mac or Linux with mic/speakers).

The `/vocli:install` wizard handles everything:

| Step | What happens |
|------|-------------|
| 1 | Checks Python 3.10+ and ffmpeg |
| 2 | Installs `faster-whisper` and `kokoro-onnx` |
| 3 | Downloads Kokoro voice model (~325MB) and Whisper model (~500MB) |
| 4 | Detects your CPU architecture (Apple Silicon / Intel / ARM) |
| 5 | Lets you choose model size (`tiny` for speed, `small` for accuracy) |
| 6 | Asks for your name, assistant name, and preferences |

**Performance note:** On Apple Silicon, voCLI automatically uses `float16` for faster speech recognition. On Intel, it uses `int8`.

---

## Remote Install

For running Claude Code on a **remote VM** while keeping voice on your local machine.

### Why?

Remote VMs have no microphone or speakers. voCLI's remote mode runs the audio servers on your local machine and connects them to Claude Code on the VM via the network.

### How it works

```
Your Mac/Linux (local)              Remote VM
+------------------+               +------------------+
|  STT Server      | <-- network   |  Claude Code     |
|  (port 2022)     | ----------->  |  + voCLI Plugin  |
|                  |               |                  |
|  TTS Server      | <-- network   |  /vocli:talk     |
|  (port 8880)     | ----------->  |  just works!     |
|                  |               |                  |
|  Mic + Speakers  |               |  No audio deps   |
+------------------+               +------------------+
```

### Setup

Install the plugin on your remote VM, then run the remote setup wizard:

The `/vocli:remote-install` wizard handles everything:

From starting the servers on your local machine, entering the URLs, and configuring your preferences.

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

voCLI runs as an MCP server with three tools:

| Tool | What it does |
|------|-------------|
| `talk` | Speak a message and optionally listen for a reply. Auto-starts servers if needed. |
| `status` | Check health of STT/TTS servers and show current config. |
| `service` | Start, stop, or restart STT/TTS servers. |

---

## Requirements

| Requirement | Details |
|-------------|---------|
| Python | 3.10 or higher |
| OS | macOS (Apple Silicon or Intel) or Linux |
| Disk space | ~900MB for models |
| Audio | Microphone + speakers |

---

## License

MIT
