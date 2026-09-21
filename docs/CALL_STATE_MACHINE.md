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

Exact values will be selected after provider testing. No arbitrary fixed production values are accepted yet.

Required timeout entries:
- webhook acknowledgement
- human ringing
- AI answer
- media connection
- STT response
- LLM first token
- TTS first audio
- takeover bridge
- reconnect
- post-call processing

## Phase 0 status

Design drafted. Implementation is not yet claimed complete.
