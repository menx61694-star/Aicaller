# Aicaller — Test Strategy

## Test layers

### Unit
Test state transitions, routing precedence, timeout handling, policy guards, confidence thresholds, authorization, data retention rules and deterministic utilities.

### Integration
Test telephony adapter events, webhook verification, media adapter, realtime model adapter, database transactions, object storage, notifications and calendar/CRM adapters.

### End-to-end
Run real or provider-sandbox calls covering human answer before AI timeout, AI answer after timeout, normal AI conversation, caller interruption, repeated interruption, human takeover, takeover failure, caller hangup, human hangup, IVR, DTMF, voicemail, spam/urgency routing, recording/transcript lifecycle and post-call processing.

### Resilience
Inject STT/model timeout, LLM failure, TTS failure, WebSocket disconnect, packet loss/degraded audio, provider webhook retry, duplicate events, out-of-order events, database transient failure, object-storage failure and notification failure.

### Security
Verify invalid webhook signatures are rejected, expired tokens are rejected, unauthorized call/recording access is rejected, tool authorization is enforced, secrets are absent from client/logs, prompt injection cannot change system policy, sensitive-data guardrails block credential collection, and recording/transcript deletion works.

### Performance
Measure webhook acknowledgement, media connection, STT latency, LLM TTFT, TTS first audio, end-to-end first audio, barge-in reaction, takeover bridge, CPU/memory and per-call cost.

## Release gates

A phase cannot be marked complete when a required test is missing, a critical path is unverified, a known failure has no defined fallback, security controls are untested, or a provider-specific assumption has not been validated.

## Test artifacts

Every phase should leave automated test results, manual evidence for real-call behavior where required, known limitations and regression cases for every production bug.
