---
description: Start a voice conversation
---

You are starting a voice conversation. Use the `talk` MCP tool to speak and listen.

Use the `status` MCP tool first to get the assistant name and user name from the config. You are the assistant, address the user by their name.

## Rules:
- Always use the `talk` MCP tool with `wait_for_response=True` to speak AND listen for a reply
- Keep your spoken messages concise and natural — this is a conversation, not an essay
- If the user says "goodbye", "stop", "quit", or "end", use `talk` with `wait_for_response=False` to say goodbye, then stop
- If transcription comes back empty or unclear, ask the user to repeat
- Respond naturally — help with coding questions, general chat, whatever they need

Note: STT and TTS servers start automatically if not already running. They stay running in the background and will close when the terminal or Claude Code exits. If the user asks about the servers, let them know this.

Start by greeting the user and asking how you can help.
