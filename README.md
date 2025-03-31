# Locus - Local Voice Assistant

![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
<!-- Optional: Add build status, etc. later -->

A simple, privacy-focused voice assistant that runs entirely on your local machine using Ollama, Whisper.cpp, and Piper TTS. No cloud dependencies for core functionality.

<!-- Optional: Add a GIF or Screenshot Here -->
<!-- ![Demo GIF](docs/demo.gif) -->

## Key Features

*   **🗣️ Voice Interaction:** Speak commands and hear responses naturally.
*   **🧠 LLM Powered:** Uses local large language models via [Ollama](https://ollama.com/) (e.g., Llama 3, Mistral).
*   **👂 Local Speech-to-Text:** Fast and accurate transcription using [Whisper.cpp](https://github.com/ggerganov/whisper.cpp).
*   **🔊 Local Text-to-Speech:** Natural voice synthesis using [Piper TTS](https://github.com/rhasspy/piper).
*   **💬 Conversation History:** Remembers the context of your chat.
*   **🔒 Privacy Focused:** Your conversations stay on your machine.
*   **🔧 Customizable:** Easily change LLM models, voices, prompts, etc.

## Core Technologies

*   [Python 3](https://www.python.org/)
*   [Ollama](https://ollama.com/)
*   [Whisper.cpp](https://github.com/ggerganov/whisper.cpp)
*   [Piper TTS](https://github.com/rhasspy/piper)
*   [SoundDevice](https://python-sounddevice.readthedocs.io/) (Audio I/O)
*   [Wavio](https://github.com/WarrenWeckesser/wavio) (WAV file handling)

## Prerequisites

Before you begin, ensure you have the following installed:

1.  **Python:** Version 3.8 or higher. ([Download](https://www.python.org/downloads/))
2.  **Git:** For cloning this repository. ([Download](https://git-scm.com/downloads))
3.  **Ollama:** Installed and running. ([Download & Setup](https://youtu.be/tG0QwQxicgo?si=olsrFoJhZ4XBtpor))
    *   Make sure you have pulled an LLM model: `ollama pull llama3:8b` (or another model specified in `assistant.py`)
4.  **Build Tools (for Whisper.cpp):**
    *   **Linux (Debian/Ubuntu):** `sudo apt update && sudo apt install build-essential git`
    *   **macOS:** Install Xcode Command Line Tools: `xcode-select --install` (Git is usually included).
    *   **Windows:** Install Build Tools for Visual Studio (with C++ workload) or use WSL (Windows Subsystem for Linux).

5.  **Audio Playback Tool (Optional but helpful for testing/some OS):**
    *   **Linux:** `sox` (`sudo apt install sox`) or ensure `aplay` (usually part of `alsa-utils`) is available.
    *   **macOS:** `afplay` is built-in.
    *   **Windows:** Script attempts `playsound` library or `os.startfile`. Installing `sox` via package managers like Chocolatey might provide `play.exe`.

## Setup Instructions

1.  **Clone the Repository:**
    ```bash
    git clone https://github.com/AshuGupta5118/Locus.git
    cd Locus
    ```

2.  **Create Python Virtual Environment (Recommended):**
    ```bash
    python -m venv venv
    # Activate the environment:
    # Linux/macOS:
    source venv/bin/activate
    # Windows (Command Prompt):
    # venv\Scripts\activate.bat
    # Windows (PowerShell):
    # .\venv\Scripts\Activate.ps1
    ```

3.  **Install Python Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
    *(We will create `requirements.txt` in a later step)*

4.  **Set up Whisper.cpp:**
    *   This will clone Whisper.cpp *inside* your `Locus` project folder.
    ```bash
    git clone https://github.com/ggerganov/whisper.cpp.git whisper.cpp
    cd whisper.cpp
    ```
    *   Compile Whisper.cpp:
    ```bash
    make
    # For potential speedups on specific hardware, check whisper.cpp docs (e.g., make LLAMA_CUBLAS=1 for Nvidia)
    ```
    *   Download a Whisper model (e.g., `base.en`):
    ```bash
    bash ./models/download-ggml-model.sh base.en
    ```
    *   Return to the project root:
    ```bash
    cd ..
    ```

5.  **Set up Piper TTS:**
    *   Create the directory: `mkdir piper-tts`
    *   Go to [Piper TTS Releases](https://github.com/rhasspy/piper/releases) and download the appropriate binary archive for your OS into the `piper-tts` folder.
    *   Extract the archive within the `piper-tts` folder. You should have a `piper` executable (or `piper.exe`).
    *   **(Linux/macOS):** Make it executable: `chmod +x piper-tts/piper`
    *   Go to [Piper Voices on Hugging Face](https://huggingface.co/rhasspy/piper-voices/tree/main).
    *   Download a voice model: Get *both* the `.onnx` file and the `.onnx.json` file for your chosen voice (e.g., `en_US-lessac-medium`).
    *   Place *both* downloaded voice files directly into the `piper-tts` folder.

6.  **Configuration:**
    *   Open `assistant.py` in a text editor.
    *   **CRITICAL:** Verify the paths in the `Configuration` section (`WHISPER_EXECUTABLE`, `WHISPER_MODEL`, `PIPER_EXECUTABLE`, `PIPER_MODEL`, etc.) match your local setup exactly.
    *   Adjust `OLLAMA_MODEL` if you pulled a different model.
    *   Change `RECORDING_DURATION` if needed.

## Running the Assistant

1.  **Ensure Ollama is running** in the background.
2.  **Activate your virtual environment** (`source venv/bin/activate` or equivalent).
3.  Run the main script from the `Locus` directory:
    ```bash
    python assistant.py
    ```

## Usage

*   The script will prompt you to "Press Enter to record...".
*   Press Enter, then speak your command or question clearly for the configured duration.
*   Wait for the transcription, LLM response, and spoken audio playback.
*   Say "goodbye" to exit the assistant.

## Project Structure

Here's the layout of the project directory after following the setup instructions. Items marked `(*)` are typically ignored by Git and managed locally.

```plaintext
Locus/
├── .git/                     # Internal Git folder (hidden)
├── .gitignore                # Specifies files/folders for Git to ignore
├── LICENSE                   # Project license file
├── README.md                 # This documentation file
├── assistant.py              # The main Python voice assistant script
├── requirements.txt          # Python package dependencies
│
├── venv/ (*)                 # Python virtual environment
│   └── ...
│
├── whisper.cpp/ (*)          # Cloned Whisper.cpp repository
│   ├── main (*)              # Compiled whisper executable
│   ├── models/ (*)           # Whisper models folder
│   │   └── *.bin (*)         # Downloaded whisper models
│   └── ...                   # Other Whisper.cpp source files
│
└── piper-tts/ (*)            # Piper TTS directory
    ├── piper (*)             # Piper executable
    ├── *.onnx (*)            # Piper voice model
    └── *.onnx.json (*)       # Piper voice config

# Temporary files created during runtime (*)
# temp_input.wav
# temp_output.wav
*(Note: Compiled tools and models inside `whisper.cpp` and `piper-tts` are intended to be acquired locally via the setup steps and are ignored by git to keep the repository small.)*
```

## Troubleshooting

*   **Path Errors:** Double-check all paths in `assistant.py`. This is the most common issue.
*   **Permissions:** Ensure `whisper.cpp/main` and `piper-tts/piper` are executable (`chmod +x ...`).
*   **Ollama Connection Error:** Make sure the Ollama application/service is running before starting `assistant.py`. Check the `OLLAMA_API_URL` in the script.
*   **Microphone Issues:** Check system audio settings. `sounddevice` might need configuration if the default mic isn't correct. Use `python -m sounddevice` to list devices.
*   **Audio Playback Failed:** Ensure you have a compatible command-line player installed (`aplay`, `play`, `afplay`) or that the `playsound` library works on your system (especially Windows).
*   **Whisper/Piper Errors:** Check the console output for specific error messages from these tools. Ensure models were downloaded correctly.

## Contributing / Future Improvements

Contributions are welcome! Feel free to open an issue or submit a pull request.

Potential enhancements:

*   [ ] Implement Wake Word detection (e.g., using `pvporcupine`).
*   [ ] Create a simple GUI (e.g., using Tkinter, PyQt, or a web framework like Flask/FastAPI).
*   [ ] More robust error handling and user feedback.
*   [ ] Configuration file instead of hardcoded paths in the script.
*   [ ] Option to select different STT/TTS voices/models easily.
*   [ ] Persistent conversation history (saving/loading).

## License

This project is licensed under the [MIT License](LICENSE).
