# Phase 5 — Intent & Routing Progress Audit

## Implemented and CI-verified

- `src/aicaller/ai/classification.py`: deterministic phrase-based caller classification for urgent, human-request, spam, important, routine, and unknown intents. Configurable thresholds cover urgent, spam, important, and human-request indicators. Scores are rule-derived indicators, not calibrated probabilities.
- `src/aicaller/ai/intent.py`: monotonic intent context store retains intent, confidence, sequence, and reason.
- `src/aicaller/ai/intent_routing.py`: explicit routing precedence and configurable thresholds. Urgency and explicit human requests outrank spam signals; automatic spam blocking is opt-in and defaults off.
- `src/aicaller/ai/intent_routing_service.py`: connects classifier → router → intent/policy context stores. It preflights monotonic sequences before writes and rejects partial realtime transcript events as routing inputs.
- `src/aicaller/services/intent_call_coordinator.py`: applies `REQUEST_HUMAN` decisions to the deterministic call state machine: RINGING → HUMAN_CALL and AI_CALL → TAKEOVER_REQUESTED. Escalation in unsupported states is deferred rather than forcing an invalid transition. Coordinator state is scoped to one call.
- `tests/test_classification.py`: urgency, mixed spam/human precedence, configurable thresholds, routine intent, urgency-over-routine precedence, unknown text, and invalid input.
- `tests/test_intent_routing.py`: precedence, safe spam default, configurable escalation, unknown handling, and invalid score/threshold coverage.
- `tests/test_intent_routing_service.py`: end-to-end context persistence, final-transcript gating, partial-event non-mutation, safe spam default, stale-sequence non-mutation, and invalid sequence handling.
- `tests/test_intent_call_coordinator.py`: call-state escalation from RINGING and AI_CALL, unknown intent non-transition, unsupported-state deferral, and invalid/missing call handling.

## CI verification

- Workflows #130–#133 passed for the initial classifier and routing implementation/tests.
- Workflow #137 passed after removing an unused import; this run reported 171 tests passed and Ruff clean.
- Workflows #138 and #139 passed for final-transcript gating and its regression tests.
- Workflow #140 passed for routine-intent classification.
- Workflow #141 passed on commit `8af600a7beb4a10baf8575298d192530b8300590`: 175 tests passed and Ruff clean.
- Workflow #144 passed for call-state coordinator implementation.
- Workflow #145 passed on commit `384b688180b39ea7692f7c85cec01ae41516590b`: **181 tests passed**, one third-party deprecation warning, and `ruff check .` passed.
- Latest verified code workflow: https://github.com/menx61694-star/Aicaller/actions/runs/38282886820

## Limits / remaining work

- Phrase-based scores are not calibrated probabilities and are not production-grade ML classification.
- Locale/language-specific phrases, representative transcript evaluation, and model-based calibration remain pending.
- The coordinator updates domain call state only; actual Exotel ring/bridge/hangup actions still require account-specific configuration and telephony adapter execution.
- Provider runtime verification, Phase 5 full regression/audit, and external bridge behavior remain pending.
- Phase 5 is **not complete** until provider-dependent escalation and final audit requirements are verified.
