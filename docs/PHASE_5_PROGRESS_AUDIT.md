# Phase 5 — Intent & Routing Progress Audit

## Implemented and CI-verified

- `src/aicaller/ai/classification.py`: deterministic phrase-based caller classification for urgent, human-request, spam, important, and routine intents. Configurable thresholds cover urgent, spam, important, and human-request indicators. Scores are rule-derived indicators, not calibrated probabilities.
- `src/aicaller/ai/intent.py`: monotonic intent context store retains intent, confidence, sequence, and reason.
- `src/aicaller/ai/intent_routing.py`: explicit routing precedence and configurable thresholds. Urgency and explicit human requests outrank spam signals; automatic spam blocking is opt-in and defaults off.
- `src/aicaller/ai/intent_routing_service.py`: connects classifier → router → intent/policy context stores. It preflights monotonic sequences before writes and rejects partial realtime transcript events as routing inputs.
- `tests/test_classification.py`: urgency, mixed spam/human precedence, configurable thresholds, routine intent, urgency-over-routine precedence, unknown text, and invalid input.
- `tests/test_intent_routing.py`: precedence, safe spam default, configurable escalation, unknown handling, and invalid score/threshold coverage.
- `tests/test_intent_routing_service.py`: end-to-end context persistence, final-transcript gating, partial-event non-mutation, safe spam default, stale-sequence non-mutation, and invalid sequence handling.

## CI verification

- Workflows #130–#133 passed for the initial classifier and routing implementation/tests.
- Workflow #137 passed after removing an unused import; this run reported 171 tests passed and Ruff clean.
- Workflows #138 and #139 passed for final-transcript gating and its regression tests.
- Workflow #140 passed for routine-intent classification.
- Workflow #141 passed on commit `8af600a7beb4a10baf8575298d192530b8300590`: **175 tests passed**, one third-party deprecation warning, and `ruff check .` passed.
- Latest verified workflow: https://github.com/menx61694-star/Aicaller/actions/runs/38282667808

## Limits / remaining work

- Phrase-based scores are not calibrated probabilities and are not production-grade ML classification.
- Locale/language-specific phrases, representative transcript evaluation, and model-based calibration remain pending.
- The service persists intent/policy context but is not yet wired into the live telephony call-state transition/worker path.
- Human escalation decisions are produced deterministically; the real Exotel bridge/transfer remains blocked on account-specific configuration and runtime verification.
- Phase 5 is **not complete** until live-call integration, remaining checklist items, and the final regression/audit are verified.
