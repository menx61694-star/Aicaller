# Phase 0 — Provider & Framework Evaluation

## Evaluation status

This is a documented architecture evaluation, not a production certification. Capabilities below are based on current official documentation checked on 21 September 2026. Pricing, India number availability, account approval, and contractual terms must still be validated during implementation.

## 1. Telephony candidates

| Candidate | Realtime media | Bidirectional AI audio | Human transfer/bridge | India relevance | Notes |
|---|---|---|---|---|---|
| Exotel AgentStream | Yes | Yes | Call-flow/agent routing capabilities | Strong India fit; Mumbai instance is specifically documented for Indian customers | Requires account setup/KYC/access enablement for AgentStream |
| Plivo | Yes | Yes | Yes | India numbers require KYC | Strong documented AI voice-agent workflow and live transfer |
| Twilio | Yes | Yes | Telephony call-control ecosystem | India support/capability must be validated for exact number/use case | Media Streams supports bidirectional WebSocket audio |

### Exotel

Exotel documents a bidirectional VoiceBot applet that sends caller audio to a WSS endpoint and accepts audio back for playback. Its AgentStream documentation also describes bidirectional streaming, stream lifecycle metadata, and routing context. Exotel recommends the Mumbai instance for Indian customers and states that AgentStream access requires KYC and enablement.

**Implication:** Exotel is a serious first candidate for an India-first deployment. Before locking it in, verify account approval, exact inbound-number availability, transfer semantics, recording rules, and production limits.

### Plivo

Plivo documents bidirectional Audio Streams for conversational AI, including audio returned from the WebSocket to the caller. Its AI-agent documentation also covers interruption using clearAudio, human transfer, India number KYC, and WebSocket failure callbacks.

**Implication:** Plivo is a strong technical fallback and should remain an adapter target even if Exotel becomes the initial provider.

### Twilio

Twilio documents bidirectional Media Streams using Connect/Stream, where the WebSocket receives caller audio and can send audio back to the call. Twilio's documentation states that bidirectional streams receive only the inbound track and support inbound DTMF.

**Implication:** Twilio is technically suitable for the media architecture, but India-specific number availability, pricing, and exact call-control requirements must be verified before production selection.

## 2. Media framework candidates

### LiveKit Agents

LiveKit Agents currently supports Python and Node.js, realtime media, STT-LLM-TTS pipelines, realtime speech-to-speech models, interruption handling, telephony through SIP, agent handoffs, tools, observability, and multiple AI providers.

**Decision:** Use LiveKit Agents as the primary media/agent framework candidate.

Reason: it maps closely to Aicaller's requirements for realtime audio, interruption, telephony, provider abstraction, and human/agent workflow orchestration.

### Pipecat

Pipecat remains an architecture candidate for a Python-first pipeline, especially if direct control over individual media/AI processors is needed.

**Decision:** Keep Pipecat as the secondary/fallback framework, not the initial implementation target.

## 3. AI pipeline candidates

### Primary architecture

Use modular STT/LLM/TTS interfaces even if the first implementation uses a realtime speech-to-speech model. This preserves the ability to inspect transcripts and intent separately, enforce deterministic policy before tool calls, switch model providers, implement custom fallback, and measure latency independently.

### Realtime model path

OpenAI Realtime is a valid primary candidate through LiveKit. LiveKit documents integration with the OpenAI Realtime API and interruption/context handling.

### Cascaded path

Keep STT → policy/intent → LLM → TTS available as a fallback architecture. LiveKit supports this model and multiple provider integrations.

**Decision:** Start with a realtime-model adapter for the first conversational prototype, but retain explicit STT/LLM/TTS interfaces in the application architecture. The realtime model must not bypass Aicaller's policy, state, routing, or audit layers.

## 4. Audio requirements

The media adapter must normalize provider-specific audio into an internal format and handle:
- sample-rate conversion
- codec conversion
- packet/frame sequencing
- jitter buffering
- VAD/turn detection
- interruption/barge-in
- noise suppression where appropriate
- gain normalization where appropriate
- packet loss/degraded-stream handling
- audio queue cancellation

Provider-specific codecs must never leak into the call-state machine or policy layer.

## 5. Provider selection gate

No telephony provider is final yet.

The provider must pass a real-call validation matrix covering:
1. inbound call establishment
2. webhook acknowledgement timing
3. AI answer after configured ringing delay
4. bidirectional audio
5. caller interruption
6. DTMF
7. voicemail/IVR behavior
8. human takeover
9. recording/transcript lifecycle
10. network/WebSocket failure
11. call termination
12. India number/KYC/account requirements
13. provider limits and pricing

Until this matrix is executed, the architecture remains provider-agnostic.
