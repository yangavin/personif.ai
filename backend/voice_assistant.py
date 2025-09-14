import os
import time
import threading
import queue
from typing import Iterator, Optional
from dotenv import load_dotenv

# Import our components
from generate import generate_streaming_response
from voice import stream_text_word_by_word
import assemblyai as aai
from assemblyai.streaming.v3 import (
    BeginEvent,
    StreamingClient,
    StreamingClientOptions,
    StreamingError,
    StreamingEvents,
    StreamingParameters,
    StreamingSessionParameters,
    TerminationEvent,
    TurnEvent,
)

load_dotenv()

class VoiceAssistant:
    def __init__(self):
        # Initialize API keys
        self.assemblyai_key = os.getenv("ASSEMBLYAI_API_KEY")
        self.cerebras_key = os.getenv("CEREBRAS_API_KEY")
        self.elevenlabs_key = os.getenv("ELEVENLABS_API_KEY")

        # Voice settings
        self.voice_id = "WHIyRN9WblX9JzVlTL97"  # Your custom voice

        # State management
        self.is_listening = False
        self.is_speaking = False
        self.conversation_active = True

        # Communication queues
        self.speech_queue = queue.Queue()
        self.response_queue = queue.Queue()

        # System prompt for AI personality
        self.system_prompt = """You are a helpful, conversational AI assistant.
        Keep responses concise and natural for voice conversation.
        Respond as if you're having a friendly chat."""

    def start_speech_recognition(self):
        """Start continuous speech recognition"""
        print("🎤 Starting speech recognition...")

        def on_begin(client: StreamingClient, event: BeginEvent):
            print(f"📡 Speech session started: {event.id}")

        def on_turn(client: StreamingClient, event: TurnEvent):
            if event.end_of_turn and event.transcript.strip():
                user_text = event.transcript.strip()
                print(f"👤 You said: {user_text}")

                # Add to queue for processing
                if not self.is_speaking:  # Only process if AI isn't currently speaking
                    self.speech_queue.put(user_text)

        def on_terminated(client: StreamingClient, event: TerminationEvent):
            print(f"📡 Speech session ended: {event.audio_duration_seconds}s processed")

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
                    end_utterance_silence_timeout=1000,  # 1 second silence to end turn
                )
            )

            # Start streaming from microphone
            client.stream(aai.extras.MicrophoneStream(sample_rate=16000))

        except Exception as e:
            print(f"❌ Failed to start speech recognition: {e}")
        finally:
            client.disconnect(terminate=True)

    def process_speech_to_response(self):
        """Process speech input and generate AI responses"""
        print("🧠 Starting AI response processor...")

        while self.conversation_active:
            try:
                # Wait for user speech
                user_text = self.speech_queue.get(timeout=1.0)

                if user_text.lower() in ['quit', 'exit', 'stop', 'goodbye']:
                    print("👋 Ending conversation...")
                    self.conversation_active = False
                    break

                print(f"🧠 AI thinking about: {user_text}")

                # Generate streaming response from Cerebras
                ai_response = ""
                for word_chunk in generate_streaming_response(user_text, self.system_prompt):
                    ai_response += word_chunk

                print(f"🤖 AI response: {ai_response}")

                # Send to TTS queue
                self.response_queue.put(ai_response)

            except queue.Empty:
                continue
            except Exception as e:
                print(f"❌ Error processing speech: {e}")

    def text_to_speech_handler(self):
        """Handle text-to-speech conversion and playback"""
        print("🔊 Starting text-to-speech handler...")

        while self.conversation_active:
            try:
                # Wait for AI response
                response_text = self.response_queue.get(timeout=1.0)

                print("🔊 Speaking response...")
                self.is_speaking = True

                # Use our streaming TTS function
                stream_text_word_by_word(response_text, self.voice_id)

                self.is_speaking = False
                print("✅ Finished speaking")

            except queue.Empty:
                continue
            except Exception as e:
                print(f"❌ Error in text-to-speech: {e}")
                self.is_speaking = False

    def start_conversation(self):
        """Start the complete voice-to-voice conversation pipeline"""
        print("🚀 Starting PersonifAI Voice Assistant...")
        print("=" * 50)
        print("💡 Say something to start the conversation!")
        print("💡 Say 'quit', 'exit', or 'stop' to end")
        print("=" * 50)

        # Start all components in separate threads
        threads = []

        # Speech recognition thread
        speech_thread = threading.Thread(
            target=self.start_speech_recognition,
            daemon=True
        )
        threads.append(speech_thread)

        # AI processing thread
        ai_thread = threading.Thread(
            target=self.process_speech_to_response,
            daemon=True
        )
        threads.append(ai_thread)

        # Text-to-speech thread
        tts_thread = threading.Thread(
            target=self.text_to_speech_handler,
            daemon=True
        )
        threads.append(tts_thread)

        # Start all threads
        for thread in threads:
            thread.start()

        try:
            # Keep main thread alive
            while self.conversation_active:
                time.sleep(0.1)
        except KeyboardInterrupt:
            print("\n⛔ Interrupted by user")
        finally:
            print("🛑 Shutting down voice assistant...")
            self.conversation_active = False

if __name__ == "__main__":
    assistant = VoiceAssistant()
    assistant.start_conversation()