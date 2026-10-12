# Phase 5 — Intent & Routing Progress Audit

## Implemented and CI-verified

- `src/aicaller/ai/classification.py`: deterministic phrase-based caller classification for urgent, human-request, spam, important, routine, and unknown intents. English, Hindi transliteration, and selected Devanagari phrases are covered. Local negation checks prevent direct phrases such as “not an emergency” or “emergency nahi hai” from triggering urgent classification. These are rule-derived indicators, not calibrated probabilities.
- `src/aicaller/ai/intent.py`: monotonic intent context store retains intent, confidence, sequence, and reason.
- `src/aicaller/ai/intent_routing.py`: explicit routing precedence and configurable thresholds. Urgency and explicit human-request scores outrank spam signals; intent labels cannot bypass configured score thresholds; automatic spam blocking is opt-in and defaults off.
- `src/aicaller/ai/intent_routing_service.py`: connects classifier → router → intent/policy context stores. It preflights monotonic sequences before writes and rejects partial realtime transcript events as routing inputs.
- `src/aicaller/services/intent_call_coordinator.py`: applies `REQUEST_HUMAN` decisions to the deterministic call state machine: RINGING → HUMAN_CALL and AI_CALL → TAKEOVER_REQUESTED. Escalation in unsupported states is deferred rather than forcing an invalid transition. Transcript stream IDs must match the coordinator's bound stream before classification or state mutation.
- `src/aicaller/services/realtime_intent_event_handler.py`: connects parsed `RealtimeAISession` transcript events to the call coordinator. Non-transcript and partial events do not trigger routing; final transcript events may trigger escalation.
- `tests/test_classification.py`: English and Hindi intent phrases, routine intent, urgency precedence, direct-negation cases, previous-sentence isolation, unknown text, threshold validation, and invalid input.
- `tests/test_intent_routing.py`: precedence, score-threshold enforcement, safe spam default, configurable escalation, unknown handling, and invalid score/threshold coverage.
- `tests/test_intent_routing_service.py`: end-to-end context persistence, final-transcript gating, partial-event non-mutation, safe spam default, stale-sequence non-mutation, and invalid sequence handling.
- `tests/test_intent_call_coordinator.py`: call-state escalation from RINGING and AI_CALL, unknown intent non-transition, unsupported-state deferral, invalid/missing call handling, and rejection of cross-stream transcript events without mutation.
- `tests/test_realtime_intent_event_handler.py`: final transcript escalation, partial transcript non-routing, unrelated provider event handling, stream binding, and malformed-event rejection.

## CI verification

- Workflows #130–#145 passed for classifier, routing, service and call-state coordinator implementation/tests; workflow #145 reported 181 tests passed and Ruff clean.
- Workflow #150 passed on commit `896a6a2f0bb501b698c490aac26b977e59f6ed6d`: 190 tests passed, one third-party deprecation warning, Ruff clean.
- Workflow #153 failed because its code commit was tested against the immediately previous test-file revision; six coordinator constructor tests used the old signature. The next commit updated all tests to the stream-bound constructor.
- Workflow #154 passed on commit `c91e5b9cb56050b05f69ad18162930e6209ba98e`: 193 tests passed and Ruff clean.
- Workflow #158 passed on commit `9d54a3fda0c55505d0bc6d586d00fb988cf6b461`: **198 tests passed**, one third-party deprecation warning, and `ruff check .` passed.
- Latest verified code workflow: https://github.com/menx61694-star/Aicaller/actions/runs/38284913977

## Limits / remaining work

- Phrase-based scores are not calibrated probabilities and are not production-grade ML classification.
- Hindi/English phrase coverage is still limited; representative transcript evaluation, broader language support, and model-based calibration remain pending.
- The transcript handler is now implemented and tested, but the live Exotel AgentStream loop still discards completed utterances and is not connected to a running OpenAI Realtime WebSocket session.
- The coordinator updates domain call state only; actual Exotel ring/bridge/hangup actions still require account-specific configuration and telephony adapter execution.
- Provider runtime verification and final regression/audit remain pending.
- Phase 5 is **not complete** until live worker wiring, provider-dependent escalation, and final audit requirements are verified.
