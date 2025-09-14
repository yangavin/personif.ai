import os
import time
import threading
import queue
import io
from typing import Iterator, Optional
from dotenv import load_dotenv
import pygame

# Import our components
from generate import generate_streaming_response
from elevenlabs import ElevenLabs, VoiceSettings
import assemblyai as aai
from assemblyai.streaming.v3 import (
    BeginEvent,
    StreamingClient,
    StreamingClientOptions,
    StreamingError,
    StreamingEvents,
    StreamingParameters,
    TerminationEvent,
    TurnEvent,
)

load_dotenv()

class RealtimeVoiceAssistant:
    def __init__(self):
        # Initialize API keys
        self.assemblyai_key = os.getenv("ASSEMBLYAI_API_KEY")
        self.cerebras_key = os.getenv("CEREBRAS_API_KEY")
        self.elevenlabs_key = os.getenv("ELEVENLABS_API_KEY")

        # Initialize ElevenLabs client
        self.tts_client = ElevenLabs(api_key=self.elevenlabs_key)

        # Voice settings
        self.voice_id = "WHIyRN9WblX9JzVlTL97"  # Your custom voice

        # State management
        self.is_listening = True
        self.is_speaking = False
        self.conversation_active = True

        # Audio setup
        pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=1024)

        # Communication queues
        self.speech_queue = queue.Queue()

        # Voice settings for Steve Harvey-like sound
        self.voice_settings = VoiceSettings(
            stability=0.8,        # Higher stability for consistent Steve Harvey voice
            similarity_boost=0.9,  # High similarity to original voice clone
            style=0.3,            # Moderate style for personality
            use_speaker_boost=True # Enhanced speaker characteristics
        )

        # System prompt for Steve Harvey personality
        self.system_prompt = """You are Steve Harvey, the famous comedian and Family Feud host.
        Respond with your characteristic humor, wisdom, and personality.
        Use your catchphrases occasionally like 'Survey says...' or 'Family Feud!'
        Keep responses conversational and entertaining, but not overly long.
        Be encouraging and positive like the real Steve Harvey."""

    def stream_ai_to_voice_realtime(self, user_input: str):
        """Stream AI response directly to voice as it generates - original method"""
        print(f"🧠 AI processing: {user_input}")

        self.is_speaking = True

        def ai_word_generator():
            """Generate words from Cerebras AI - simple, no buffers"""
            try:
                for word_chunk in generate_streaming_response(user_input, self.system_prompt):
                    if word_chunk.strip():
                        yield word_chunk.strip() + " "
            except Exception as e:
                print(f"❌ AI generation error: {e}")
                yield "Sorry, I encountered an error generating a response. "

        try:
            print("🤖 AI speaking (original streaming)...")

            # Use ElevenLabs realtime streaming - original method
            audio_stream = self.tts_client.text_to_speech.convert_realtime(
                voice_id=self.voice_id,
                text=ai_word_generator(),
                model_id="eleven_monolingual_v1",
                output_format="mp3_44100_128",
                voice_settings=None
            )

            # Stream and play audio chunks - original simple method
            chunk_count = 0
            for audio_chunk in audio_stream:
                if not self.conversation_active:
                    break

                chunk_count += 1
                print(f"🔊 Playing chunk {chunk_count} ({len(audio_chunk)} bytes)")

                # Create an in-memory file-like object
                audio_buffer = io.BytesIO(audio_chunk)

                # Load and play the audio chunk - simple, no extra delays
                try:
                    pygame.mixer.music.load(audio_buffer)
                    pygame.mixer.music.play()

                    # Wait for the chunk to finish playing - basic method
                    while pygame.mixer.music.get_busy():
                        time.sleep(0.01)
                        if not self.conversation_active:
                            pygame.mixer.music.stop()
                            break

                except pygame.error as e:
                    print(f"🔊 Audio playback error: {e}")
                    continue

            print(f"✅ Finished speaking ({chunk_count} chunks)")

        except Exception as e:
            print(f"❌ TTS streaming error: {e}")
        finally:
            self.is_speaking = False

    def start_speech_recognition(self):
        """Start continuous speech recognition"""
        print("🎤 Starting speech recognition...")

        def on_begin(client: StreamingClient, event: BeginEvent):
            print(f"📡 Speech session started")

        def on_turn(client: StreamingClient, event: TurnEvent):
            if event.end_of_turn and event.transcript.strip():
                user_text = event.transcript.strip()
                print(f"👤 You: {user_text}")

                # Check for exit commands
                if user_text.lower() in ['quit', 'exit', 'stop', 'goodbye', 'bye']:
                    print("👋 Ending conversation...")
                    self.conversation_active = False
                    return

                # Only process if AI isn't currently speaking
                if not self.is_speaking and self.conversation_active:
                    self.speech_queue.put(user_text)

        def on_terminated(client: StreamingClient, event: TerminationEvent):
            print(f"📡 Speech session ended")

        def on_error(client: StreamingClient, error: StreamingError):
            print(f"❌ Speech recognition error: {error}")

        # Setup AssemblyAI streaming client
        client = StreamingClient(
            StreamingClientOptions(
                api_key=self.assemblyai_key,
                api_host="streaming.assemblyai.com",
            )
        )

        client.on(StreamingEvents.Begin, on_begin)
        client.on(StreamingEvents.Turn, on_turn)
        client.on(StreamingEvents.Termination, on_terminated)
        client.on(StreamingEvents.Error, on_error)

        try:
            client.connect(
                StreamingParameters(
                    sample_rate=16000,
                    format_turns=True,
                    end_utterance_silence_timeout=1500,  # 1.5 seconds silence to end turn
                )
            )

            # Start streaming from microphone
            print("🎤 Listening... (speak naturally)")
            client.stream(aai.extras.MicrophoneStream(sample_rate=16000))

        except Exception as e:
            print(f"❌ Failed to start speech recognition: {e}")
            self.conversation_active = False
        finally:
            try:
                client.disconnect(terminate=True)
            except:
                pass

    def process_conversation_loop(self):
        """Main conversation processing loop"""
        print("💭 Starting conversation processor...")

        while self.conversation_active:
            try:
                # Wait for user speech
                user_text = self.speech_queue.get(timeout=1.0)

                if not self.conversation_active:
                    break

                # Stream AI response directly to voice in real-time
                self.stream_ai_to_voice_realtime(user_text)

            except queue.Empty:
                continue
            except Exception as e:
                print(f"❌ Error in conversation loop: {e}")

    def start_conversation(self):
        """Start the complete real-time voice-to-voice conversation"""
        print("\n" + "="*60)
        print("🚀 PersonifAI - Real-time Voice Assistant")
        print("="*60)
        print("💡 Speak naturally - I'll respond in real-time!")
        print("💡 Say 'quit', 'exit', or 'stop' to end conversation")
        print("💡 Wait for me to finish speaking before your next question")
        print("="*60)

        # Give a Steve Harvey greeting
        threading.Thread(
            target=self.stream_ai_to_voice_realtime,
            args=("Hey there! It's your boy Steve Harvey! What's going on? What do you want to talk about today?",),
            daemon=True
        ).start()

        time.sleep(2)  # Let greeting start

        # Start components in separate threads
        threads = []

        # Speech recognition thread
        speech_thread = threading.Thread(
            target=self.start_speech_recognition,
            daemon=True
        )
        threads.append(speech_thread)

        # Conversation processing thread
        conversation_thread = threading.Thread(
            target=self.process_conversation_loop,
            daemon=True
        )
        threads.append(conversation_thread)

        # Start all threads
        for thread in threads:
            thread.start()

        try:
            # Keep main thread alive and monitor
            while self.conversation_active:
                time.sleep(0.1)
        except KeyboardInterrupt:
            print("\n⛔ Interrupted by user")
        finally:
            print("\n🛑 Shutting down voice assistant...")
            self.conversation_active = False
            pygame.mixer.quit()

if __name__ == "__main__":
    assistant = RealtimeVoiceAssistant()
    assistant.start_conversation()