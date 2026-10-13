# Phase 5 — Intent & Routing Progress Audit

## Implemented and CI-verified

- `src/aicaller/ai/classification.py`: deterministic phrase-based caller classification for urgent, human-request, spam, important, routine, and unknown intents. English, Hindi transliteration, and selected Devanagari phrases are covered. Local negation checks prevent direct phrases such as “not an emergency” or “emergency nahi hai” from triggering urgent classification. These are rule-derived indicators, not calibrated probabilities.
- `src/aicaller/ai/intent_routing.py`: explicit routing precedence and configurable thresholds. Urgency and explicit human-request scores outrank spam signals; intent labels cannot bypass configured score thresholds; automatic spam blocking is opt-in and defaults off.
- `src/aicaller/ai/intent_routing_service.py`: connects classifier → router → intent/policy context stores, preflights monotonic sequences before writes, and rejects partial realtime transcript events as routing inputs.
- `src/aicaller/services/intent_call_coordinator.py`: applies `REQUEST_HUMAN` decisions to the call state machine only after a provider action succeeds. Missing destination/provider configuration and provider errors leave the call state unchanged. Transcript stream IDs must match the call's bound stream.
- `src/aicaller/services/realtime_intent_event_handler.py`: routes only final transcript events; partial and unrelated events cannot change call routing.
- `src/aicaller/services/realtime_call_worker.py`: sends completed utterances as append+commit messages and routes received provider events. It supports injected audio encoding and surfaces provider error events instead of silently ignoring them.
- `src/aicaller/ai/openai_realtime_transport.py`: authenticated WebSocket transport for OpenAI Realtime transcription, configures `gpt-live-transcribe` with 8 kHz G.711 μ-law and English/Hindi language hints, waits for session initialization, and closes failed handshakes.
- `src/aicaller/audio/mulaw.py`: tested mono PCM16LE 8 kHz ↔ G.711 μ-law conversion.
- `src/aicaller/api/routes/exotel_stream.py`: when `OPENAI_API_KEY` is configured, connects the OpenAI transcription session on AgentStream START, sends completed VAD utterances to the realtime worker, reads transcript events concurrently, logs routing decisions, and closes the worker/transport on STOP/disconnect. When no key is configured, the optional AI transcription path remains disabled.
- `HUMAN_PHONE_NUMBER` is now documented in `.env.example`. Exotel human ring/takeover still intentionally fails closed until account-specific bridge actions are implemented/configured.
- Focused tests cover classification, precedence, provider-confirmed state transitions, cross-stream rejection, transcript-final gating, transport handshake, μ-law conversion, worker behavior, AgentStream utterance handoff, and a route-level final urgent transcript → coordinator → provider-action integration path. Additional regressions verify unexpected provider exceptions fail closed and repeated urgent events do not repeat takeover actions.
- `docs/PHASE_5_PROVIDER_VALIDATION.md` documents the real OpenAI handshake, live AgentStream routing, and account-specific Exotel bridge sign-off procedure. This runbook is not evidence that those live checks have passed.

## CI verification

- Workflows #130–#145 passed for initial classifier/routing/service/coordinator implementation and tests.
- Workflow #158 passed: 198 tests passed and Ruff clean.
- Workflow #162 passed: 203 tests passed and Ruff clean.
- Workflow #177 passed: 213 tests passed and Ruff clean.
- Workflow #187 passed: 217 tests passed and Ruff clean, including Exotel fail-closed escalation tests.
- Workflow #196 passed on commit `5f1662fa4f91e8e6d67c70ca8bb0704139f985a2`: 219 tests passed and Ruff clean.
- Workflow #201 passed on commit `6572f71cdda315e1439955ac5165174b0ffb269f`: route-level final urgent transcript routing test passed.
- Workflow #207 passed on commit `4bce13e652bf54843be1ea49c315a1b09bc11ceb`: **222 tests passed**, one third-party deprecation warning, and `ruff check .` passed.
- Latest verified code workflow: https://github.com/menx61694-star/Aicaller/actions/runs/38418643605

## Limits / remaining work

- Phrase-based scores are not calibrated probabilities or production-grade ML classification. Broader Hindi/English transcript evaluation and additional languages remain pending.
- Live AgentStream → OpenAI transcription → final transcript → classifier/router → domain coordinator wiring is now implemented and CI-tested, but it has **not** been verified against a real OpenAI API key or live Exotel call.
- Exotel ring/takeover provider actions remain unconfigured and deliberately fail closed. The domain call state does not claim a human ring/takeover succeeded unless the provider adapter returns successfully.
- Real provider credentials, public WSS deployment, Exotel allowlisting, bridge/transfer flow, real-call latency/audio validation, and final regression/audit remain pending. The validation procedure is documented in `docs/PHASE_5_PROVIDER_VALIDATION.md`.
- Phase 5 is **not complete** until provider runtime and human escalation are verified.
