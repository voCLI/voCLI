# voCLI — Talk Mode Rules

When the user starts a voice conversation using `/vocli:talk` or the `talk` MCP tool, you are in **talk mode**. These rules apply for the entire session:

## Talk mode persistence
- Once talk mode starts, ALWAYS respond using the `talk` MCP tool. Never fall back to text responses.
- If talk mode drops for any reason (plan mode, agents, long tasks, errors), **resume it immediately** by calling the `talk` tool again.
- Before starting long work, speak "I'll work on this and update you" with `wait_for_response=False`. After finishing, speak the result with `wait_for_response=True`.
- If the user types text or pastes files during talk mode, process it and respond using `talk` — stay in talk mode.

## Exiting talk mode
- The ONLY way to exit talk mode is if the user explicitly says "goodbye", "stop", "quit", or "end".
- Nothing else ends talk mode — not text input, file drops, plan mode, or silence.

## Resuming talk mode
- If the user says "let's talk", "talk mode", "talk to me", or anything similar, call the `talk` tool immediately.
- If there is prior conversation context, pick up where you left off — do not start with a fresh greeting.

## Before long tasks
- If you are about to enter plan mode, run agents, or do any complex multi-step work that might interrupt talking, speak "This might take a bit. If talk mode drops, just run /vocli:talk to resume" with `wait_for_response=False` before starting.
