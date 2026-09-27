import asyncio
import os
import tempfile

import edge_tts
import pygame
from colorama import Fore, Style, init
from dotenv import load_dotenv
from groq import Groq

load_dotenv()
init(autoreset=True)

API_KEY = os.getenv("GROQ_API_KEY")
MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")
TTS_VOICE = os.getenv("TTS_VOICE", "en-US-AriaNeural")
MAX_HISTORY_MESSAGES = 12

if not API_KEY:
    raise RuntimeError("GROQ_API_KEY is missing. Add it to your .env file.")

client = Groq(api_key=API_KEY)

SYSTEM_PROMPT = """
You are a helpful AI voice assistant.
Answer clearly and naturally.
Keep responses concise unless the user asks for more detail.
"""

messages = [{"role": "system", "content": SYSTEM_PROMPT}]


def print_header():
    print(Fore.CYAN + Style.BRIGHT + "\n" + "=" * 58)
    print("             AI / LLM VOICE ASSISTANT")
    print("=" * 58 + Style.RESET_ALL)


def generate_response(user_text: str) -> str:
    messages.append({"role": "user", "content": user_text})

    if len(messages) > MAX_HISTORY_MESSAGES + 1:
        del messages[1:2]

    response = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        temperature=0.7,
    )

    answer = response.choices[0].message.content.strip()
    messages.append({"role": "assistant", "content": answer})
    return answer


async def synthesize_speech(text: str, output_path: str):
    communicator = edge_tts.Communicate(text, TTS_VOICE)
    await communicator.save(output_path)


def speak(text: str):
    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as audio_file:
        audio_path = audio_file.name

    try:
        asyncio.run(synthesize_speech(text, audio_path))
        pygame.mixer.init()
        pygame.mixer.music.load(audio_path)
        pygame.mixer.music.play()

        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)

        pygame.mixer.quit()
    finally:
        if os.path.exists(audio_path):
            os.remove(audio_path)


def main():
    print_header()
    print(Fore.WHITE + "Type 'exit' or 'quit' to stop.\n")

    while True:
        try:
            user_text = input(Fore.BLUE + "You > " + Style.RESET_ALL).strip()

            if not user_text:
                continue

            if user_text.lower() in {"exit", "quit", "bye"}:
                print(Fore.CYAN + "Goodbye!")
                break

            print(Fore.YELLOW + "Thinking...")
            answer = generate_response(user_text)

            print(Fore.GREEN + f"Assistant > {answer}")
            print(Fore.MAGENTA + "Speaking...")

            speak(answer)

        except KeyboardInterrupt:
            print(Fore.CYAN + "\nGoodbye!")
            break
        except Exception as exc:
            print(Fore.RED + f"Error: {exc}")


if __name__ == "__main__":
    main()
