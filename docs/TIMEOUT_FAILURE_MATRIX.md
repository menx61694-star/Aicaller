# Phase 0 — Timeout & Failure Matrix

These values are initial engineering budgets, not provider guarantees. They must be measured and adjusted during real-call testing.

| Area | Initial budget | On timeout/failure | Telemetry |
|---|---:|---|---|
| Webhook acknowledgement | 2 s | acknowledge first; process asynchronously | webhook_latency_ms |
| Human ringing window | 5–8 s configurable | transition to AI answering | ring_elapsed_ms |
| AI answer setup | 3 s | retry once if safe, then fallback/terminate | ai_answer_setup_ms |
| Media/WebSocket connection | 2 s | retry/reconnect; fallback | media_connect_ms |
| STT first partial/final | 1.5 s target | use partials, retry/fallback | stt_latency_ms |
| LLM first token/audio-ready | 1.0 s target | fallback model/short response | llm_ttft_ms |
| TTS first audio | 0.8 s target | fallback voice/model | tts_first_audio_ms |
| End-to-end response start | 2.0 s target | shorten response/fallback | e2e_first_audio_ms |
| Barge-in reaction | 250 ms target | immediately cancel/flush AI audio | barge_in_ms |
| Takeover bridge | 3 s target | retry once, then safe termination | takeover_ms |
| WebSocket reconnect | 2 attempts / bounded backoff | enter FAILURE or fallback | reconnect_count |
| Post-call processing | 30 s target | persist raw event and retry asynchronously | postprocess_ms |

## Failure transition rules

### Telephony
- Provider webhook failure: retry only where provider semantics permit; keep handlers idempotent.
- Provider call-control failure: do not repeatedly issue conflicting call commands; move to FAILURE with a machine-readable reason.
- Call disconnect: mark CALL_ENDED exactly once.

### Media
- WebSocket disconnect: attempt bounded reconnect if the provider supports it.
- Reconnect failure: stop AI output and use provider-safe fallback or terminate.
- Slow/degraded stream: record degradation and avoid unbounded buffering.

### AI
- STT failure: retry with bounded attempts; if unavailable, route to human or safe termination.
- LLM failure: use a deterministic fallback phrase or human escalation; never fabricate an answer.
- TTS failure: retry or use a fallback voice; do not leave stale audio in the playback queue.
- Model timeout: cancel the turn and restore a valid call state.

### Human takeover
1. Set TAKEOVER_REQUESTED.
2. Establish human leg/bridge.
3. Confirm bridge active.
4. Stop AI generation.
5. Flush pending AI audio.
6. Set HUMAN_CALL.
7. If bridge fails, restore AI_CALL only if no human leg is active; otherwise terminate safely.

### Security failures
- Authentication failure: reject the session.
- Invalid provider signature: reject webhook/media session.
- Suspicious tool request: block action and log policy event.
- Prompt-injection attempt: treat caller content as untrusted data; never allow it to override system policy.

## Required implementation rule

Timeouts are configuration values, not scattered constants. Store them in one versioned configuration object and emit metrics for every timeout/retry/fallback.
