import logging
import os

import assemblyai as aai
from assemblyai.streaming.v3 import (
    StreamingClient,
    StreamingClientOptions,
    StreamingEvents,
    StreamingParameters,
)
from dotenv import load_dotenv

from services.transcript_service import transcript_service

load_dotenv()

api_key = os.getenv("ASSEMBLYAI_API_KEY")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    """Main function to start the streaming transcript service"""
    client = StreamingClient(
        StreamingClientOptions(
            api_key=api_key,
            api_host="streaming.assemblyai.com",
        )
    )

    # Use the transcript service's methods as event handlers
    client.on(StreamingEvents.Begin, transcript_service.on_begin)
    client.on(StreamingEvents.Turn, transcript_service.on_turn)
    client.on(StreamingEvents.Termination, transcript_service.on_terminated)
    client.on(StreamingEvents.Error, transcript_service.on_error)

    client.connect(
        StreamingParameters(
            sample_rate=16000,
            format_turns=True,
        )
    )

    try:
        client.stream(aai.extras.MicrophoneStream(sample_rate=16000))
    finally:
        client.disconnect(terminate=True)

if __name__ == "__main__":
    main()