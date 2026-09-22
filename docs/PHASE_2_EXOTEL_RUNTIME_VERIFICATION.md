# Phase 2 — Exotel AgentStream Runtime Verification

CI has verified the deterministic test suite and Ruff lint. The remaining Phase 2 gate is real Exotel runtime verification.

## Required real-call checks

1. Authenticated WSS connection from Exotel to the deployed Aicaller endpoint.
2. START event received and accepted.
3. Continuous inbound media frames received.
4. Actual sample rate and encoding observed and accepted.
5. Sequence/timestamp behavior observed under the live stream.
6. Jitter and packet-loss behavior observed.
7. Outbound media accepted and played by Exotel.
8. Acoustic echo behavior and AEC reference alignment checked.
9. Noise suppression and AGC checked on PSTN audio.
10. VAD/utterance boundaries checked with a real caller.
11. STOP/disconnect behavior checked.
12. Runtime latency and resource usage recorded.

## Required account configuration

- Public WSS endpoint for `/api/ws/exotel/agentstream`
- Exotel AgentStream enabled for the account
- Exotel API key/token configured server-side
- Required Exotel IP/network allowlisting
- Controlled test caller and destination

Never put production credentials in source control or CI logs.

## Completion rule

Do not mark the Phase 2 media connection, streaming transport, AEC, noise suppression, AGC, or VAD items complete from unit tests alone. They require this real-provider smoke test.

Current status: **BLOCKED pending real Exotel account/runtime verification.**
