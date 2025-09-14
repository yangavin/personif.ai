import os
import time
import io
from typing import Iterator
from elevenlabs import ElevenLabs
from dotenv import load_dotenv
import pygame

load_dotenv()

api_key = os.getenv("ELEVENLABS_API_KEY")
client = ElevenLabs(api_key=api_key)

def get_available_voices():
    """Get list of available voices"""
    try:
        voices = client.voices.get_all()
        return voices.voices
    except Exception as e:
        print(f"Error getting voices: {e}")
        return []

def list_voices():
    """List available voices for selection"""
    voices = get_available_voices()
    if voices:
        print("\nAvailable voices:")
        for i, voice in enumerate(voices, 1):
            print(f"{i}. {voice.name} (ID: {voice.voice_id})")
        return voices
    return []

def text_to_word_iterator(text: str) -> Iterator[str]:
    """Split text into words and yield them one by one"""
    words = text.split()
    for word in words:
        yield word + " "  # Add space back
        time.sleep(0.1)  # Small delay between words (adjust as needed)

def stream_text_word_by_word(text: str, voice_id: str = "WHIyRN9WblX9JzVlTL97"):
    """Stream text to speech word by word using ElevenLabs realtime streaming"""

    # Use convert_realtime for word-by-word streaming
    audio_stream = client.text_to_speech.convert_realtime(
        voice_id=voice_id,
        text=text_to_word_iterator(text),
        model_id="eleven_monolingual_v1",
        output_format="mp3_44100_128",
        voice_settings=None  # Fix for ellipsis bug
    )

    # Initialize pygame mixer for audio playback
    pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=1024)

    # Stream and play audio chunks
    chunk_count = 0
    for audio_chunk in audio_stream:
        chunk_count += 1
        print(f"Playing audio chunk {chunk_count} ({len(audio_chunk)} bytes)")

        # Create an in-memory file-like object
        audio_buffer = io.BytesIO(audio_chunk)

        # Load and play the audio chunk
        try:
            pygame.mixer.music.load(audio_buffer)
            pygame.mixer.music.play()

            # Wait for the chunk to finish playing
            while pygame.mixer.music.get_busy():
                time.sleep(0.01)

        except pygame.error as e:
            print(f"Audio playback error: {e}")
            continue

    print(f"Streaming complete! Played {chunk_count} audio chunks.")

def stream_text_simple(text: str, voice_id: str = "WHIyRN9WblX9JzVlTL97"):
    """Simple streaming - entire text at once but streamed audio playback"""

    audio_stream = client.text_to_speech.stream(
        voice_id=voice_id,
        text=text,
        model_id="eleven_monolingual_v1",
        output_format="mp3_44100_128",
        optimize_streaming_latency=3  # Max latency optimization
    )

    # Initialize pygame mixer
    pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=1024)

    # Collect all chunks and play
    audio_chunks = []
    for chunk in audio_stream:
        audio_chunks.append(chunk)

    # Combine chunks and play
    audio_data = b"".join(audio_chunks)
    audio_buffer = io.BytesIO(audio_data)

    try:
        pygame.mixer.music.load(audio_buffer)
        pygame.mixer.music.play()

        while pygame.mixer.music.get_busy():
            time.sleep(0.1)

    except pygame.error as e:
        print(f"Audio playback error: {e}")

def save_streaming_audio(text: str, filename: str = "streaming_output.mp3", voice_id: str = "WHIyRN9WblX9JzVlTL97"):
    """Save streamed audio to file"""

    audio_stream = client.text_to_speech.stream(
        voice_id=voice_id,
        text=text,
        model_id="eleven_monolingual_v1",
        output_format="mp3_44100_128"
    )

    with open(filename, "wb") as f:
        for chunk in audio_stream:
            f.write(chunk)

    print(f"Audio saved to {filename}")

if __name__ == "__main__":
    test_text = "I don't play the odds, I play the man. Winning isn't about luck—it's about being the one who refuses to lose. If you're waiting for permission to be great, you've already lost."

    print("Choose streaming method:")
    print("1. Word-by-word realtime streaming")
    print("2. Simple streaming with immediate playback")
    print("3. Save to file")
    print("4. List available voices")

    choice = input("Enter choice (1-4): ")

    # Default voice (Your custom voice)
    selected_voice_id = "WHIyRN9WblX9JzVlTL97"

    if choice == "1":
        print("Streaming word by word...")
        stream_text_word_by_word(test_text, voice_id=selected_voice_id)
    elif choice == "2":
        print("Simple streaming...")
        stream_text_simple(test_text, voice_id=selected_voice_id)
    elif choice == "3":
        save_streaming_audio(test_text, voice_id=selected_voice_id)
    elif choice == "4":
        voices = list_voices()
        if voices:
            try:
                voice_choice = int(input("\nEnter voice number: ")) - 1
                if 0 <= voice_choice < len(voices):
                    selected_voice_id = voices[voice_choice].voice_id
                    print(f"Selected voice: {voices[voice_choice].name}")

                    # Ask for streaming method again
                    print("\nChoose streaming method:")
                    print("1. Word-by-word realtime streaming")
                    print("2. Simple streaming with immediate playback")
                    print("3. Save to file")

                    method_choice = input("Enter choice (1-3): ")
                    if method_choice == "1":
                        stream_text_word_by_word(test_text, voice_id=selected_voice_id)
                    elif method_choice == "2":
                        stream_text_simple(test_text, voice_id=selected_voice_id)
                    elif method_choice == "3":
                        save_streaming_audio(test_text, voice_id=selected_voice_id)
                else:
                    print("Invalid voice selection")
            except ValueError:
                print("Invalid input")
    else:
        print("Invalid choice")
