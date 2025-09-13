#!/usr/bin/env python3
"""
Simple Speaker Recognition Test

This script tests if the speaker recognition model can identify your voice.
It records audio in real-time and shows whether it recognizes you or not.
"""

import logging
import time
import numpy as np
import sounddevice as sd
from services.speaker_service import speaker_service

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def record_and_test_continuously(sample_rate: int = 16000, chunk_duration: float = 3.0):
    """
    Continuously record audio chunks and test speaker recognition
    
    Args:
        sample_rate: Audio sample rate
        chunk_duration: Length of each test chunk in seconds
    """
    
    chunk_samples = int(chunk_duration * sample_rate)
    
    logger.info("🎤 Starting continuous speaker recognition test...")
    logger.info(f"Recording {chunk_duration}-second chunks at {sample_rate}Hz")
    logger.info("Speak into your microphone. Press Ctrl+C to stop.")
    logger.info("-" * 50)
    
    try:
        while True:
            # Record a chunk of audio
            print(f"🔴 Recording {chunk_duration} seconds...")
            audio_chunk = sd.rec(
                frames=chunk_samples,
                samplerate=sample_rate,
                channels=1,
                dtype=np.float32
            )
            
            # Wait for recording to complete
            sd.wait()
            
            # Flatten the audio data
            audio_data = audio_chunk.flatten()
            
            # Test speaker recognition
            result = speaker_service.is_user_speaking(audio_data, sample_rate)
            
            # Display results
            if result.is_user:
                status = "✅ YOU"
                confidence_bar = "█" * int(result.confidence * 10)
            else:
                status = "❌ OTHER"
                confidence_bar = "▒" * int(result.confidence * 10)
            
            print(f"{status} | Confidence: {result.confidence:.1%} [{confidence_bar:>10}] | Similarity: {result.similarity_score:.3f}")
            
            # Small delay before next recording
            time.sleep(0.5)
            
    except KeyboardInterrupt:
        logger.info("\n✋ Test stopped by user.")


def single_test(duration: float = 5.0, sample_rate: int = 16000):
    """
    Record once and test speaker recognition
    
    Args:
        duration: Recording duration in seconds
        sample_rate: Audio sample rate
    """
    
    logger.info("🎤 Single Speaker Recognition Test")
    logger.info(f"Please speak for {duration} seconds...")
    logger.info("Starting in 3 seconds...")
    time.sleep(3)
    
    logger.info("🔴 RECORDING NOW - Please speak!")
    
    # Record audio
    audio_data = sd.rec(
        frames=int(duration * sample_rate),
        samplerate=sample_rate,
        channels=1,
        dtype=np.float32
    )
    
    # Wait for recording to complete
    sd.wait()
    
    logger.info("✅ Recording complete! Processing...")
    
    # Test speaker recognition
    audio_data = audio_data.flatten()
    result = speaker_service.is_user_speaking(audio_data, sample_rate)
    
    # Display detailed results
    print("\n" + "="*50)
    print("SPEAKER RECOGNITION RESULTS")
    print("="*50)
    print(f"Is User Speaking: {'✅ YES' if result.is_user else '❌ NO'}")
    print(f"Confidence: {result.confidence:.1%}")
    print(f"Similarity Score: {result.similarity_score:.3f}")
    print(f"Timestamp: {result.timestamp}")
    print("="*50)


def main():
    """Main test function"""
    
    print("🎯 Speaker Recognition Test Tool")
    print("="*40)
    
    # Check if user has enrolled their voice
    if not speaker_service.has_user_profile():
        logger.error("❌ No user voice profile found!")
        logger.info("Please run 'python enroll_voice.py' first to enroll your voice.")
        return
    
    logger.info("✅ User voice profile found!")
    logger.info(f"Current similarity threshold: {speaker_service.similarity_threshold:.2f}")
    
    print("\nChoose test mode:")
    print("1. Single test (record once)")
    print("2. Continuous test (keep recording)")
    print("3. Quit")
    
    try:
        choice = input("\nEnter choice (1-3): ").strip()
        
        if choice == "1":
            print("\n--- Single Test Mode ---")
            single_test(duration=5.0)
            
        elif choice == "2":
            print("\n--- Continuous Test Mode ---")
            record_and_test_continuously()
            
        elif choice == "3":
            logger.info("Goodbye! 👋")
            
        else:
            logger.error("Invalid choice. Please enter 1, 2, or 3.")
            
    except KeyboardInterrupt:
        logger.info("\nTest interrupted by user.")
    except Exception as e:
        logger.error(f"Error during test: {e}")


if __name__ == "__main__":
    main()
