import threading
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, Dict, Any
import logging
import requests
import random
import json
import os

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
    
    def __init__(self, json_output_path: str = "live_transcription.json"):
        self._lock = threading.Lock()
        self._current_transcript = ""
        self._complete_transcript = ""
        self._transcript_history: List[TranscriptEntry] = []
        self._session_id: Optional[str] = None
        self._is_active = False
        
        # JSON transcription tracking
        self.json_output_path = json_output_path
        self._current_speaker = "other"  # Start with "other" as per requirement
        self._transcription_data = {"you": "", "other": ""}
        self._finalized_text = {"you": "", "other": ""}  # Track finalized text separately
        self._initialize_json_file()
    
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
            with open(self.json_output_path, 'w', encoding='utf-8') as f:
                json.dump(self._transcription_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Failed to write JSON file: {e}")
    
    def _update_transcription(self, text: str, is_end_of_turn: bool):
        """Update the transcription data and write to JSON"""
        try:
            # Track finalized text separately from current turn text
            if not hasattr(self, '_finalized_text'):
                self._finalized_text = {"you": "", "other": ""}
            
            # Determine actual speaker from speaker recognition
            actual_speaker = self._get_actual_speaker()
            
            # Check if we should skip updating "other" due to recent clearing
            if hasattr(self, '_skip_next_other_update') and self._skip_next_other_update and actual_speaker == "other":
                self._skip_next_other_update = False
                # Update current speaker for next turn
                if is_end_of_turn:
                    self._current_speaker = actual_speaker
                    logger.info(f"🔄 Turn ended, current speaker: {self._current_speaker}")
                return
            
            # Update current speaker based on recognition
            self._current_speaker = actual_speaker
            
            if not is_end_of_turn:
                # Live update - show finalized text + current partial text
                if self._finalized_text[self._current_speaker]:
                    self._transcription_data[self._current_speaker] = self._finalized_text[self._current_speaker] + " " + text
                else:
                    self._transcription_data[self._current_speaker] = text
            else:
                # End of turn - finalize the text
                if self._finalized_text[self._current_speaker]:
                    self._finalized_text[self._current_speaker] += " " + text
                else:
                    self._finalized_text[self._current_speaker] = text
                
                # Update the JSON with finalized text
                self._transcription_data[self._current_speaker] = self._finalized_text[self._current_speaker]
                
                logger.info(f"🔄 Turn ended, speaker was: {self._current_speaker}")
            
            # Write to JSON file
            self._write_json_file()
                
        except Exception as e:
            logger.error(f"Failed to update transcription: {e}")
    
    def _get_actual_speaker(self) -> str:
        """Get the actual speaker based on speaker recognition"""
        try:
            from .speaker_service import speaker_service
            last_speaker_was_user = speaker_service.get_last_speaker_was_user()
            
            if last_speaker_was_user is None:
                # Fallback to current speaker if no recognition data
                return self._current_speaker
            
            return "you" if last_speaker_was_user else "other"
        except Exception as e:
            logger.error(f"Error getting actual speaker: {e}")
            return self._current_speaker
    
    def on_begin(self, client: StreamingClient, event: BeginEvent):
        """Handle streaming session begin event"""
        with self._lock:
            self._session_id = event.id
            self._is_active = True
            self._current_transcript = ""
            self._complete_transcript = ""
            self._transcript_history.clear()
            
            # Reset transcription data for new session
            self._current_speaker = "other"  # Always start with "other"
            self._transcription_data = {"you": "", "other": ""}
            self._finalized_text = {"you": "", "other": ""}
            self._write_json_file()
            
        print(f"Session started: {event.id}")
        logger.info(f"📝 JSON transcription reset - starting with speaker: {self._current_speaker}")
    
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
            
            # If it's end of turn, handle API call BEFORE updating transcription
            # This ensures we check the current speaker before switching
            if event.end_of_turn:
                # Check if we need to make API call (before speaker switch)
                self._handle_end_of_turn(event.transcript)
                
                # Add to complete transcript
                if self._complete_transcript:
                    self._complete_transcript += " " + event.transcript
                else:
                    self._complete_transcript = event.transcript
            
            # Update JSON transcription with live data (this will switch speakers if end_of_turn)
            self._update_transcription(event.transcript, event.end_of_turn)
        
        # Show the actual speaker based on recognition
        actual_speaker = self._get_actual_speaker()
        print(f"[{actual_speaker.upper()}] {event.transcript} ({event.end_of_turn})")
        
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
            
            # Reset JSON transcription data
            self._current_speaker = "other"
            self._transcription_data = {"you": "", "other": ""}
            self._finalized_text = {"you": "", "other": ""}
            self._write_json_file()
            logger.info("📝 Transcript and JSON data cleared")
    
    def get_json_transcription(self) -> Dict[str, str]:
        """Get current JSON transcription data"""
        with self._lock:
            return self._transcription_data.copy()
    
    def get_current_speaker(self) -> str:
        """Get the current speaker (you/other)"""
        with self._lock:
            return self._current_speaker
    
    def set_json_output_path(self, path: str):
        """Set a new path for JSON output"""
        with self._lock:
            self.json_output_path = path
            self._write_json_file()
            logger.info(f"JSON output path updated to: {path}")
    
    def _handle_end_of_turn(self, transcript_text: str):
        """Handle end of turn - check if we need to make API call"""
        try:
            # Import here to avoid circular imports
            from .speaker_service import speaker_service
            
            # Get the actual speaker recognition result instead of using turn alternation
            last_speaker_was_user = speaker_service.get_last_speaker_was_user()
            
            # Determine who was actually speaking based on speaker recognition
            if last_speaker_was_user is None:
                logger.info("⚠️ End of turn: no speaker recognition data available - no API call made")
                return
            
            actual_speaker = "you" if last_speaker_was_user else "other"
            
            # Guard rail: Only make API call if:
            # 1. The actual speaker (from recognition) was "other" 
            # 2. AND there's actual transcript content to send
            
            if (not last_speaker_was_user and 
                transcript_text.strip() and 
                len(transcript_text.strip()) > 0):
                
                logger.info("🔴 End of turn: 'other' finished speaking (via speaker recognition) - making API call with transcript")
                self._make_api_call_with_transcript(transcript_text)
                self._clear_current_transcript()
            else:
                if last_speaker_was_user:
                    logger.info("🟢 End of turn: 'you' finished speaking (via speaker recognition) - no API call needed")
                elif not transcript_text.strip():
                    logger.info("⚠️ End of turn: empty transcript - no API call made")
                else:
                    logger.info(f"ℹ️ End of turn: speaker recognition indicates '{actual_speaker}' - no API call needed")
                
        except Exception as e:
            logger.error(f"Error handling end of turn: {e}")
    
    def _make_api_call_with_transcript(self, transcript_text: str):
        """Make an API call with the transcript data"""
        try:
            # Example endpoint that accepts POST data
            endpoint = "https://httpbin.org/post"
            
            # Prepare the payload with transcript
            payload = {
                "transcript": transcript_text,
                "speaker": "other",
                "timestamp": datetime.now().isoformat(),
                "session_id": self._session_id
            }
            
            logger.info(f"Making API call to: {endpoint}")
            logger.info(f"Transcript content: '{transcript_text}'")
            
            # Make the API call with a timeout
            response = requests.post(endpoint, json=payload, timeout=5)
            
            if response.status_code == 200:
                logger.info(f"✅ API call successful! Status: {response.status_code}")
                # Log response for debugging
                try:
                    response_data = response.json()
                    logger.info(f"Response data received: {response_data.get('json', {})}")
                except:
                    logger.info("Response received (non-JSON)")
            else:
                logger.warning(f"⚠️ API call returned status {response.status_code}")
                
        except requests.exceptions.Timeout:
            logger.error("❌ API call timed out")
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ API call failed: {e}")
        except Exception as e:
            logger.error(f"❌ Unexpected error during API call: {e}")
    
    def _clear_current_transcript(self):
        """Clear the current transcript data"""
        try:
            # Clear the "other" speaker's text since they just finished speaking
            # We need to clear both the display data and finalized data
            self._transcription_data["other"] = ""
            self._finalized_text["other"] = ""
            
            # Set a flag to prevent the next _update_transcription from overwriting
            self._skip_next_other_update = True
            
            # Write updated JSON
            self._write_json_file()
            
            logger.info("🗑️ Cleared 'other' speaker transcript after API call")
            
        except Exception as e:
            logger.error(f"Failed to clear transcript: {e}")
    
    def _make_random_api_call(self):
        """Make an API call to a random example endpoint (legacy method)"""
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