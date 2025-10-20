from pyrogram import Client, filters
from pyrogram.enums import ParseMode
from pydub import AudioSegment
from dotenv import load_dotenv
import os, subprocess, asyncio, re

# === CONFIG ===
load_dotenv()
api_id = int(os.getenv("TG_API_ID"))
api_hash = os.getenv("TG_API_HASH")
bot_token = os.getenv("TG_BOT_TOKEN")
admin_id = os.getenv("ADMIN_ID")

# Paths - FINAL PATHS AND OPTIMIZED MODEL
WHISPER_CPP_PATH = "/home/pi/Desktop/whisper.cpp/build/bin/whisper-cli"
MODEL_PATH = "/home/pi/Desktop/whisper.cpp/models/ggml-base-q5_1.bin"
TEMP_DIR = "/tmp/telegram_transcribe"
os.makedirs(TEMP_DIR, exist_ok=True)

# New limit constant
MAX_DURATION_SECONDS = 300  # 5 minutes maximum duration

# === NEW FEATURES CONFIG ===
# Replace with your actual Telegram User ID to receive notifications
ADMIN_ID =  admin_id # <--- IMPORTANT: Change this to your numeric Telegram user ID
STATS_FILE = "vocaly_bot_stats.txt"
UNIQUE_USERS_FILE = "vocaly_bot_users.txt"

# === STATISTICS FUNCTIONS ===
def load_stats():
    """Loads bot statistics from the stats file."""
    stats = {"total_starts": 0, "total_transcriptions": 0, "total_mb_transcribed": 0.0}
    if os.path.exists(STATS_FILE):
        try:
            with open(STATS_FILE, "r") as f:
                for line in f:
                    key, value = line.strip().split(": ")
                    if key == "total_mb_transcribed":
                        stats[key] = float(value)
                    else:
                        stats[key] = int(value)
        except Exception as e:
            print(f"Error loading stats: {e}. Starting with fresh stats.")
            return {"total_starts": 0, "total_transcriptions": 0, "total_mb_transcribed": 0.0}
    return stats

def save_stats(stats):
    """Saves bot statistics to the stats file."""
    with open(STATS_FILE, "w") as f:
        for key, value in stats.items():
            f.write(f"{key}: {value}\n")

def load_unique_users():
    """Loads the set of unique user IDs from a file."""
    users = set()
    if os.path.exists(UNIQUE_USERS_FILE):
        try:
            with open(UNIQUE_USERS_FILE, "r") as f:
                for user_id in f:
                    users.add(int(user_id.strip()))
        except Exception as e:
            print(f"Error loading unique users: {e}. Starting with an empty set.")
            return set()
    return users

def add_unique_user(user_id, user_set):
    """Adds a new user ID to the set and file if not already present."""
    if user_id not in user_set:
        user_set.add(user_id)
        with open(UNIQUE_USERS_FILE, "a") as f:
            f.write(f"{user_id}\n")

# Initialize stats on startup
bot_stats = load_stats()
unique_users = load_unique_users()

# === HELPER FUNCTIONS ===
def convert_to_wav(in_path, out_path):
    """Convert audio to 16kHz mono WAV, required for Whisper."""
    audio = AudioSegment.from_file(in_path)
    audio = audio.set_frame_rate(16000).set_channels(1).set_sample_width(2)
    audio.export(out_path, format="wav")

def transcribe_file(file_path):
    """Convert and transcribe with whisper-cli, limits threads, and cleans output."""
    wav_path = file_path + ".wav"
    convert_to_wav(file_path, wav_path)
    result = subprocess.run(
        [WHISPER_CPP_PATH, "-m", MODEL_PATH, "-f", wav_path, "-l", "auto", "-otxt", "-t", "2"],
        capture_output=True, text=True
    )
    out_txt = wav_path + ".txt"
    text = "[Transcription not found or audio was too short/silent]"
    if os.path.exists(out_txt):
        with open(out_txt, "r") as f:
            text = f.read().strip()
        os.remove(out_txt)
    os.remove(wav_path)
    stdout_cleaned = re.sub(r'WARNING:.*', '', result.stdout, flags=re.DOTALL | re.IGNORECASE).strip()
    if text.startswith("[Transcription not found") and stdout_cleaned:
        text = stdout_cleaned
    return text or "[Transcription failed. Check audio quality.]"

# === BOT ===
bot = Client("vocaly_bot", api_id=api_id, api_hash=api_hash, bot_token=bot_token)


# Handler for the /start command
@bot.on_message(filters.command("start"))
async def start_command(client, message):
    """Handles the /start command, providing an intro, updating stats, and notifying admin."""
    
    user = message.from_user
    
    # --- STATISTICS & NOTIFICATION ---
    is_new_user = user.id not in unique_users
    add_unique_user(user.id, unique_users)
    
    # Increment total starts count every time
    bot_stats["total_starts"] = bot_stats.get("total_starts", 0) + 1
    save_stats(bot_stats)

    username = f"@{user.username}" if user.username else f"{user.first_name} (ID: {user.id})"
    
    # Only notify for brand new users
    if is_new_user:
        notification_text = f"🔔 New user started VocalyBot: {username}"
        try:
            await client.send_message(ADMIN_ID, notification_text)
        except Exception as e:
            print(f"Could not send notification to ADMIN_ID {ADMIN_ID}. Error: {e}")
    # --------------------------------

    welcome_text = (
        "👋 Hi! I'm Vocaly, your automatic transcription bot. "
        "Send me a voice message or an audio file and I'll"
        " transcribe it into text instantly!"
    )
    await message.reply_text(welcome_text, quote=True, parse_mode=ParseMode.HTML)

@bot.on_message(filters.command("stats"))
async def stats_command(client, message):
    """Displays public statistics for the bot."""
    total_mb = bot_stats.get('total_mb_transcribed', 0.0)
    stats_text = (
        "📊 <b>Vocaly Bot Statistics</b>\n\n"
        f"👥 <b>Unique Users:</b> {len(unique_users)}\n"
        f"🚀 <b>Total /start Commands:</b> {bot_stats.get('total_starts', 0)}\n"
        f"🎤 <b>Total Transcriptions:</b> {bot_stats.get('total_transcriptions', 0)}\n"
        f"💾 <b>Data Transcribed:</b> {total_mb:.2f} MB"
    )
    await message.reply_text(stats_text, quote=True, parse_mode=ParseMode.HTML)

@bot.on_message(filters.command("about") & filters.private)
async def about_command(client, message):
    """Handles the /about command, providing information about the creator."""
    about_text = (
        "🤖 Vocaly was created for fun by: "
        "<a href='https://t.me/daniele_deb'>@daniele_deb</a>"
    )
    await message.reply_text(about_text, quote=True, parse_mode=ParseMode.HTML, disable_web_page_preview=True)

@bot.on_message(filters.text & filters.private & ~filters.regex(r"^\/"))
async def handle_text(client, message):
    """Informs the user that the bot only accepts voice and audio."""
    error_text = (
        "🚫 I only transcribe audio. "
        "Please send me a voice message."
    )
    await message.reply_text(error_text, quote=True, parse_mode=ParseMode.HTML)
       
@bot.on_message(filters.voice | filters.audio)
async def handle_voice(client, message):
    temp_prefix = os.path.join(TEMP_DIR, f"{message.id}")
    downloaded_file_path = None
    
    # --- DURATION LIMIT CHECK ---
    duration = 0
    if message.voice:
        duration = message.voice.duration
    elif message.audio:
        duration = message.audio.duration
        
    if duration > MAX_DURATION_SECONDS:
        max_minutes = MAX_DURATION_SECONDS // 60
        limit_text = (
            f"⛔ **File too long.** "
            f"The maximum allowed duration is {max_minutes} minutes."
        )
        await message.reply_text(limit_text, quote=True, parse_mode=ParseMode.HTML)
        return  # Stop processing if the limit is exceeded
    # ----------------------------

    try:
        # 1. Download the file
        downloaded_file_path = await client.download_media(message, file_name=temp_prefix)
        
        # 2. Waiting message
        await message.reply_text("⏳ Transcription in progress...", quote=True)
        # 3. Execute transcription in a separate thread
        text = await asyncio.to_thread(transcribe_file, downloaded_file_path)
        # 4. Send the final transcription
        await message.reply_text(f"📝 <b>Transcription:</b>\n{text}", quote=True, parse_mode=ParseMode.HTML)
        
        # --- UPDATE TRANSCRIPTION STATS ---
        file_size_bytes = os.path.getsize(downloaded_file_path)
        file_size_mb = file_size_bytes / (1024 * 1024)
        bot_stats["total_transcriptions"] = bot_stats.get("total_transcriptions", 0) + 1
        bot_stats["total_mb_transcribed"] = bot_stats.get("total_mb_transcribed", 0.0) + file_size_mb
        save_stats(bot_stats)
        # ------------------------------------
        
    except Exception as e:
        print(f"Error in handle_voice handler: {e}")
        await message.reply_text(f"❌ Error during transcription: {e}", quote=True)
        
    finally:
        # Clean up temporary files
        if downloaded_file_path and os.path.exists(downloaded_file_path):
            os.remove(downloaded_file_path)
        # Remove intermediate temporary files (.wav and .txt)
        for ext in [".wav", ".txt"]:
            path = downloaded_file_path + ext if downloaded_file_path else temp_prefix + ext
            if os.path.exists(path):
                os.remove(path)

# === RUN ===
if __name__ == "__main__":
    print("🤖 Vocaly running...")
    mb_stat = f"{bot_stats.get('total_mb_transcribed', 0.0):.2f}"
    print(f"📊 Current stats: Starts={bot_stats.get('total_starts', 0)}, Transcriptions={bot_stats.get('total_transcriptions', 0)}, MBs={mb_stat} | Unique Users: {len(unique_users)}")
    bot.run()

