import threading
from datetime import datetime
from typing import List, Optional, Dict
import logging
import requests
import json

from assemblyai.streaming.v3 import (
    BeginEvent,
    StreamingClient,
    StreamingError,
    TerminationEvent,
    TurnEvent,
)

logger = logging.getLogger(__name__)


class TranscriptService:
    """Simplified service for managing streaming transcript data with JSON output"""

    def __init__(self, json_output_path: str = "live_transcription.json"):
        self._lock = threading.Lock()
        self._session_id: Optional[str] = None
        self._is_active = False

        # JSON transcription tracking
        self.json_output_path = json_output_path
        self._transcription_data: List[Dict[str, str]] = []
        self._initialize_json_file()
        self._curr_speaker = "you"
        self._prev_speaker = "you"
        self._end_of_turn_counter = 0  # Track end_of_turn events

        # Voice assistant instance - will be set externally
        self._voice_assistant = None

    def _initialize_json_file(self):
        """Initialize the JSON transcription file"""
        try:
            self._write_json_file()
            logger.info(f"Initialized JSON transcription file: {self.json_output_path}")
        except Exception as e:
            logger.error(f"Failed to initialize JSON file: {e}")

    def _write_json_file(self):
        """Write current transcription data to JSON file"""
        try:
            with open(self.json_output_path, "w", encoding="utf-8") as f:
                json.dump(self._transcription_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Failed to write JSON file: {e}")

    def _get_speaker(self) -> str:
        """Get the current speaker based on speaker recognition"""
        try:
            from .speaker_service import speaker_service

            last_speaker_was_user = speaker_service.get_last_speaker_was_user()
            return "you" if last_speaker_was_user else "other"
        except Exception as e:
            logger.error(f"Error getting speaker: {e}")
            return "other"  # Default fallback

    def on_begin(self, client: StreamingClient, event: BeginEvent):
        """Handle streaming session begin event"""
        with self._lock:
            self._session_id = event.id
            self._is_active = True
            self._transcription_data = []
            self._write_json_file()
            self._curr_speaker = "you"
            self._prev_speaker = "you"
            self._end_of_turn_counter = 0  # Reset counter for new session

        logger.info(f"Session started: {event.id}")

    def on_turn(self, client: StreamingClient, event: TurnEvent):
        """Handle streaming transcript turn event"""
        with self._lock:
            # Log with current speaker BEFORE any changes
            current_speaker_for_logging = self._curr_speaker

            # Add or update transcript entry
            if event.end_of_turn:
                self._end_of_turn_counter += 1

                # Only process every other end_of_turn (skip the raw, keep the formatted)
                if self._end_of_turn_counter % 2 == 0:
                    # Finalize the transcript entry (this should be the formatted version)
                    self._transcription_data.append(
                        {self._curr_speaker: event.transcript}
                    )
                    self._write_json_file()

                    # Make API call if "other" was speaking
                    if (
                        current_speaker_for_logging == "other"
                        and event.transcript.strip()
                    ):
                        self._make_api_call(event.transcript)

                    # Switch speaker for next turn
                    self._prev_speaker = self._curr_speaker
                    self._curr_speaker = (
                        "you" if self._prev_speaker == "other" else "other"
                    )

        logger.info(
            f"[{current_speaker_for_logging.upper()}] {event.transcript} (end_of_turn: {event.end_of_turn}) [Counter: {self._end_of_turn_counter}]"
        )

    def on_terminated(self, client: StreamingClient, event: TerminationEvent):
        """Handle streaming session termination event"""
        with self._lock:
            self._is_active = False
        logger.info(
            f"Session terminated: {event.audio_duration_seconds} seconds of audio processed"
        )

    def on_error(self, client: StreamingClient, error: StreamingError):
        """Handle streaming error event"""
        logger.error(f"Streaming error: {error}")

    def is_session_active(self) -> bool:
        """Check if streaming session is currently active"""
        with self._lock:
            return self._is_active

    def set_voice_assistant(self, voice_assistant):
        """Set the voice assistant instance to use for responses"""
        self._voice_assistant = voice_assistant

    def _make_api_call(self, transcript_text: str):
        """Process transcript with voice assistant or make fallback API call"""
        try:
            if self._voice_assistant:
                logger.info(f"🎤 Processing with voice assistant: '{transcript_text}'")
                # Use voice assistant to respond
                threading.Thread(
                    target=self._voice_assistant.respond_to_input,
                    args=(transcript_text,),
                    daemon=True,
                ).start()
            else:
                # Fallback to original API call behavior
                endpoint = "https://httpbin.org/post"
                payload = {
                    "transcript": transcript_text,
                    "speaker": "other",
                    "timestamp": datetime.now().isoformat(),
                    "session_id": self._session_id,
                }

                logger.info(
                    f"Making fallback API call with transcript: '{transcript_text}'"
                )
                response = requests.post(endpoint, json=payload, timeout=5)

                if response.status_code == 200:
                    logger.info("✅ Fallback API call successful")
                else:
                    logger.warning(
                        f"⚠️ Fallback API call returned status {response.status_code}"
                    )

        except Exception as e:
            logger.error(f"❌ Unexpected error during processing: {e}")


# Global service instance that can be accessed from anywhere
transcript_service = TranscriptService()
