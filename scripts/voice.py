import os
from elevenlabs import ElevenLabs

api_key = os.getenv("ELEVENLABS_API_KEY")
# Initialize client
client = ElevenLabs(api_key=api_key)

# Simple TTS test
audio_stream = client.text_to_speech.convert(
    voice_id="WHIyRN9WblX9JzVlTL97", 
    text="I don’t play the odds, I play the man. Winning isn’t about luck—it’s about being the one who refuses to lose. If you’re waiting for permission to be great, you’ve already lost.",
    model_id="eleven_monolingual_v1"
)

# Convert stream to bytes
audio_bytes = b"".join(audio_stream)

# Save to file
with open("output.mp3", "wb") as f:
    f.write(audio_bytes)
