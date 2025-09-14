import os
import time
import threading
import json
import io
from typing import Iterator, List, Dict
from dotenv import load_dotenv
import pygame

# Import our components
from generate import generate_streaming_response
from elevenlabs import ElevenLabs, VoiceSettings

load_dotenv()

class JsonVoiceAssistant:
    def __init__(self, conversation_file: str = "conversation.json"):
        # Initialize API keys
        self.cerebras_key = os.getenv("CEREBRAS_API_KEY")
        self.elevenlabs_key = os.getenv("ELEVENLABS_API_KEY")

        # Initialize ElevenLabs client
        self.tts_client = ElevenLabs(api_key=self.elevenlabs_key)

        # Voice settings
        self.voice_id = "WHIyRN9WblX9JzVlTL97"  # Harvey Specter voice

        # Voice settings with speed control for Harvey Specter (set to SLOW)
        self.voice_settings = VoiceSettings(
            stability=0.9,        # Higher stability for slow, clear speech
            similarity_boost=0.85, # High similarity to original voice clone
            style=0.2,            # Lower style for slower, more deliberate speech
            use_speaker_boost=True # Enhanced speaker characteristics
        )

        # Speed control options
        self.speaking_speed = "normal"  # Options: "slow", "normal", "fast"

        # State management
        self.is_speaking = False
        self.conversation_active = True

        # Audio setup
        pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=1024)

        # Conversation data
        self.conversation_file = conversation_file
        self.conversation_data: List[Dict[str, str]] = []
        self.current_index = 0

        # System prompt for Harvey Specter personality
        self.system_prompt = """You are Harvey Specter from the TV show Suits.
        Respond with your characteristic confidence, wit, and legal expertise.
        Use your catchphrases and maintain your sophisticated, winning personality.
        Keep responses conversational and engaging."""

    def load_conversation(self) -> bool:
        """Load conversation from JSON file"""
        try:
            with open(self.conversation_file, 'r', encoding='utf-8') as f:
                self.conversation_data = json.load(f)
            print(f"✅ Loaded {len(self.conversation_data)} conversation entries")
            return True
        except FileNotFoundError:
            print(f"❌ Conversation file '{self.conversation_file}' not found")
            return False
        except json.JSONDecodeError as e:
            print(f"❌ Invalid JSON format: {e}")
            return False
        except Exception as e:
            print(f"❌ Error loading conversation: {e}")
            return False

    def get_next_entry(self) -> Dict[str, str]:
        """Get the next conversation entry"""
        if self.current_index < len(self.conversation_data):
            entry = self.conversation_data[self.current_index]
            self.current_index += 1
            return entry
        return None

    def stream_ai_to_voice_realtime(self, user_input: str):
        """Stream AI response directly to voice as it generates - original method"""
        print(f"🧠 AI processing: {user_input}")

        self.is_speaking = True

        def ai_word_generator():
            """Generate words from Cerebras AI with speed control"""
            try:
                for word_chunk in generate_streaming_response(user_input, self.system_prompt):
                    if word_chunk.strip():
                        yield word_chunk.strip() + " "
                        # Add delay based on speed setting
                        if self.speaking_speed == "slow":
                            time.sleep(0.2)  # 200ms delay for slow speech
                        elif self.speaking_speed == "normal":
                            time.sleep(0.05)  # 50ms delay for normal speech
                        elif self.speaking_speed == "fast":
                            time.sleep(0.01)  # 10ms delay for fast speech
            except Exception as e:
                print(f"❌ AI generation error: {e}")
                yield "Sorry, I encountered an error generating a response. "

        try:
            print("🤖 Harvey speaking (original streaming)...")

            # Use ElevenLabs realtime streaming with voice settings for speed control
            audio_stream = self.tts_client.text_to_speech.convert_realtime(
                voice_id=self.voice_id,
                text=ai_word_generator(),
                model_id="eleven_monolingual_v1",
                output_format="mp3_44100_128",
                voice_settings=self.voice_settings
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

    def process_json_conversation(self):
        """Process the JSON conversation entries"""
        print("🎬 Starting JSON conversation processor...")

        while self.conversation_active and self.current_index < len(self.conversation_data):
            try:
                # Get next conversation entry
                entry = self.get_next_entry()
                if not entry:
                    print("📝 End of conversation reached")
                    break

                # Process based on entry type
                if "You" in entry:
                    user_text = entry["You"]
                    print(f"👤 You: {user_text}")

                    # Wait a moment before processing (simulating natural conversation)
                    time.sleep(1.0)

                    # Process through AI and speak the response
                    if self.conversation_active:
                        self.stream_ai_to_voice_realtime(user_text)

                    # Wait for Harvey to finish speaking before next entry
                    while self.is_speaking and self.conversation_active:
                        time.sleep(0.1)

                    # Pause between conversation turns
                    time.sleep(2.0)

                elif "Other" in entry:
                    other_text = entry["Other"]
                    print(f"👥 Other: {other_text}")

                    # For "Other" entries, we could either:
                    # Option 1: Skip them (since Harvey is responding to "You")
                    # Option 2: Use them as context or have a different voice speak them
                    # For now, let's skip them since Harvey responds to "You" entries

                    print("⏭️  Skipping 'Other' entry (Harvey will generate his own response)")
                    continue

                else:
                    print(f"❌ Unknown entry format: {entry}")
                    continue

            except Exception as e:
                print(f"❌ Error processing conversation: {e}")
                break

        print("🏁 JSON conversation completed")
        self.conversation_active = False

    def start_conversation(self):
        """Start the JSON-driven voice conversation"""
        print("\n" + "="*60)
        print("🎬 PersonifAI - JSON Conversation Mode")
        print("="*60)
        print("📖 Reading conversation from JSON file")
        print("🎤 Harvey will respond to each 'You' entry")
        print(f"🎛️ Speaking speed: {self.speaking_speed}")
        print("="*60)

        # Load the conversation file
        if not self.load_conversation():
            print("❌ Failed to load conversation. Exiting...")
            return

        # Start the conversation processing
        conversation_thread = threading.Thread(
            target=self.process_json_conversation,
            daemon=True
        )
        conversation_thread.start()

        try:
            # Keep main thread alive
            while self.conversation_active:
                time.sleep(0.1)
        except KeyboardInterrupt:
            print("\n⛔ Interrupted by user")
        finally:
            print("\n🛑 Shutting down JSON voice assistant...")
            self.conversation_active = False
            pygame.mixer.quit()

if __name__ == "__main__":
    # You can specify a different conversation file
    import sys
    conversation_file = sys.argv[1] if len(sys.argv) > 1 else "conversation.json"

    assistant = JsonVoiceAssistant(conversation_file)
    assistant.start_conversation()