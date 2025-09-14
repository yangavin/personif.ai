import logging
import os
import numpy as np
import threading
import time

import assemblyai as aai
from assemblyai.streaming.v3 import (
    StreamingClient,
    StreamingClientOptions,
    StreamingEvents,
    StreamingParameters,
)
from dotenv import load_dotenv

from services.transcript_service import transcript_service
from services.audio_chunking_service import audio_chunking_service
from services.speaker_service import speaker_service

load_dotenv()

api_key = os.getenv("ASSEMBLYAI_API_KEY")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DualAudioStream:
    """Custom audio stream that sends data to both AssemblyAI and speaker recognition"""
    
    def __init__(self, sample_rate: int = 16000):
        self.sample_rate = sample_rate
        self.mic_stream = aai.extras.MicrophoneStream(sample_rate=sample_rate)
        self._running = False
        
    def __iter__(self):
        """Iterator interface for AssemblyAI streaming"""
        self._running = True
        
        for audio_data in self.mic_stream:
            if not self._running:
                break
                
            # COMMENTED OUT: Send to audio chunking service for speaker recognition
            # try:
            #     # Convert bytes to numpy array for chunking service
            #     audio_array = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32768.0
            #     audio_chunking_service.add_audio_data(audio_array)
            # except Exception as e:
            #     logger.error(f"Error sending audio to chunking service: {e}")
            pass  # Disabled speaker recognition
            
            # Send to AssemblyAI
            yield audio_data
    
    def stop(self):
        """Stop the audio stream"""
        self._running = False


def speaker_recognition_callback(chunk):
    """Callback function to handle speaker recognition results"""
    try:
        # Perform speaker recognition on the chunk
        result = speaker_service.is_user_speaking(chunk.data, chunk.sample_rate)
        
        # Display results in real-time
        if result.is_user:
            status = "🟢 YOU"
            confidence_bar = "█" * int(result.confidence * 10)
        else:
            status = "🔴 OTHER"
            confidence_bar = "▒" * int(result.confidence * 10)
        
        print(f"[SPEAKER] {status} | Confidence: {result.confidence:.1%} [{confidence_bar:>10}] | Similarity: {result.similarity_score:.3f}")
        
    except Exception as e:
        logger.error(f"Error in speaker recognition callback: {e}")


def main():
    """Main function to start streaming with speaker recognition"""
    
    # Check if user has enrolled their voice
    # if not speaker_service.has_user_profile():
    #     logger.error("❌ No user voice profile found!")
    #     logger.info("Please run 'python enroll_voice.py' first to enroll your voice.")
    #     return
    
    # logger.info("✅ User voice profile found!")
    # logger.info("🎯 Starting dual audio streaming: AssemblyAI transcription + Speaker recognition")
    
    # # Configure audio chunking for speaker recognition (3-second chunks)
    # audio_chunking_service.chunk_duration_seconds = 3.0
    # audio_chunking_service.overlap_seconds = 1.0
    
    # # Set up speaker recognition callback
    # audio_chunking_service.set_chunk_callback(speaker_recognition_callback)
    # audio_chunking_service.start()
    
    # Set up AssemblyAI client
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
            min_end_of_turn_silence_when_confident=600,
        )
    )

    # Create dual audio stream
    dual_stream = DualAudioStream(sample_rate=16000)

    try:
        logger.info("🎤 Streaming started! You'll see:")
        logger.info("  • [SPEAKER] lines showing real-time speaker recognition")
        logger.info("  • Transcript lines showing AssemblyAI transcription")
        logger.info("  • Press Ctrl+C to stop")
        print("-" * 80)
        
        client.stream(dual_stream)
        
    except KeyboardInterrupt:
        logger.info("🛑 Stopping audio stream...")
        dual_stream.stop()
    finally:
        # Clean up
        # audio_chunking_service.stop()
        client.disconnect(terminate=True)
        logger.info("✅ Cleanup complete")

if __name__ == "__main__":
    main()