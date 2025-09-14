import os
from typing import Iterator
from cerebras.cloud.sdk import Cerebras
from dotenv import load_dotenv

load_dotenv()

# Initialize Cerebras client with environment variable
client = Cerebras(api_key=os.getenv("CEREBRAS_API_KEY"))


def generate_response(user_input: str, system_prompt: str = None) -> str:
    """Generate a single response from Cerebras AI"""

    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})

    messages.append({"role": "user", "content": user_input})

    try:
        chat_completion = client.chat.completions.create(
            messages=messages,
            model="llama-4-scout-17b-16e-instruct",
            temperature=0.7,
            max_tokens=1024,
        )
        return chat_completion.choices[0].message.content
    except Exception as e:
        return f"Error generating response: {e}"


def generate_streaming_response(
    user_input: str, system_prompt: str = None
) -> Iterator[str]:
    """Generate a streaming response from Cerebras AI - yields words as they come"""

    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})

    messages.append({"role": "user", "content": user_input})

    try:
        stream = client.chat.completions.create(
            messages=messages,
            model="llama-4-scout-17b-16e-instruct",
            temperature=0.7,
            max_tokens=1024,
            stream=True,  # Enable streaming
        )

        # Stream response word by word
        current_content = ""
        for chunk in stream:
            if chunk.choices[0].delta.content:
                delta_content = chunk.choices[0].delta.content
                current_content += delta_content

                # Yield complete words when we hit a space
                words = current_content.split(" ")
                if len(words) > 1:
                    # Yield all complete words except the last (incomplete) one
                    for word in words[:-1]:
                        if word.strip():
                            yield word + " "
                    current_content = words[-1]  # Keep the incomplete word

        # Yield any remaining content
        if current_content.strip():
            yield current_content

    except Exception as e:
        yield f"Error: {e}"


def chat_session():
    """Interactive chat session with Cerebras AI"""

    print("Cerebras AI Chat Session")
    print("Type 'quit' to exit, 'stream' to toggle streaming mode")
    print("-" * 50)

    streaming_mode = False
    system_prompt = (
        "You are a helpful, conversational AI assistant. Be concise but informative."
    )

    while True:
        user_input = input("\nYou: ").strip()

        if user_input.lower() in ["quit", "exit", "q"]:
            print("Goodbye!")
            break

        if user_input.lower() == "stream":
            streaming_mode = not streaming_mode
            print(f"Streaming mode: {'ON' if streaming_mode else 'OFF'}")
            continue

        if user_input.lower() == "clear":
            os.system("cls" if os.name == "nt" else "clear")
            continue

        if not user_input:
            continue

        print("\nAI: ", end="", flush=True)

        if streaming_mode:
            # Stream response word by word
            for word_chunk in generate_streaming_response(user_input, system_prompt):
                print(word_chunk, end="", flush=True)
            print()  # New line after streaming
        else:
            # Get complete response at once
            response = generate_response(user_input, system_prompt)
            print(response)


if __name__ == "__main__":
    chat_session()
