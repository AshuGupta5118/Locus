import requests
import json
import sounddevice as sd
import wavio
import numpy as np # Often required by sounddevice/wavio
import subprocess
import os
import platform
import time

# --- Configuration ---
# Adjust these paths based on your project structure and downloaded models!
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__)) # Gets the directory where the script is
WHISPER_CPP_DIR = os.path.join(PROJECT_ROOT, "whisper.cpp")
WHISPER_EXECUTABLE = os.path.join(WHISPER_CPP_DIR, "main")
WHISPER_MODEL = os.path.join(WHISPER_CPP_DIR, "models/ggml-base.en.bin") # Ensure this model file exists

PIPER_TTS_DIR = os.path.join(PROJECT_ROOT, "piper-tts")
PIPER_EXECUTABLE = os.path.join(PIPER_TTS_DIR, "piper")
PIPER_MODEL = os.path.join(PIPER_TTS_DIR, "en_US-lessac-medium.onnx") # Ensure this .onnx file exists
# Piper also needs the .onnx.json file in the same directory, but we only specify the .onnx in the command

OLLAMA_API_URL = "http://localhost:11434/api/chat"
OLLAMA_MODEL = "llama3:8b" # Model you pulled with 'ollama pull'

RECORDING_FILENAME = os.path.join(PROJECT_ROOT, "temp_input.wav")
TTS_OUTPUT_FILENAME = os.path.join(PROJECT_ROOT, "temp_output.wav")
SAMPLE_RATE = 16000 # Whisper works well with 16kHz
RECORDING_DURATION = 5 # Duration in seconds to record audio

# --- Conversation History ---
conversation_history = []
MAX_HISTORY_MESSAGES = 10 # Keep the last N messages (user + assistant)

# --- Helper Functions ---

def record_audio(filename=RECORDING_FILENAME, duration=RECORDING_DURATION, fs=SAMPLE_RATE):
    """Records audio from the default input device."""
    print(f"Recording for {duration} seconds...")
    try:
        # Record audio using sounddevice
        recording = sd.rec(int(duration * fs), samplerate=fs, channels=1, dtype='int16')
        sd.wait() # Wait until recording is finished

        # Save audio to WAV file using wavio
        wavio.write(filename, recording, fs, sampwidth=2) # sampwidth=2 for 16-bit
        print(f"Recording saved to {filename}")
        return True
    except Exception as e:
        print(f"Error during recording: {e}")
        return False

def transcribe_audio_whisper_cpp(audio_path=RECORDING_FILENAME):
    """Transcribes audio using the whisper.cpp command-line tool."""
    print("Transcribing audio...")
    if not os.path.exists(WHISPER_EXECUTABLE):
        print(f"Error: Whisper executable not found at {WHISPER_EXECUTABLE}")
        return None
    if not os.path.exists(WHISPER_MODEL):
        print(f"Error: Whisper model not found at {WHISPER_MODEL}")
        return None
    if not os.path.exists(audio_path):
        print(f"Error: Audio file not found at {audio_path}")
        return None

    command = [
        WHISPER_EXECUTABLE,
        "-m", WHISPER_MODEL,
        "-f", audio_path,
        "-otxt", # Output transcription to a .txt file
        "-nt", # No timestamps
        "--language", "en" # Specify language
    ]
    try:
        # Run whisper.cpp, wait for it to complete
        process = subprocess.run(command, check=True, capture_output=True, text=True, cwd=WHISPER_CPP_DIR)
        print("Whisper.cpp ran successfully.")

        # Expected output text file path
        transcription_file_path = audio_path + ".txt"

        if os.path.exists(transcription_file_path):
            with open(transcription_file_path, 'r', encoding='utf-8') as f:
                transcription = f.read().strip()
            os.remove(transcription_file_path) # Clean up the text file
            # Sometimes whisper adds [..] annotations, remove them
            transcription = transcription.replace("[SOUND]", "").replace("[MUSIC]", "").strip()
            print(f"Transcription: {transcription}")
            return transcription
        else:
            print(f"Error: Transcription file '{transcription_file_path}' not found after running Whisper.")
            print(f"Whisper stdout: {process.stdout}")
            print(f"Whisper stderr: {process.stderr}")
            return None

    except subprocess.CalledProcessError as e:
        print(f"Whisper.cpp failed:")
        print(f"Command: {' '.join(e.cmd)}")
        print(f"Return code: {e.returncode}")
        print(f"Stderr: {e.stderr}")
        print(f"Stdout: {e.stdout}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred during transcription: {e}")
        return None


def get_ollama_response(history):
    """Sends conversation history to Ollama and gets a response."""
    print("Sending request to Ollama...")
    try:
        payload = {
            "model": OLLAMA_MODEL,
            "messages": history,
            "stream": False # Get the full response at once
        }
        response = requests.post(OLLAMA_API_URL, json=payload, timeout=90) # Increased timeout
        response.raise_for_status() # Raise an exception for bad status codes (4xx or 5xx)

        response_data = response.json()

        # Extract the actual message content
        if 'message' in response_data and 'content' in response_data['message']:
            assistant_message = response_data['message']['content']
            print(f"Ollama Response: {assistant_message}")
            return assistant_message
        else:
            print(f"Error: Unexpected response format from Ollama: {response_data}")
            return None

    except requests.exceptions.RequestException as e:
        print(f"Error connecting to Ollama API at {OLLAMA_API_URL}: {e}")
        print("Is the Ollama service running?")
        return None
    except Exception as e:
        print(f"An unexpected error occurred communicating with Ollama: {e}")
        return None


def text_to_speech_piper(text, output_filename=TTS_OUTPUT_FILENAME):
    """Converts text to speech using the Piper TTS command-line tool."""
    print("Generating speech...")
    if not os.path.exists(PIPER_EXECUTABLE):
        print(f"Error: Piper executable not found at {PIPER_EXECUTABLE}")
        return False
    if not os.path.exists(PIPER_MODEL):
        print(f"Error: Piper model not found at {PIPER_MODEL}")
        return False
    if not os.path.exists(PIPER_MODEL + ".json"):
        print(f"Error: Piper model config (.json) not found next to {PIPER_MODEL}")
        return False

    # Command using echo and pipe (requires shell=True, use cautiously)
    # Ensure 'text' doesn't contain characters that break the shell command.
    # Basic sanitization: replace double quotes with single quotes for the echo command.
    sanitized_text = text.replace('"', "'")
    command = f'echo "{sanitized_text}" | "{PIPER_EXECUTABLE}" --model "{PIPER_MODEL}" --output_file "{output_filename}"'

    try:
        # Run Piper TTS command using shell=True because of the pipe (|)
        process = subprocess.run(command, shell=True, check=True, capture_output=True, text=True, cwd=PIPER_TTS_DIR)
        print(f"Speech saved to {output_filename}")
        print(f"Piper stdout: {process.stdout}") # Piper might output logs here
        print(f"Piper stderr: {process.stderr}") # Errors usually go here
        return True
    except subprocess.CalledProcessError as e:
        print(f"Piper TTS failed:")
        print(f"Command: {command}") # Show the command run via shell
        print(f"Return code: {e.returncode}")
        print(f"Stderr: {e.stderr}")
        print(f"Stdout: {e.stdout}")
        return False
    except Exception as e:
        print(f"An unexpected error occurred during TTS: {e}")
        return False


def play_audio(filename=TTS_OUTPUT_FILENAME):
    """Plays an audio file using platform-specific command-line tools."""
    print("Playing response...")
    if not os.path.exists(filename):
        print(f"Error: Audio file not found at {filename}")
        return

    system = platform.system()
    try:
        if system == "Linux":
            # Try 'aplay' first (common) or 'play' (from sox)
            try:
                subprocess.run(["aplay", filename], check=True, capture_output=True)
            except FileNotFoundError:
                print("'aplay' not found, trying 'play' (requires SoX: sudo apt install sox)")
                subprocess.run(["play", filename], check=True, capture_output=True)
        elif system == "Darwin": # macOS
            subprocess.run(["afplay", filename], check=True, capture_output=True)
        elif system == "Windows":
            # Windows playback is more complex via subprocess.
            # Using 'start' might work but is non-blocking.
            # Consider installing 'playsound' library: pip install playsound
            # Then use:
            try:
                 from playsound import playsound
                 playsound(filename)
            except ImportError:
                 print("Windows playback: 'playsound' library not found.")
                 print("Attempting with system 'start' (might open default player)...")
                 os.startfile(filename) # Non-blocking, might open a media player window
            except Exception as ps_error:
                print(f"Playsound error: {ps_error}")
                print("Trying os.startfile as fallback...")
                os.startfile(filename)

        else:
            print(f"Unsupported OS for automatic audio playback: {system}")

        # Optional: Clean up the TTS file after playing
        # time.sleep(1) # Give playback a moment
        # try:
        #     os.remove(filename)
        # except OSError as e:
        #     print(f"Warning: Could not remove temp TTS file {filename}: {e}")

    except FileNotFoundError as e:
        print(f"Error: Audio playback command not found. Is the player installed?")
        print(f"Missing command details: {e}")
    except subprocess.CalledProcessError as e:
        print(f"Audio playback failed:")
        print(f"Command: {' '.join(e.cmd)}")
        print(f"Return code: {e.returncode}")
        print(f"Stderr: {e.stderr}")
    except Exception as e:
        print(f"An unexpected error occurred during audio playback: {e}")


# --- Main Loop ---
if __name__ == "__main__":
    # Optional: Add an initial system prompt to guide the assistant's behavior
    # conversation_history.append({"role": "system", "content": "You are a helpful voice assistant. Keep responses concise."})

    print("Local Voice Assistant - Ready!")
    print("Press Enter to start recording, then speak.")
    print("Say 'goodbye' to exit.")

    while True:
        input("Press Enter to record...") # Simple trigger

        if not record_audio():
            print("Skipping turn due to recording error.")
            continue # Skip to next loop iteration

        user_text = transcribe_audio_whisper_cpp()

        if user_text:
            # Check for exit command
            if user_text.lower().strip() == "goodbye":
                print("Assistant: Goodbye!")
                farewell_text = "Goodbye!"
                if text_to_speech_piper(farewell_text):
                    play_audio()
                break # Exit the loop

            # Add user message to history
            conversation_history.append({"role": "user", "content": user_text})

            # Limit history length (keep only the last N messages)
            if len(conversation_history) > MAX_HISTORY_MESSAGES:
                # Keep the optional system prompt plus the last N user/assistant messages
                start_index = 1 if conversation_history[0].get("role") == "system" else 0
                conversation_history = conversation_history[:start_index] + conversation_history[-MAX_HISTORY_MESSAGES:]


            # Get response from Ollama
            assistant_response = get_ollama_response(conversation_history)

            if assistant_response:
                # Add assistant response to history
                conversation_history.append({"role": "assistant", "content": assistant_response})

                # Generate and play speech
                if text_to_speech_piper(assistant_response):
                    play_audio()
                else:
                    print("Skipping playback due to TTS error.")
            else:
                print("Assistant: Sorry, I couldn't get a response from the language model.")
                # Optionally add an error message to history or handle differently

        else:
            print("Could not transcribe audio clearly. Please try again.")
            # Don't add anything to history if transcription failed

    print("Exiting assistant.")
