import threading
import numpy as np
import queue
import time
from typing import Callable, Optional
from dataclasses import dataclass
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class AudioChunk:
    data: np.ndarray
    timestamp: datetime
    duration_seconds: float
    sample_rate: int


class AudioChunkingService:
    """Service to buffer and chunk audio data for speaker recognition"""
    
    def __init__(self, 
                 chunk_duration_seconds: float = 3.0,
                 overlap_seconds: float = 1.0,
                 sample_rate: int = 16000,
                 max_buffer_seconds: float = 30.0):
        """
        Initialize audio chunking service
        
        Args:
            chunk_duration_seconds: Duration of each audio chunk
            overlap_seconds: Overlap between consecutive chunks
            sample_rate: Audio sample rate
            max_buffer_seconds: Maximum duration to keep in buffer
        """
        self.chunk_duration_seconds = chunk_duration_seconds
        self.overlap_seconds = overlap_seconds
        self.sample_rate = sample_rate
        self.max_buffer_seconds = max_buffer_seconds
        
        # Calculate sizes in samples
        self.chunk_size_samples = int(chunk_duration_seconds * sample_rate)
        self.overlap_samples = int(overlap_seconds * sample_rate)
        self.max_buffer_samples = int(max_buffer_seconds * sample_rate)
        
        # Threading and buffering
        self._lock = threading.Lock()
        self._audio_buffer = np.array([], dtype=np.float32)
        self._chunk_queue = queue.Queue(maxsize=50)
        self._is_running = False
        self._processing_thread: Optional[threading.Thread] = None
        
        # Callbacks
        self._chunk_callback: Optional[Callable[[AudioChunk], None]] = None
        
        logger.info(f"AudioChunkingService initialized: chunk_duration={chunk_duration_seconds}s, "
                   f"overlap={overlap_seconds}s, sample_rate={sample_rate}Hz")
    
    def set_chunk_callback(self, callback: Callable[[AudioChunk], None]):
        """Set callback function to be called when a new chunk is ready"""
        self._chunk_callback = callback
    
    def start(self):
        """Start the audio chunking service"""
        with self._lock:
            if self._is_running:
                logger.warning("Audio chunking service is already running")
                return
            
            self._is_running = True
            self._processing_thread = threading.Thread(target=self._processing_loop, daemon=True)
            self._processing_thread.start()
            logger.info("Audio chunking service started")
    
    def stop(self):
        """Stop the audio chunking service"""
        with self._lock:
            if not self._is_running:
                return
            
            self._is_running = False
        
        if self._processing_thread:
            self._processing_thread.join(timeout=2.0)
        
        logger.info("Audio chunking service stopped")
    
    def add_audio_data(self, audio_data: np.ndarray):
        """
        Add new audio data to the buffer
        
        Args:
            audio_data: Audio data as numpy array (float32, mono)
        """
        if not self._is_running:
            return
        
        try:
            # Ensure audio data is float32
            if audio_data.dtype != np.float32:
                audio_data = audio_data.astype(np.float32)
            
            # Ensure mono audio
            if audio_data.ndim > 1:
                audio_data = np.mean(audio_data, axis=1)
            
            with self._lock:
                # Add new data to buffer
                self._audio_buffer = np.concatenate([self._audio_buffer, audio_data])
                
                # Trim buffer if it's too long
                if len(self._audio_buffer) > self.max_buffer_samples:
                    excess_samples = len(self._audio_buffer) - self.max_buffer_samples
                    self._audio_buffer = self._audio_buffer[excess_samples:]
                
                # Check if we have enough data for a chunk
                if len(self._audio_buffer) >= self.chunk_size_samples:
                    self._try_create_chunk()
                    
        except Exception as e:
            logger.error(f"Error adding audio data: {e}")
    
    def _try_create_chunk(self):
        """Try to create a new audio chunk from the buffer (called with lock held)"""
        try:
            if len(self._audio_buffer) < self.chunk_size_samples:
                return
            
            # Extract chunk data
            chunk_data = self._audio_buffer[:self.chunk_size_samples].copy()
            
            # Remove processed data (keeping overlap)
            samples_to_remove = self.chunk_size_samples - self.overlap_samples
            self._audio_buffer = self._audio_buffer[samples_to_remove:]
            
            # Create chunk object
            chunk = AudioChunk(
                data=chunk_data,
                timestamp=datetime.now(),
                duration_seconds=self.chunk_duration_seconds,
                sample_rate=self.sample_rate
            )
            
            # Add to processing queue
            try:
                self._chunk_queue.put_nowait(chunk)
            except queue.Full:
                logger.warning("Chunk queue is full, dropping oldest chunk")
                try:
                    self._chunk_queue.get_nowait()  # Remove oldest
                    self._chunk_queue.put_nowait(chunk)  # Add new
                except queue.Empty:
                    pass
                    
        except Exception as e:
            logger.error(f"Error creating audio chunk: {e}")
    
    def _processing_loop(self):
        """Main processing loop that handles chunk callbacks"""
        logger.info("Audio chunk processing loop started")
        
        while self._is_running:
            try:
                # Get chunk from queue with timeout
                chunk = self._chunk_queue.get(timeout=0.1)
                
                # Call the callback if set
                if self._chunk_callback:
                    try:
                        self._chunk_callback(chunk)
                    except Exception as e:
                        logger.error(f"Error in chunk callback: {e}")
                
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Error in processing loop: {e}")
                time.sleep(0.1)
        
        logger.info("Audio chunk processing loop stopped")
    
    def get_buffer_info(self) -> dict:
        """Get information about the current buffer state"""
        with self._lock:
            return {
                "buffer_size_samples": len(self._audio_buffer),
                "buffer_duration_seconds": len(self._audio_buffer) / self.sample_rate,
                "queue_size": self._chunk_queue.qsize(),
                "is_running": self._is_running
            }
    
    def clear_buffer(self):
        """Clear the audio buffer"""
        with self._lock:
            self._audio_buffer = np.array([], dtype=np.float32)
            # Clear the queue
            while not self._chunk_queue.empty():
                try:
                    self._chunk_queue.get_nowait()
                except queue.Empty:
                    break
        logger.info("Audio buffer cleared")


# Global service instance
audio_chunking_service = AudioChunkingService()
