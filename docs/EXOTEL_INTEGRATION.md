# Exotel Integration Boundary

## Verified from current Exotel AgentStream documentation

Exotel AgentStream Voicebot WSS endpoints support:

- IP allowlisting as an authentication option.
- HTTP Basic Authentication for the WSS connection.
- A `start` event containing stream/call metadata.
- `call_sid` as the provider call identifier.
- `from` / `to` caller and destination metadata.
- `media_format.sample_rate` for media configuration.
- Subsequent `media`, `stop`, `dtmf` and related stream events.

The implementation therefore keeps AgentStream WSS authentication and parsing separate from the generic HTTP telephony webhook.

## Implemented

- `ExotelStreamAdapter.verify_request()` validates the WSS `Authorization: Basic ...` header.
- Empty credentials fail closed.
- `ExotelStreamAdapter.parse_start()` validates the `start` event and extracts provider correlation metadata.
- The parsed start event can be converted into the domain `TelephonyEvent`.

## Not yet claimed as complete

The following still require validation against the user's actual Exotel account/flow:

- Exact account region/subdomain.
- IP allowlist requirements.
- Production WSS endpoint configuration.
- Voicebot/Stream Applet configuration.
- Real call delivery and media behavior.
- Transfer/human takeover behavior.
- Production provider event ordering and retry behavior.

The generic HTTP webhook adapter remains fail-closed until its exact production authentication mechanism is established for the selected Exotel flow.