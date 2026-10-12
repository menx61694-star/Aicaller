# Phase 4 — Barge-in Audit

## Scope

This audit records code-side coverage for speech detection during TTS, cancellation signalling, outbound audio flush, caller speech capture, interruption context preservation, repeated interruption limits, and deterministic latency measurement.

## Implemented boundaries

- `src/aicaller/ai/barge_in.py`: configurable consecutive-speech detector with confidence threshold and reset.
- `src/aicaller/audio/tts_cancel.py`: idempotent cancellation signal for an active TTS stream.
- `src/aicaller/audio/output.py`: flushes pending outbound frames and resets sequence cursor so a new TTS generation can start cleanly.
- `src/aicaller/audio/barge_in_capture.py`: bounded caller audio capture with stream validation and timestamps.
- `src/aicaller/ai/barge_in_context.py`: retains interrupted caller utterance and TTS generation for continuation.
- `src/aicaller/ai/repeated_barge_in.py`: limits repeated interruptions and advances generations; rejected events must not mutate guard state.
- `src/aicaller/audio/barge_in_latency.py`: validates event ordering and reports detection-to-cancellation / detection-to-flush durations.
- `tests/test_phase4_barge_in_chain.py`: deterministic component-chain coverage for detection, cancellation, flush, capture, context and latency.

## Verification boundary

- Workflow #125 passed for commit `7ff29963876ae4e14591d406e6decc7cb83d7f62`.
- Follow-up hardening of repeated-interruption rejection is in commits `7ee5f21d5db10c362c9994ec1d2ff853bbf995bb` and `bb1d2d8dc26cec5b1b16bcc27532a56c8b839d2e`; their workflows must pass before the final Phase 4 checklist items are marked verified.
- Unit/integration tests do not prove real-time telephony behavior. Provider runtime, acoustic conditions, actual TTS cancellation propagation, transport-side audio already in flight, and measured production latency remain unverified without a deployed provider smoke test.

## Exit criteria

- [ ] Latest Phase 2 test workflow is green after all Phase 4 changes.
- [ ] Repeated-interruption limit and rejected-event state invariants are CI-verified.
- [ ] Phase 4 test suite and lint are green on the same final commit.
- [ ] Real provider runtime smoke test performed, or explicitly left blocked on account/deployment access.
- [ ] Project checklist updated without marking provider-runtime work complete from unit tests alone.
