# Aicaller — Call State Machine

This is a Phase 0 design artifact. It is intentionally provider-neutral.

## States

1. INCOMING
2. RINGING
3. AI_ANSWERING
4. AI_CALL
5. TAKEOVER_REQUESTED
6. HUMAN_CALL
7. FAILURE
8. CALL_ENDED
9. POST_PROCESSING

## Transition table

| Current | Event | Next | Required action |
|---|---|---|---|
| INCOMING | call accepted by telephony webhook | RINGING | persist call ID and caller metadata |
| RINGING | human answers | HUMAN_CALL | bind human call session |
| RINGING | timeout | AI_ANSWERING | request AI answer/media session |
| RINGING | provider failure | FAILURE | record provider error and fallback |
| AI_ANSWERING | media established | AI_CALL | start AI session |
| AI_ANSWERING | media/answer failure | FAILURE | execute fallback |
| AI_CALL | caller hangs up | CALL_ENDED | stop AI/media resources |
| AI_CALL | takeover requested | TAKEOVER_REQUESTED | freeze routing transition and start bridge |
| AI_CALL | provider/network failure | FAILURE | execute configured fallback |
| TAKEOVER_REQUESTED | human bridge succeeds | HUMAN_CALL | stop AI speech and connect human |
| TAKEOVER_REQUESTED | timeout/failure | AI_CALL or FAILURE | apply configured policy |
| HUMAN_CALL | caller hangs up | CALL_ENDED | close human bridge |
| HUMAN_CALL | human ends call | CALL_ENDED | close call |
| FAILURE | safe fallback succeeds | CALL_ENDED | record failure/fallback outcome |
| FAILURE | fallback unavailable | CALL_ENDED | safe termination |
| CALL_ENDED | post-call processing starts | POST_PROCESSING | finalize transcript/recording |
| POST_PROCESSING | processing complete | terminal | persist summary/actions |

## Required transition invariants

- Every transition must be idempotent.
- A stale provider event must not move a call backward into an invalid state.
- A call must have one authoritative call ID.
- Every state change must be timestamped.
- Every failure must record a machine-readable reason.
- A human takeover must never leave AI audio playing after the bridge becomes active.
- Post-call processing must not block call termination.

## Timeout matrix

Initial engineering budgets are documented in docs/TIMEOUT_FAILURE_MATRIX.md:
- webhook acknowledgement: 2s
- human ringing: 5–8s configurable
- AI answer setup: 3s
- media connection: 2s
- STT response: 1.5s target
- LLM first token/audio-ready: 1s target
- TTS first audio: 0.8s target
- end-to-end first audio: 2s target
- barge-in reaction: 250ms target
- takeover bridge: 3s target
- reconnect: bounded retry/backoff
- post-call processing: 30s target

These are engineering targets, not provider guarantees. Phase 1 real-call measurements may change them.

## Transition safety rules

1. Provider events are accepted only after signature/session validation.
2. Each transition uses an atomic compare-and-set or equivalent concurrency guard.
3. Duplicate events are idempotent.
4. Events carrying an older sequence/timestamp cannot move state backward.
5. Only the authoritative call session may mutate call state.
6. CALL_ENDED is terminal for call-control purposes; post-call processing is asynchronous.
7. AI output is cancelled and queued audio flushed before HUMAN_CALL is activated.
8. Every transition emits a structured event containing call_id, old_state, new_state, event_type, timestamp and failure_reason when applicable.

## Phase 0 status

**COMPLETE — state model frozen for Phase 1.**
