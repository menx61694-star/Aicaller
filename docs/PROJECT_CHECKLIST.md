# Aicaller — Exhaustive Project Checklist

## Rule

**Nothing is skipped.** Every phase, step and sub-step must be explicitly marked COMPLETE only after implementation and verification. If a dependency prevents completion, mark it BLOCKED and record the reason; do not silently bypass it.

## Phase 0 — Architecture Freeze

### 0.1 Repository audit
- [x] Confirm repository identity and visibility
- [x] Confirm default branch
- [x] Confirm current repository size/state
- [x] Confirm whether existing source code exists
- [x] Record existing application structure — empty baseline
- [x] Record existing build system — none existed
- [x] Record existing backend/frontend components — none existed
- [x] Record existing API integrations — none existed
- [x] Record existing database/storage integrations — none existed
- [x] Record existing authentication — none existed
- [x] Record existing permissions — none existed
- [x] Record existing CI/CD — none existed
- [x] Record existing tests — none existed
- [x] Record existing issues/PRs
- [x] Freeze baseline before implementation

### 0.2 Architecture decisions
- [x] Telephony provider decision — Exotel AgentStream initial India-first adapter; alternatives retained
- [x] Call-routing model decision — deterministic call-state machine with policy-driven routing
- [x] Media transport decision — provider media adapter with WSS/SIP/WebRTC boundary
- [x] Media-server/framework decision — LiveKit Agents primary; Pipecat fallback
- [x] STT decision — modular STT interface; realtime-model path primary initially
- [x] LLM decision — OpenAI Realtime adapter initially; provider abstraction retained
- [x] TTS decision — realtime model initially; explicit TTS interface retained for cascaded fallback
- [x] VAD decision — realtime turn detection/VAD initially; standalone VAD remains replaceable
- [x] Audio processing decision — normalized internal audio, jitter buffer, VAD, interruption, packet-loss handling, noise/gain processing where appropriate
- [x] Backend/runtime decision — Python + FastAPI + worker service
- [x] Database decision — PostgreSQL
- [x] Audio object-storage decision — S3-compatible encrypted object storage
- [x] Authentication/authorization decision — short-lived tokens + server-side authorization
- [x] Notification decision — FCM primary; optional adapters later
- [x] Calendar/CRM integration strategy — adapter-based, confirmation required for external actions
- [x] Observability strategy — structured logs, metrics, traces, error tracking, call correlation IDs
- [x] Security/privacy baseline — TLS/WSS, secret isolation, access control, encryption, retention, prompt-injection and sensitive-data controls
- [x] Failure/fallback strategy — bounded retry, human/voicemail fallback, safe termination
- [x] Cost-control strategy — per-call duration/model/recording budgets plus daily/monthly limits
- [x] Testing strategy — unit, integration, E2E, resilience, security and performance gates

### 0.3 Call-state model
- [x] Define every call state
- [x] Define every valid state transition
- [x] Define transition triggers
- [x] Define timeout for every applicable state
- [x] Define failure transition for every applicable state
- [x] Define human takeover transition
- [x] Define call termination transition
- [x] Define post-call transition

### 0.4 Baseline verification
- [x] Architecture reviewed
- [x] Dependencies identified
- [x] No unresolved critical architectural contradiction
- [x] Phase 0 completion audit performed

## Phase 1 — Telephony Foundation
- [ ] Virtual/DID number
- [x] Incoming webhook — endpoint and adapter boundary implemented; provider authentication remains blocked until account credentials/mechanism are configured
- [x] Caller metadata handling — adapter parses caller number
- [x] Call ID correlation — provider call ID is retained in domain session
- [ ] Human ringing path
- [ ] AI timeout path
- [ ] Conditional routing
- [x] Call-state persistence boundary — repository interface plus PostgreSQL model/repository and Alembic migration implemented; live DB verification remains pending
- [x] Telephony error handling — invalid/missing IDs and invalid transitions are rejected; provider-specific failure handling remains pending
- [x] Phase 1 tests — unit/security tests added; real-provider and live-PostgreSQL tests pending
- [ ] Phase 1 completion audit

## Phase 2 — Real-Time Audio Engine
- [ ] Media connection — Exotel AgentStream WSS endpoint and authenticated stream boundary implemented; real provider connection still requires account/configuration and runtime verification
- [ ] Streaming transport — WebSocket receive path implemented for text/binary AgentStream frames; real media streaming verification pending
- [x] Jitter buffering — bounded sequence-aware buffer implemented; gap recovery policy remains separate
- [ ] AEC
- [ ] Noise suppression
- [ ] AGC where appropriate
- [ ] VAD
- [ ] Packet-loss handling
- [ ] Audio buffering
- [ ] Input pipeline
- [ ] Output pipeline
- [ ] Phase 2 tests — parser and WebSocket tests added; runtime execution and real-call verification pending
- [ ] Phase 2 completion audit

## Phase 3 — AI Voice Brain
- [ ] Streaming STT
- [ ] Partial transcript
- [ ] Final transcript
- [ ] Language handling
- [ ] Conversation manager
- [ ] Intent context
- [ ] Policy context
- [ ] LLM streaming
- [ ] Streaming TTS
- [ ] Response validation
- [ ] AI disclosure
- [ ] Phase 3 tests
- [ ] Phase 3 completion audit

## Phase 4 — Barge-in
- [ ] Speech detection during TTS
- [ ] TTS cancellation
- [ ] Audio-buffer flush
- [ ] Caller speech capture
- [ ] Context preservation
- [ ] Repeated interruption handling
- [ ] Barge-in latency measurement
- [ ] Phase 4 tests
- [ ] Phase 4 completion audit

## Phase 5 — Intent & Routing
- [ ] Caller classification
- [ ] Intent classification
- [ ] Confidence scores
- [ ] Spam scoring
- [ ] Urgency scoring
- [ ] Configurable thresholds
- [ ] Routing rules
- [ ] Rule precedence
- [ ] Human escalation
- [ ] Phase 5 tests
- [ ] Phase 5 completion audit

## Phase 6 — Human Takeover
- [ ] Takeover request
- [ ] AI speech stop
- [ ] AI input/output mute logic
- [ ] Human bridge
- [ ] Caller continuity
- [ ] Transcript continuity
- [ ] Recording continuity
- [ ] Takeover timeout
- [ ] Takeover failure fallback
- [ ] Phase 6 tests
- [ ] Phase 6 completion audit

## Phase 7 — Whisper / Coach
- [ ] Listen-only mode
- [ ] Private coach channel
- [ ] Human-to-caller mute state
- [ ] Caller-to-human audio
- [ ] AI suggestions
- [ ] Privacy controls
- [ ] Phase 7 tests
- [ ] Phase 7 completion audit

## Phase 8 — Live Dashboard
- [ ] Active call screen
- [ ] Caller identity
- [ ] Live transcript
- [ ] Intent/urgency/spam indicators
- [ ] Takeover control
- [ ] Whisper control
- [ ] End-call control
- [ ] Connection status
- [ ] Error state UI
- [ ] Phase 8 tests
- [ ] Phase 8 completion audit

## Phase 9 — Identity & Memory
- [ ] Contact resolution
- [ ] Local contact privacy boundary
- [ ] Known/unknown classification
- [ ] Short-term conversation memory
- [ ] Memory expiry
- [ ] Caller history
- [ ] Previous intent
- [ ] Previous interaction metadata
- [ ] Phase 9 tests
- [ ] Phase 9 completion audit

## Phase 10 — IVR / Spam / Voicemail
- [ ] Human detection
- [ ] IVR detection
- [ ] DTMF detection — AgentStream DTMF event is now parsed and validated at the transport boundary; IVR behavior is not implemented
- [ ] Voicemail detection
- [ ] Automated caller handling
- [ ] Configurable actions
- [ ] Phase 10 tests
- [ ] Phase 10 completion audit

## Phase 11 — Security & Privacy
- [ ] TLS/HTTPS
- [ ] Secure WebSocket
- [ ] Authentication
- [ ] Authorization
- [ ] Session/device controls
- [ ] Secret management
- [ ] API-key isolation
- [ ] Encryption at rest
- [ ] Secure audio URLs
- [ ] Prompt-injection defenses
- [ ] Sensitive-data policy
- [ ] Data retention controls
- [ ] Phase 11 security tests
- [ ] Phase 11 completion audit

## Phase 12 — Recording & Transcript
- [ ] Recording pipeline
- [ ] Encrypted object storage
- [ ] Transcript storage
- [ ] Call metadata
- [ ] Recording retention
- [ ] Transcript retention
- [ ] Retrieval permissions
- [ ] Phase 12 tests
- [ ] Phase 12 completion audit

## Phase 13 — Post-call AI
- [ ] Transcript finalization
- [ ] Summary
- [ ] Intent
- [ ] Urgency
- [ ] Action extraction
- [ ] Structured output validation
- [ ] Phase 13 tests
- [ ] Phase 13 completion audit

## Phase 14 — Notifications
- [ ] Android notification
- [ ] FCM
- [ ] Optional Telegram
- [ ] Optional SMS
- [ ] Notification preferences
- [ ] Notification failure handling
- [ ] Phase 14 tests
- [ ] Phase 14 completion audit

## Phase 15 — Calendar / CRM
- [ ] Structured action schema
- [ ] User confirmation
- [ ] Calendar integration
- [ ] CRM integration
- [ ] Permission boundaries
- [ ] Failure handling
- [ ] Phase 15 tests
- [ ] Phase 15 completion audit

## Phase 16 — Failure Recovery
- [ ] STT retry
- [ ] LLM retry
- [ ] TTS retry
- [ ] Telephony failure path
- [ ] Network disconnect
- [ ] WebSocket reconnect
- [ ] Provider failure
- [ ] Human fallback
- [ ] Voicemail fallback
- [ ] Safe termination
- [ ] Phase 16 tests
- [ ] Phase 16 completion audit

## Phase 17 — Observability
- [ ] Call correlation IDs
- [ ] Structured events
- [ ] Metrics
- [ ] Logs
- [ ] Error tracking
- [ ] Latency tracing
- [ ] Takeover metrics
- [ ] Failure metrics
- [ ] Phase 17 tests
- [ ] Phase 17 completion audit

## Phase 18 — Latency & Cost
- [ ] STT latency
- [ ] LLM TTFT
- [ ] TTS first-audio latency
- [ ] End-to-end latency
- [ ] Barge-in latency
- [ ] Telephony latency
- [ ] Per-call cost
- [ ] Daily/monthly budget
- [ ] Call-duration limits
- [ ] Optimization pass
- [ ] Phase 18 completion audit

## Phase 19 — Testing
- [ ] Unit tests
- [ ] Integration tests
- [ ] End-to-end call tests
- [ ] Long-call tests
- [ ] Noisy-audio tests
- [ ] Repeated-interruption tests
- [ ] Network-failure tests
- [ ] Provider-failure tests
- [ ] Takeover tests
- [ ] Security tests
- [ ] Regression tests
- [ ] Phase 19 completion audit

## Phase 20 — Beta / Production
- [ ] One-number beta
- [ ] One-user beta
- [ ] Real-call validation
- [ ] Monitoring
- [ ] Bug fixes
- [ ] Production readiness audit
- [ ] Full roadmap completion audit
- [ ] Release
