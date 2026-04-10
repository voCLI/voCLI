# voCLI — Voice Mode Rules

When the user starts a voice conversation using `/vocli:talk` or the `talk` MCP tool, you are in **voice mode**. These rules apply for the entire session:

## Voice mode persistence
- Once voice mode starts, ALWAYS respond using the `talk` MCP tool. Never fall back to text responses.
- If voice mode drops for any reason (plan mode, agents, long tasks, errors), **resume it immediately** by calling the `talk` tool again.
- Before starting long work, speak "I'll work on this and update you" with `wait_for_response=False`. After finishing, speak the result with `wait_for_response=True`.
- If the user types text or pastes files during voice mode, process it and respond using `talk` — stay in voice mode.

## Exiting voice mode
- The ONLY way to exit voice mode is if the user explicitly says "goodbye", "stop", "quit", or "end".
- Nothing else ends voice mode — not text input, file drops, plan mode, or silence.

## Resuming voice mode
- If the user says "let's talk", "voice mode", "talk to me", or anything similar, call the `talk` tool immediately.
- If there is prior conversation context, pick up where you left off — do not start with a fresh greeting.
