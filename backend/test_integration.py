#!/usr/bin/env python3
"""
Test script to verify the JSONBin integration with the voice assistant.
This script demonstrates how the system now works with personifications.
"""

import os
import json
from dotenv import load_dotenv
from services.jsonbin_service import jsonbin_service
from json_voice_assistant import JsonVoiceAssistant

load_dotenv()


def test_jsonbin_integration():
    """Test the JSONBin integration"""
    print("🧪 Testing JSONBin Integration")
    print("=" * 50)

    # Test 1: Fetch personifications data
    print("1. Fetching personifications data...")
    try:
        data = jsonbin_service.get_personifications_data()
        print(
            f"   ✅ Success! Found {len(data.get('personifications', []))} personifications"
        )
        print(f"   ✅ Active choice: {data.get('choice', 'None')}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return

    # Test 2: Get active personification
    print("\n2. Getting active personification...")
    try:
        active = jsonbin_service.get_active_personification()
        if active:
            print(f"   ✅ Active personification: {active.get('name', 'Unknown')}")
            print(f"   ✅ Voice ID: {active.get('elevenLabsId', 'Default')}")
        else:
            print("   ℹ️ No active personification set")
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return

    # Test 3: Create voice assistant with transcription data
    print("\n3. Testing voice assistant creation...")
    try:
        # Load sample transcription data
        sample_transcription = [
            {"you": "Hello, how are you today?"},
            {"other": "I'm doing great, thank you for asking!"},
        ]

        # Create voice assistant
        assistant = JsonVoiceAssistant(
            conversation_data=sample_transcription, personification_data=active
        )

        print("   ✅ Voice assistant created successfully!")
        print(f"   ✅ Using voice ID: {assistant.voice_id}")
        print(f"   ✅ System prompt length: {len(assistant.system_prompt)} characters")

    except Exception as e:
        print(f"   ❌ Error creating voice assistant: {e}")
        return

    print("\n🎉 All tests passed! The integration is working correctly.")
    print("\nNext steps:")
    print("1. Set up your .env file with JSONBIN_API_KEY and JSONBIN_BIN_ID")
    print("2. Run 'python main.py' to start the voice assistant")
    print("3. The system will now use the active personification from JSONBin!")


if __name__ == "__main__":
    test_jsonbin_integration()
