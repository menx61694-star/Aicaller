# Aicaller — Architecture Baseline

## Core principle

Aicaller is not just a voice chatbot. It is a telephony system with a deterministic call-state machine, real-time media pipeline, AI layer, and human fallback.

## High-level flow

Caller
-> Telephony Gateway
-> Call State Machine
-> Media Session
-> Audio Processing
-> VAD
-> Streaming STT
-> Conversation Manager
-> Policy + Intent + Context
-> Streaming LLM
-> Response Validation
-> Streaming TTS
-> Media Session
-> Telephony
-> Caller

Parallel systems:

- Call-state persistence
- Live transcript
- Recording/object storage
- Caller/contact resolution
- Notifications
- Calendar/CRM actions
- Observability
- Security and audit logging

## Mandatory architectural boundaries

### Telephony boundary
Responsible for call lifecycle, routing, call identifiers, provider events and bridge/transfer operations.

### Media boundary
Responsible for real-time audio transport, buffering, audio processing, VAD and interruption handling.

### AI boundary
Responsible for STT, conversation state, intent, policy, LLM and TTS.

### Application boundary
Responsible for caller identity, user settings, routing policies, memory, notifications and external actions.

### Data boundary
Responsible for call metadata, transcripts, recordings, retention and access control.

## Call-state machine

Required states:

INCOMING
RINGING
AI_ANSWERING
AI_CALL
TAKEOVER_REQUESTED
HUMAN_CALL
FAILURE
CALL_ENDED
POST_PROCESSING

Every state must define valid transitions, triggers, timeout behavior and failure behavior before implementation is considered complete.

## Non-functional requirements

- Streaming-first architecture
- Explicit timeout handling
- Graceful degradation
- Secure server-side secrets
- Correlated structured logs
- Measurable latency
- Configurable routing thresholds
- Explicit data retention
- Human fallback
- No silent feature omission

## Technology decision status

Technology choices are intentionally not hard-coded in this baseline until Phase 0 architecture review is completed. Provider/model/framework choices must be evaluated against latency, availability, India telephony support, cost, security, streaming support and takeover/bridge capabilities.
