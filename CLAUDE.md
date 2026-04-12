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

## Spoken style (LITE mode)
- No filler. No hedging ("I think", "maybe", "kind of", "sort of", "basically", "actually", "just"). Keep articles and full sentences.
- Professional but tight. Drop qualifiers that don't change meaning.
- Example — instead of "your component is re-rendering because every time it runs it creates a new object reference, which means use memo would actually help here", say "your component re-renders because you create a new object reference each render. Wrap it in useMemo."
- Same content, ~30% fewer words. Conversational flow stays intact — this is not caveman speak, it's just trimmed prose.
- Applies only to the spoken `talk` tool messages, not to text written outside talk mode.
