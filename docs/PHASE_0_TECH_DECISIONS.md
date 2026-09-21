# Phase 0 — Technology & Compliance Decision Record

## Current verified baseline

- Repository: Aicaller
- Default branch: main
- Repository was empty before the Phase 0 documentation baseline was added.
- No application framework or provider is currently present in the repository.

## Decision rule

Provider/framework choices must not be selected by popularity alone. Each candidate must be evaluated for:
1. India telephony availability and regulatory fit
2. Incoming-call/webhook support
3. Bidirectional real-time media streaming
4. Human bridge/transfer support
5. WebSocket/WebRTC/SIP compatibility
6. Audio codec compatibility
7. STT/LLM/TTS streaming compatibility
8. Latency characteristics
9. Reliability and failure recovery
10. Pricing and expected per-minute cost
11. Data/security controls
12. Recording/transcription support
13. Documentation and SDK maturity
14. Android/dashboard integration
15. Vendor lock-in and migration path

## Initial architecture direction

The project will use a provider-agnostic boundary:

Telephony Adapter
-> Call State Machine
-> Media Adapter
-> AI Pipeline
-> Application/Policy Layer
-> Data/Notification Layer

This prevents the application core from being tightly coupled to one telephony or AI vendor.

## India telecom/compliance baseline

This project is initially an **incoming-call screening** product, not an outbound telemarketing system. Outbound commercial calling/SMS must be treated as a separate compliance scope.

TRAI's current published material states that unsolicited commercial communication includes voice calls and that commercial communication is subject to consent/preference and sender requirements. The consolidated TCCCPR material was updated on 21 May 2026. Any future outbound commercial-call feature therefore requires a separate compliance review before implementation.

TRAI also publishes current consent-management guidance for commercial communications.

The implementation must not assume that an AI disclosure, recording notice, or any other single measure by itself establishes complete legal compliance. Applicable telecom, privacy, recording/consent, provider, and contractual requirements must be verified before production deployment.

## Data protection baseline

Voice recordings, transcripts, caller numbers, contact information and call metadata are treated as sensitive application data for architecture purposes.

The project will therefore include:
- explicit retention configuration
- access control
- encrypted transport
- protected storage
- auditability
- deletion capability
- minimum-data principle
- provider data-flow review

India's Digital Personal Data Protection Rules, 2025 are published by MeitY, with an enforcement timeline published separately. Exact production obligations will be mapped during the security/privacy phase rather than guessed at this stage.

## Evaluation documents

- Provider/framework evaluation: `docs/PROVIDER_EVALUATION.md`
- Timeout/failure matrix: `docs/TIMEOUT_FAILURE_MATRIX.md`

These documents record candidate evaluation and provisional engineering budgets. They do not mark provider selection or production readiness complete.

## Phase 0 status

### Completed
- Repository baseline verification
- Empty-repository verification
- Architecture boundary definition
- Exhaustive roadmap checklist created
- Compliance items added to architecture scope

### Still required before Phase 0 completion
- Evaluate telephony providers — documented; final provider remains open pending real-call India validation
- Evaluate media frameworks — documented; LiveKit Agents is the primary candidate and Pipecat remains fallback
- Evaluate STT candidates — architecture supports modular providers; final production STT remains open
- Evaluate LLM candidates — realtime-model path evaluated; final production model remains open
- Evaluate TTS candidates — modular interface defined; final production TTS remains open
- Evaluate backend/runtime options
- Evaluate database/storage options
- Evaluate authentication options
- Evaluate notification options
- Define complete call-state transition table
- Define timeout/failure matrix
- Define test strategy
- Perform final Phase 0 audit

**No Phase 1 implementation should be considered complete until these decisions are documented and verified.**
