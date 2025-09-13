import threading
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

from assemblyai.streaming.v3 import (
    BeginEvent,
    StreamingClient,
    StreamingError,
    StreamingSessionParameters,
    TerminationEvent,
    TurnEvent,
)


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


# Global service instance that can be accessed from anywhere
transcript_service = TranscriptService()