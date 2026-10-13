# Phase 5 — Provider Validation Runbook

This runbook is for closing the remaining real-provider verification gate for Intent & Routing. CI tests use mocked transports and **do not** prove that an account can complete a real call.

## Safety and prerequisites

- Use a dedicated test number and a test Exotel account/app; do not test on an unsuspecting person's live phone.
- Keep API credentials in local environment variables or a secret manager. Never commit `.env`, keys, tokens, phone numbers, or raw call audio.
- Required for OpenAI runtime: a valid `OPENAI_API_KEY` with Realtime access.
- Required for the Exotel AgentStream path: configured Exotel account/app, public HTTPS/WSS endpoint, provider allowlisting/authentication, and an account-specific human ring/bridge/transfer flow.
- The current `ExotelAdapter.start_human_ring` and `request_human_takeover` deliberately fail closed. A live human escalation must not be attempted until those methods are backed by the correct account-specific action and that action is verified.

## A. OpenAI Realtime connection smoke test

1. Install the project and dependencies using the repository's documented environment setup.
2. Set `OPENAI_API_KEY` in the local environment (do not echo it in logs).
3. Run this short smoke test from the repository root:

   ```bash
   python - <<'PY'
   import asyncio
   import os
   from aicaller.ai.openai_realtime_transport import (
       OpenAIRealtimeTranscriptionTransport,
   )

   async def main():
       key = os.environ.get("OPENAI_API_KEY", "")
       transport = await OpenAIRealtimeTranscriptionTransport.connect(key)
       print("OpenAI Realtime transcription session initialized")
       await transport.close()
       print("OpenAI Realtime socket closed cleanly")

   asyncio.run(main())
   PY
   ```

4. Record the date, tested deployment/environment, result, and sanitized error class/message. Never record the API key.
5. A successful handshake verifies authentication/session setup only; it does not verify transcript quality, latency, or telephony audio.

## B. End-to-end AgentStream transcription test

1. Deploy the app behind a valid TLS certificate and expose the configured AgentStream WebSocket route.
2. Configure the Exotel test app to stream mono 8 kHz media to that WSS endpoint and configure request authentication/allowlisting according to the account.
3. Set `OPENAI_API_KEY` for the service. Confirm startup does not log secrets.
4. Place a controlled test call and speak a short routine sentence, then an explicit human-request/urgent phrase. Confirm sanitized `realtime intent routing evaluated` events include the final transcript's intent, routing action, call state, and transition reason.
5. Confirm partial transcript events do not trigger routing; confirm routine/unknown calls do not request a human; confirm the final urgent transcript requests escalation in policy.
6. Stop/disconnect the call and confirm the OpenAI WebSocket closes and no reader task is left running.
7. Record the sanitized call correlation ID, result, and measured end-to-end latency. Do not store raw audio/transcripts unless consent, access, and retention policy explicitly allow it.

## C. Human escalation bridge gate

1. Implement/configure the exact Exotel account-specific ring/bridge/transfer action; do not replace the fail-closed adapter with a guessed endpoint.
2. Test success, provider rejection, timeout, invalid destination, and disconnect during escalation.
3. Verify the domain state transitions to `HUMAN_CALL` or `TAKEOVER_REQUESTED` only after provider acceptance. On every failure, verify the state remains unchanged and the reason is observable.
4. Verify the caller stays connected, audio paths are correct, and the human receives the intended call. Capture no more personal data than required.
5. Do not mark Phase 5 complete until this test passes against the actual Exotel account.

## Sign-off record

Fill this section only with real observed results:

- OpenAI handshake: **PENDING**
- Live AgentStream transcription/routing: **PENDING**
- Exotel human ring/bridge/transfer: **BLOCKED — account-specific flow not configured**
- Regression CI: see the latest successful GitHub Actions run linked from the Phase 5 audit.
- Final Phase 5 sign-off: **PENDING**
