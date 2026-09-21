# Phase 0 — Final Audit

## Repository baseline

- Repository identity and default branch verified.
- Repository was empty before Phase 0 documentation.
- No existing application source, build system, backend/frontend, integrations, database, auth, permissions, CI/CD or tests were present to preserve.
- Baseline documentation was committed before application implementation.

## Architecture

- Provider-agnostic telephony boundary defined.
- Call state machine defined.
- Media, AI, application and data boundaries defined.
- Human takeover and failure paths defined.
- Recording, transcript, retention and security boundaries defined.
- Cost and observability requirements defined.

## Technology decisions

- Telephony: Exotel AgentStream initial India-first adapter; Plivo/Twilio retained as alternatives.
- Media/agent: LiveKit Agents primary; Pipecat fallback.
- Realtime AI: OpenAI Realtime primary adapter; modular cascaded STT/LLM/TTS fallback.
- Backend: Python/FastAPI.
- Database: PostgreSQL.
- Ephemeral state: Redis.
- Object storage: S3-compatible.
- Authentication: token-based server authorization with Android identity provider.
- Notifications: FCM primary; optional adapters later.
- Deployment: containers.
- Observability: structured logs, metrics, traces and error tracking.

## State machine

Required states:
INCOMING → RINGING → AI_ANSWERING → AI_CALL → TAKEOVER_REQUESTED → HUMAN_CALL → CALL_ENDED → POST_PROCESSING, with FAILURE transitions.

Invariants:
- idempotent transitions
- stale-event protection
- authoritative call ID
- timestamped transitions
- machine-readable failure reason
- AI audio stopped before/when human bridge becomes active
- post-call processing cannot block termination

## Timeout/failure policy

Initial engineering budgets are documented in docs/TIMEOUT_FAILURE_MATRIX.md. They are targets, not provider guarantees, and must be tuned after Phase 1 real-call measurements.

## Testing

docs/TEST_STRATEGY.md defines unit, integration, end-to-end, resilience, security and performance gates.

## Explicitly deferred validations

These require an actual provider account/test environment:
- exact Exotel number availability
- account/KYC approval
- exact transfer/bridge behavior for the chosen account
- provider-specific recording behavior
- production pricing/limits
- real network/media latency
- real-call codec/interruption behavior

## Audit result

**PHASE 0 COMPLETE — ARCHITECTURE FROZEN FOR PHASE 1**

Completion means architecture and engineering decisions are documented and internally consistent. It does not mean external provider/account validation has already been performed.
