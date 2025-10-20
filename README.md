# 🎤 Vocaly Bot - Telegram Transcriber

A Telegram bot for the automatic transcription of voice messages and audio files, powered by whisper.cpp. Vocaly is optimized for running on compact hardware like a Raspberry Pi.

## ✨ Key Features

Fast Transcription: Utilizes the high-performance C++ implementation of Whisper (whisper.cpp) for quick transcription.

Flexible Formats: Accepts voice messages and audio files (automatically converted to 16kHz WAV by pydub).

Duration Limits: Sets a maximum limit of $5$ minutes ($300$ seconds) for files, preventing excessive resource consumption.

Integrated Statistics:

/stats command to display unique users, total transcriptions, and the volume of processed data.

Automatic notification to the Administrator when a new user starts the bot.

Persistent Logging: Saves statistics and the list of unique users to files.

## 🚀 How to Use Vocaly

The easiest way to start transcribing is to open the bot directly on Telegram:

## 🔗 Start the Bot on Telegram (Placeholder: Replace VocalyTranscriberBot with your actual bot username.)

Send the /start command.

Send any voice message or audio file (max $5$ minutes long).

Receive the automatic transcription instantly!

## 🛠️ Prerequisites

To run Vocaly, you will need:

Python 3.8+

ffmpeg: Required for audio manipulation via pydub.

whisper.cpp: The external transcription library.

1. whisper.cpp Setup

The bot relies on a functional installation of whisper.cpp and its executable, whisper-cli.

Clone the whisper.cpp repository and compile the project:

git clone [https://github.com/ggerganov/whisper.cpp](https://github.com/ggerganov/whisper.cpp)
cd whisper.cpp
make




Download the specified pre-trained model (in the code, it is ggml-base-q5_1.bin) to the /models directory:

./models/download-ggml-model.sh base.en
# You might need to specify a different model depending on your configuration




Verify Paths: Ensure that the environment variables in your Python file point to the correct paths:

WHISPER_CPP_PATH = "/home/pi/Desktop/whisper.cpp/build/bin/whisper-cli" # Modify if necessary
MODEL_PATH = "/home/pi/Desktop/whisper.cpp/models/ggml-base-q5_1.bin" # Modify if necessary




2. Python and Dependencies Setup

Install the required Python packages:

pip install pyrogram pydub python-dotenv

