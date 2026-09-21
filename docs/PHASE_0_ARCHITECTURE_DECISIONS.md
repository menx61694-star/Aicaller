# Phase 0 — Final Architecture Decisions

## Product boundary

Aicaller is an inbound-call screening and human-takeover system. The core system is provider-agnostic, but Phase 1 will use one selected telephony adapter behind an interface.

## Initial technology choices

| Area | Phase 0 choice | Boundary / fallback |
|---|---|---|
| Telephony | Exotel AgentStream candidate for India-first pilot | Plivo/Twilio adapter retained |
| Call control | Application-owned state machine behind TelephonyAdapter | Provider-specific adapter |
| Media/agent framework | LiveKit Agents | Pipecat remains fallback |
| Realtime AI | OpenAI Realtime adapter | Cascaded STT→LLM→TTS remains supported |
| Backend API | Python + FastAPI | Framework-specific code behind services |
| Async/background work | Python worker + durable job queue | Post-call work never blocks call termination |
| Database | PostgreSQL | Relational source of truth for call/session metadata |
| Audio/recordings | S3-compatible object storage | Provider storage only as temporary ingress where unavoidable |
| Cache/ephemeral state | Redis | DB remains authoritative |
| Authentication | Short-lived access tokens with server-side authorization; Android identity provider may be Firebase Auth | Auth provider must not receive call audio |
| Android notifications | Firebase Cloud Messaging | Telegram/SMS optional adapters |
| Observability | Structured JSON logs + metrics + traces + error tracking | Every event carries call_id |
| Configuration | Versioned environment/config object | No secrets in repository |
| Deployment | Containerized backend/agent services | Cloud or self-hosted deployment |
| API transport | HTTPS REST for control plane; WSS/WebRTC for realtime media | Provider adapter owns transport details |

## Runtime boundaries

### Control plane
FastAPI handles authentication, user settings, call history, routing policy, dashboard APIs and signed provider webhooks.

### Realtime plane
The media/agent service owns audio sessions, VAD/turn detection, AI generation, barge-in and media lifecycle. It must not directly mutate arbitrary application data; tool calls go through an authorization layer.

### Data plane
PostgreSQL stores durable metadata. Object storage stores recordings/audio artifacts. Redis stores ephemeral locks/session state and rate-limit data.

### Worker plane
Background workers perform transcript finalization, summaries, action extraction, notifications, retention jobs and retries.

## Security boundaries

- Provider credentials and AI API keys exist only server-side.
- Webhooks require provider signature verification where supported.
- WSS/HTTPS is mandatory for production.
- Call IDs are correlation identifiers, not authorization credentials.
- Contact data is resolved locally and only minimum required context is exposed to the model.
- OTPs, PINs, passwords, card numbers and other secrets are not collected or repeated by default.
- Tool execution requires explicit server-side authorization.
- Recording and transcript URLs are authenticated and short-lived.
- Deletion/retention policies are enforced by backend jobs.
- Caller speech is untrusted input and cannot override system policy.

## Cost controls

Every call receives a maximum duration, model/provider budget, recording policy and usage counters. Daily/monthly aggregate budgets are enforced. The system must fail safely when a budget is exhausted.

## Provider-selection gate

The Phase 0 default for the India-first pilot is Exotel AgentStream because current Exotel documentation describes bidirectional WSS voice-bot streaming and programmable call control. This is an engineering selection, not a claim that account approval, number availability, pricing or legal compliance is guaranteed.

Before production, the Phase 1 real-call gate must verify the exact Exotel account, number, KYC, media behavior, transfer/bridge behavior, recording behavior and failure semantics.

LiveKit Agents is the primary realtime framework because its current documentation supports Python/Node.js agents, realtime media, interruption handling, STT/LLM/TTS pipelines, realtime speech-to-speech models and telephony/SIP.

OpenAI Realtime is the initial realtime-model adapter. The application will still preserve explicit policy, state, routing and tool authorization outside the model.

## Phase 0 implementation rule

No production provider-specific code is written until the selected adapter's Phase 1 test matrix is executed. Architecture code may be scaffolded behind interfaces, but unresolved provider assumptions remain explicit.
