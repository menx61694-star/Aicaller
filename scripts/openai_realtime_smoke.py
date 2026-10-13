"""Run a real OpenAI Realtime transcription-session handshake.

Requires OPENAI_API_KEY in the environment. Never prints the key or provider payloads.
"""
from __future__ import annotations

import asyncio
import os
import sys

from aicaller.ai.openai_realtime_transport import (
    OpenAIRealtimeTranscriptionTransport,
)


async def main() -> int:
    api_key = os.environ.get("OPENAI_API_KEY", "")
    if not api_key.strip():
        print("FAIL: OPENAI_API_KEY is not configured.")
        return 2

    transport = None
    try:
        transport = await OpenAIRealtimeTranscriptionTransport.connect(api_key)
        print("PASS: OpenAI Realtime session created and transcription configuration accepted.")
        return 0
    except Exception as exc:
        # Do not print exception text: provider responses can contain sensitive details.
        print(f"FAIL: Realtime handshake failed ({type(exc).__name__}).")
        return 1
    finally:
        if transport is not None:
            await transport.close()
            print("PASS: Realtime WebSocket closed cleanly.")


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
