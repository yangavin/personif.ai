import threading
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional
import logging
import requests
import random

from assemblyai.streaming.v3 import (
    BeginEvent,
    StreamingClient,
    StreamingError,
    StreamingSessionParameters,
    TerminationEvent,
    TurnEvent,
)

logger = logging.getLogger(__name__)


@dataclass
class TranscriptEntry:
    transcript: str
    timestamp: datetime
    is_end_of_turn: bool
    is_partial: bool


class TranscriptService:
    """Service for managing streaming transcript data with thread-safe access"""
    
    def __init__(self):
        self._lock = threading.Lock()
        self._current_transcript = ""
        self._complete_transcript = ""
        self._transcript_history: List[TranscriptEntry] = []
        self._session_id: Optional[str] = None
        self._is_active = False
    
    def on_begin(self, client: StreamingClient, event: BeginEvent):
        """Handle streaming session begin event"""
        with self._lock:
            self._session_id = event.id
            self._is_active = True
            self._current_transcript = ""
            self._complete_transcript = ""
            self._transcript_history.clear()
        print(f"Session started: {event.id}")
    
    def on_turn(self, client: StreamingClient, event: TurnEvent):
        """Handle streaming transcript turn event"""
        with self._lock:
            # Store in history
            entry = TranscriptEntry(
                transcript=event.transcript,
                timestamp=datetime.now(),
                is_end_of_turn=event.end_of_turn,
                is_partial=not event.end_of_turn
            )
            self._transcript_history.append(entry)
            
            # Update current transcript
            self._current_transcript = event.transcript
            
            # If it's end of turn, add to complete transcript
            if event.end_of_turn:
                if self._complete_transcript:
                    self._complete_transcript += " " + event.transcript
                else:
                    self._complete_transcript = event.transcript
                
                # Check if we need to make API call
                self._handle_end_of_turn()
        
        print(f"{event.transcript} ({event.end_of_turn})")
        
        if event.end_of_turn and not event.turn_is_formatted:
            params = StreamingSessionParameters(format_turns=True)
            client.set_params(params)
    
    def on_terminated(self, client: StreamingClient, event: TerminationEvent):
        """Handle streaming session termination event"""
        with self._lock:
            self._is_active = False
        print(f"Session terminated: {event.audio_duration_seconds} seconds of audio processed")
    
    def on_error(self, client: StreamingClient, error: StreamingError):
        """Handle streaming error event"""
        print(f"Error occurred: {error}")
    
    # Public methods to access the data
    def get_current_transcript(self) -> str:
        """Get the most recent transcript (may be partial)"""
        with self._lock:
            return self._current_transcript
    
    def get_complete_transcript(self) -> str:
        """Get all completed turns concatenated"""
        with self._lock:
            return self._complete_transcript
    
    def get_transcript_history(self) -> List[TranscriptEntry]:
        """Get full history of all transcript events"""
        with self._lock:
            return self._transcript_history.copy()
    
    def get_recent_turns(self, count: int = 5) -> List[TranscriptEntry]:
        """Get the most recent completed turns"""
        with self._lock:
            completed_turns = [entry for entry in self._transcript_history if entry.is_end_of_turn]
            return completed_turns[-count:] if completed_turns else []
    
    def is_session_active(self) -> bool:
        """Check if streaming session is currently active"""
        with self._lock:
            return self._is_active
    
    def get_session_id(self) -> Optional[str]:
        """Get the current session ID"""
        with self._lock:
            return self._session_id
    
    def clear_transcript(self):
        """Clear all stored transcript data"""
        with self._lock:
            self._current_transcript = ""
            self._complete_transcript = ""
            self._transcript_history.clear()
    
    def _handle_end_of_turn(self):
        """Handle end of turn - check if we need to make API call"""
        try:
            # Import here to avoid circular imports
            from .speaker_service import speaker_service
            
            # Check if the last speaker was not the user
            last_speaker_was_user = speaker_service.get_last_speaker_was_user()
            
            if last_speaker_was_user is not None and not last_speaker_was_user:
                logger.info("🔴 End of turn detected and last speaker was not the user - making API call")
                self._make_random_api_call()
            else:
                logger.info("🟢 End of turn detected but last speaker was the user - no API call needed")
                
        except Exception as e:
            logger.error(f"Error handling end of turn: {e}")
    
    def _make_random_api_call(self):
        """Make an API call to a random example endpoint"""
        try:
            # List of example endpoints to choose from
            example_endpoints = [
                "https://jsonplaceholder.typicode.com/posts/1",
                "https://httpbin.org/get",
                "https://api.github.com/zen",
                "https://httpbin.org/uuid",
                "https://jsonplaceholder.typicode.com/users/1"
            ]
            
            # Choose a random endpoint
            endpoint = random.choice(example_endpoints)
            
            logger.info(f"Making API call to: {endpoint}")
            
            # Make the API call with a timeout
            response = requests.get(endpoint, timeout=5)
            
            if response.status_code == 200:
                logger.info(f"✅ API call successful! Status: {response.status_code}")
                # Log first 200 characters of response for debugging
                response_text = response.text[:200] + "..." if len(response.text) > 200 else response.text
                logger.info(f"Response preview: {response_text}")
            else:
                logger.warning(f"⚠️ API call returned status {response.status_code}")
                
        except requests.exceptions.Timeout:
            logger.error("❌ API call timed out")
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ API call failed: {e}")
        except Exception as e:
            logger.error(f"❌ Unexpected error during API call: {e}")


# Global service instance that can be accessed from anywhere
transcript_service = TranscriptService()