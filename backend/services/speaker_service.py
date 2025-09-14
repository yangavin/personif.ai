import os
import threading
import numpy as np
import torch
import torchaudio
import soundfile as sf
from typing import Optional, Dict, Any
from dataclasses import dataclass
from datetime import datetime
import tempfile
import logging

from speechbrain.pretrained import SpeakerRecognition

logger = logging.getLogger(__name__)

@dataclass
class SpeakerResult:
    is_user: bool
    confidence: float
    similarity_score: float
    timestamp: datetime


class SpeakerService:
    """Service for speaker recognition using SpeechBrain"""
    
    def __init__(self, user_voice_profile_path: str = "user_voice_profile.npy"):
        self._lock = threading.Lock()
        self.model: Optional[SpeakerRecognition] = None
        self.user_voice_profile: Optional[np.ndarray] = None
        self.user_voice_profile_path = user_voice_profile_path
        self.similarity_threshold = 0.7  # Adjust based on testing
        self.last_speaker_was_user: Optional[bool] = None  # Track last detected speaker
        self._initialize_model()
        self._load_user_profile()
    
    def _initialize_model(self):
        """Initialize the SpeechBrain speaker recognition model"""
        try:
            logger.info("Loading SpeechBrain speaker recognition model...")
            self.model = SpeakerRecognition.from_hparams(
                source="speechbrain/spkrec-ecapa-voxceleb",
                savedir="pretrained_models/spkrec"
            )
            logger.info("Speaker recognition model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load speaker recognition model: {e}")
            raise
    
    def _load_user_profile(self):
        """Load user's voice profile if it exists"""
        if os.path.exists(self.user_voice_profile_path):
            try:
                self.user_voice_profile = np.load(self.user_voice_profile_path)
                logger.info("User voice profile loaded successfully")
            except Exception as e:
                logger.error(f"Failed to load user voice profile: {e}")
        else:
            logger.info("No user voice profile found. Please enroll your voice first.")
    
    def enroll_user_voice(self, audio_data: np.ndarray, sample_rate: int = 16000) -> bool:
        """
        Enroll user's voice by creating a voice profile from audio data
        
        Args:
            audio_data: Audio data as numpy array
            sample_rate: Sample rate of the audio
            
        Returns:
            bool: True if enrollment was successful
        """
        try:
            with self._lock:
                if self.model is None:
                    logger.error("Speaker recognition model not initialized")
                    return False
                
                # Save audio to temporary file for processing
                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                    sf.write(temp_file.name, audio_data, sample_rate)
                    temp_path = temp_file.name
                
                try:
                    # Extract speaker embeddings
                    embeddings = self.model.encode_batch(torch.tensor(audio_data).unsqueeze(0))
                    
                    # Store the embeddings as user profile
                    self.user_voice_profile = embeddings.squeeze().cpu().numpy()
                    
                    # Save to file
                    np.save(self.user_voice_profile_path, self.user_voice_profile)
                    
                    logger.info("User voice enrolled successfully")
                    return True
                    
                finally:
                    # Clean up temporary file
                    if os.path.exists(temp_path):
                        os.unlink(temp_path)
                        
        except Exception as e:
            logger.error(f"Failed to enroll user voice: {e}")
            return False
    
    def is_user_speaking(self, audio_data: np.ndarray, sample_rate: int = 16000) -> SpeakerResult:
        """
        Determine if the audio contains the user's voice
        
        Args:
            audio_data: Audio data as numpy array
            sample_rate: Sample rate of the audio
            
        Returns:
            SpeakerResult: Result containing whether it's the user and confidence
        """
        try:
            with self._lock:
                if self.model is None:
                    logger.error("Speaker recognition model not initialized")
                    return SpeakerResult(False, 0.0, 0.0, datetime.now())
                
                if self.user_voice_profile is None:
                    logger.warning("No user voice profile available. Please enroll first.")
                    return SpeakerResult(False, 0.0, 0.0, datetime.now())
                
                # Ensure audio is long enough for speaker recognition (minimum ~1 second)
                min_samples = sample_rate * 1  # 1 second
                if len(audio_data) < min_samples:
                    # Pad with zeros if too short
                    audio_data = np.pad(audio_data, (0, min_samples - len(audio_data)), 'constant')
                
                # Extract embeddings from current audio
                current_embeddings = self.model.encode_batch(torch.tensor(audio_data).unsqueeze(0))
                current_embeddings = current_embeddings.squeeze().cpu().numpy()
                
                # Calculate similarity with user profile
                similarity_score = self._calculate_similarity(self.user_voice_profile, current_embeddings)
                
                # Determine if it's the user based on threshold
                is_user = similarity_score > self.similarity_threshold
                confidence = min(similarity_score / self.similarity_threshold, 1.0) if is_user else similarity_score
                
                # Update last speaker tracking
                self.last_speaker_was_user = is_user
                
                return SpeakerResult(
                    is_user=is_user,
                    confidence=confidence,
                    similarity_score=similarity_score,
                    timestamp=datetime.now()
                )
                
        except Exception as e:
            logger.error(f"Failed to perform speaker recognition: {e}")
            return SpeakerResult(False, 0.0, 0.0, datetime.now())
    
    def _calculate_similarity(self, profile1: np.ndarray, profile2: np.ndarray) -> float:
        """Calculate cosine similarity between two speaker profiles"""
        try:
            # Normalize vectors
            profile1_norm = profile1 / np.linalg.norm(profile1)
            profile2_norm = profile2 / np.linalg.norm(profile2)
            
            # Calculate cosine similarity
            similarity = np.dot(profile1_norm, profile2_norm)
            
            # Convert to positive scale (0-1)
            return (similarity + 1) / 2
            
        except Exception as e:
            logger.error(f"Failed to calculate similarity: {e}")
            return 0.0
    
    def has_user_profile(self) -> bool:
        """Check if user voice profile exists"""
        return self.user_voice_profile is not None
    
    def delete_user_profile(self):
        """Delete the stored user voice profile"""
        with self._lock:
            self.user_voice_profile = None
            if os.path.exists(self.user_voice_profile_path):
                os.remove(self.user_voice_profile_path)
                logger.info("User voice profile deleted")
    
    def set_similarity_threshold(self, threshold: float):
        """Set the similarity threshold for speaker recognition"""
        if 0.0 <= threshold <= 1.0:
            self.similarity_threshold = threshold
            logger.info(f"Similarity threshold set to {threshold}")
        else:
            logger.error("Threshold must be between 0.0 and 1.0")
    
    def get_last_speaker_was_user(self) -> Optional[bool]:
        """Get whether the last detected speaker was the user"""
        with self._lock:
            return self.last_speaker_was_user


# Global service instance
speaker_service = SpeakerService()
