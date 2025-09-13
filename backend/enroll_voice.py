#!/usr/bin/env python3
"""
Voice Enrollment Script

This script helps you record and enroll your voice for speaker recognition.
Run this script and speak for 10-15 seconds to create your voice profile.
"""

import logging
import time
import numpy as np
import sounddevice as sd
from services.speaker_service import speaker_service

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def record_voice_sample(duration_seconds: int = 15, sample_rate: int = 16000) -> np.ndarray:
    """
    Record audio from microphone for voice enrollment
    
    Args:
        duration_seconds: How long to record
        sample_rate: Audio sample rate
        
    Returns:
        numpy array with recorded audio
    """
    logger.info(f"Recording voice sample for {duration_seconds} seconds...")
    logger.info("Please speak clearly into your microphone. Say something like:")
    logger.info("'Hello, this is my voice for speaker recognition. I am enrolling my voice profile.'")
    logger.info("Starting recording in 3 seconds...")
    
    time.sleep(3)
    
    logger.info("🎤 RECORDING NOW - Please speak...")
    
    # Record audio
    audio_data = sd.rec(
        frames=duration_seconds * sample_rate,
        samplerate=sample_rate,
        channels=1,
        dtype=np.float32
    )
    
    # Wait for recording to complete
    sd.wait()
    
    logger.info("✅ Recording complete!")
    
    # Return flattened audio data
    return audio_data.flatten()


def main():
    """Main enrollment function"""
    try:
        logger.info("=== Voice Enrollment for Speaker Recognition ===")
        logger.info("This will record your voice and create a speaker profile.")
        
        # Check if user profile already exists
        if speaker_service.has_user_profile():
            response = input("A voice profile already exists. Do you want to replace it? (y/N): ")
            if response.lower() != 'y':
                logger.info("Enrollment cancelled.")
                return
            
            # Delete existing profile
            speaker_service.delete_user_profile()
            logger.info("Existing voice profile deleted.")
        
        # Record voice sample
        audio_data = record_voice_sample(duration_seconds=15)
        
        # Enroll the voice
        logger.info("Processing voice sample for enrollment...")
        success = speaker_service.enroll_user_voice(audio_data, sample_rate=16000)
        
        if success:
            logger.info("🎉 Voice enrollment successful!")
            logger.info("Your voice profile has been saved and speaker recognition is now ready.")
            logger.info("You can now run the main application and it will detect when you're speaking.")
        else:
            logger.error("❌ Voice enrollment failed. Please try again.")
            
    except KeyboardInterrupt:
        logger.info("\nEnrollment cancelled by user.")
    except Exception as e:
        logger.error(f"Error during voice enrollment: {e}")


if __name__ == "__main__":
    main()
