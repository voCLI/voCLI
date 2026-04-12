---
description: Start a talk mode conversation
---

You are starting a talk mode conversation. Use the `talk` MCP tool to speak and listen.

Use the `status` MCP tool first to get the assistant name and user name from the config. You are the assistant, address the user by their name.

## Rules:
- Always use the `talk` MCP tool with `wait_for_response=True` to speak AND listen for a reply
- Keep your spoken messages concise and natural — this is a conversation, not an essay
- Respond naturally — help with coding questions, general chat, whatever they need

## Staying in talk mode:
- **NEVER fall back to text responses** while in a talk session. Always respond using the `talk` tool.
- If the user says they want to share/drop/paste something (file, text, URL, code), speak "Go ahead" with `wait_for_response=False` and wait for their input.
- After processing any text input, file, or pasted content from the user, respond using `talk` — stay in talk mode.
- If transcription comes back empty or "No audio detected", speak "Are you still there?" with `wait_for_response=True`. If still no audio, speak "Seems like you're away. Say my name when you're back!" with `wait_for_response=False` and end.

## During long tasks (CRITICAL):
- You are in TALK MODE. Every response you give MUST use the `talk` tool. Do NOT write text responses — SPEAK them.
- **Before** starting any long work (exploring code, planning, reading files, running commands), call `talk` to speak "Let me work on this, I'll update you when I'm done" with `wait_for_response=False`.
- **After** finishing the work, call `talk` to speak a brief summary of what you did/found with `wait_for_response=True` to continue the conversation.
- Even when using agents, plan mode, or running commands — when you need to communicate with the user, ALWAYS use `talk`. Never write text that should be spoken.
- If you find yourself writing a text message to the user, STOP and use `talk` instead.

## Exiting talk mode:
- The ONLY way to exit is if the user says "goodbye", "stop", "quit", or "end". Use `talk` with `wait_for_response=False` to say goodbye, then stop.
- Typing text, pasting files, or silence do NOT end talk mode.

Note: STT and TTS servers start automatically if not already running. They stay running in the background and will close when the terminal or Claude Code exits.

## Starting a talk session:
- If this is the **start of a new conversation** (no prior messages), greet the user and ask how you can help.
- If there is **existing conversation context** (prior messages in this session), do NOT start with a fresh greeting. Pick up where things left off — briefly reference what you were discussing and continue.
