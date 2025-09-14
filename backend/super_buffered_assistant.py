import os
import time
import threading
import queue
import io
from typing import Iterator
from dotenv import load_dotenv
import pygame

# Import our components
from generate import generate_streaming_response
from elevenlabs import ElevenLabs
import assemblyai as aai
from assemblyai.streaming.v3 import *

load_dotenv()

class SuperBufferedVoiceAssistant:
    def __init__(self):
        # Initialize API keys
        self.assemblyai_key = os.getenv("ASSEMBLYAI_API_KEY")
        self.cerebras_key = os.getenv("CEREBRAS_API_KEY")
        self.elevenlabs_key = os.getenv("ELEVENLABS_API_KEY")

        # Initialize ElevenLabs client
        self.tts_client = ElevenLabs(api_key=self.elevenlabs_key)

        # Voice settings
        self.voice_id = "WHIyRN9WblX9JzVlTL97"  # Harvey Specter voice

        # State management
        self.is_speaking = False
        self.conversation_active = True

        # Audio setup with different settings
        pygame.mixer.init(frequency=22050, size=-16, channels=1, buffer=4096)

        # Communication queues
        self.speech_queue = queue.Queue()

        # System prompt
        self.system_prompt = """You are Steve Harvey, the famous comedian and Family Feud host.
        Respond with your characteristic humor, wisdom, and personality.
        Use your catchphrases occasionally like 'Survey says...' or 'Family Feud!'
        Keep responses conversational and entertaining, but not overly long.
        Be encouraging and positive like the real Steve Harvey."""

    def stream_ai_to_voice_super_buffered(self, user_input: str):
        """Ultra-conservative buffered approach - collect multiple words before speaking"""
        print(f"🧠 AI processing: {user_input}")

        self.is_speaking = True

        try:
            print("🤖 AI speaking (super buffered)...")

            # Collect words in groups of 3-5 before sending to TTS
            word_buffer = []
            word_count = 0

            for word_chunk in generate_streaming_response(user_input, self.system_prompt):
                if not self.conversation_active:
                    break

                if word_chunk.strip():
                    word_buffer.append(word_chunk.strip())
                    word_count += 1

                    # When we have 3-4 words, send them as a group
                    if len(word_buffer) >= 3 or word_count > 50:  # Also send if near end
                        phrase = " ".join(word_buffer) + " "
                        print(f"🎤 Speaking phrase: '{phrase.strip()}'")

                        # Generate and play this phrase completely
                        self.play_phrase_completely(phrase)

                        # Clear buffer for next group
                        word_buffer = []

            # Handle any remaining words
            if word_buffer and self.conversation_active:
                phrase = " ".join(word_buffer)
                print(f"🎤 Speaking final phrase: '{phrase.strip()}'")
                self.play_phrase_completely(phrase)

            print("✅ Finished speaking all phrases")

        except Exception as e:
            print(f"❌ TTS streaming error: {e}")
        finally:
            self.is_speaking = False

    def play_phrase_completely(self, phrase: str):
        """Play a complete phrase and wait for it to finish entirely"""
        try:
            # Generate audio for the complete phrase
            audio_stream = self.tts_client.text_to_speech.stream(
                voice_id=self.voice_id,
                text=phrase,
                model_id="eleven_monolingual_v1",
                output_format="mp3_22050_32",  # Lower quality for faster processing
                optimize_streaming_latency=3,
                voice_settings=None
            )

            # Collect all audio chunks for this phrase
            audio_chunks = []
            for chunk in audio_stream:
                if not self.conversation_active:
                    break
                audio_chunks.append(chunk)

            if audio_chunks and self.conversation_active:
                # Combine all chunks into one audio file
                audio_data = b"".join(audio_chunks)
                audio_buffer = io.BytesIO(audio_data)

                # Play the complete phrase
                pygame.mixer.music.load(audio_buffer)
                pygame.mixer.music.play()

                # Wait for it to finish COMPLETELY
                while pygame.mixer.music.get_busy():
                    time.sleep(0.1)
                    if not self.conversation_active:
                        pygame.mixer.music.stop()
                        break

                # Extra buffer time to be absolutely sure
                time.sleep(0.5)  # Half second buffer between phrases

                print(f"✅ Phrase completed: '{phrase.strip()}'")

        except Exception as e:
            print(f"❌ Error playing phrase: {e}")
            time.sleep(0.3)  # Buffer even on error

    def start_speech_recognition(self):
        """Start continuous speech recognition"""
        print("🎤 Starting speech recognition...")

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

        # Setup AssemblyAI streaming client
        client = StreamingClient(
            StreamingClientOptions(
                api_key=self.assemblyai_key,
                api_host="streaming.assemblyai.com",
            )
        )

        client.on(StreamingEvents.Turn, on_turn)

        try:
            client.connect(
                StreamingParameters(
                    sample_rate=16000,
                    format_turns=True,
                    end_utterance_silence_timeout=1500,
                )
            )

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
                user_text = self.speech_queue.get(timeout=1.0)
                if not self.conversation_active:
                    break

                # Stream AI response with super buffering
                self.stream_ai_to_voice_super_buffered(user_text)

            except queue.Empty:
                continue
            except Exception as e:
                print(f"❌ Error in conversation loop: {e}")

    def start_conversation(self):
        """Start the super buffered voice assistant"""
        print("\n" + "="*60)
        print("🚀 PersonifAI - Super Buffered Voice Assistant")
        print("="*60)
        print("💡 This version uses phrase-based buffering for cleaner audio")
        print("💡 Say 'quit', 'exit', or 'stop' to end conversation")
        print("="*60)

        # Give a greeting
        threading.Thread(
            target=self.stream_ai_to_voice_super_buffered,
            args=("Hey there! It's your boy Steve Harvey! What's going on?",),
            daemon=True
        ).start()

        time.sleep(3)

        # Start components in separate threads
        threads = []

        speech_thread = threading.Thread(
            target=self.start_speech_recognition,
            daemon=True
        )
        threads.append(speech_thread)

        conversation_thread = threading.Thread(
            target=self.process_conversation_loop,
            daemon=True
        )
        threads.append(conversation_thread)

        for thread in threads:
            thread.start()

        try:
            while self.conversation_active:
                time.sleep(0.1)
        except KeyboardInterrupt:
            print("\n⛔ Interrupted by user")
        finally:
            print("\n🛑 Shutting down voice assistant...")
            self.conversation_active = False
            pygame.mixer.quit()

if __name__ == "__main__":
    assistant = SuperBufferedVoiceAssistant()
    assistant.start_conversation()