# Aicaller

AI-powered incoming-call screening and human takeover service.

## Current phase

**Phase 5 — Intent & Routing (in progress; not signed off).**

The repository includes deterministic intent classification/routing, a fail-closed provider-confirmed escalation coordinator, OpenAI Realtime transcription transport, and an AgentStream-to-transcript routing path. These paths have automated tests, but mocked CI does not establish real-provider readiness.

Phase 5 remains open until the OpenAI Realtime handshake and live AgentStream path are verified against configured services and the account-specific Exotel human ring/bridge/transfer flow is implemented and tested. The Exotel human escalation adapter deliberately fails closed until that flow is configured.

## Stack

- Python 3.11+
- FastAPI
- Exotel AgentStream provider boundary
- OpenAI Realtime transcription transport
- Deterministic call-state machine and intent routing
- PostgreSQL / Redis / object-storage interfaces reserved

## Development rule

No phase, step, or sub-step is complete until implemented and verified. A passing unit/CI suite is not a substitute for live-provider verification.

See:
- `docs/PROJECT_CHECKLIST.md` for the exhaustive roadmap.
- `docs/PHASE_5_PROGRESS_AUDIT.md` for current Phase 5 implementation status.
- `docs/PHASE_5_PROVIDER_VALIDATION.md` for real-provider validation steps and remaining sign-off gates.
