import telebot
import yt_dlp
import os
import tempfile

BOT_TOKEN = os.environ.get("BOT_TOKEN")
bot = telebot.TeleBot(BOT_TOKEN)

def is_supported_url(url):
    return any(domain in url for domain in ["tiktok.com", "instagram.com", "instagr.am"])

def download_video(url):
    tmpdir = tempfile.mkdtemp()
    output_path = os.path.join(tmpdir, "%(title)s.%(ext)s")
    ydl_opts = {
        "outtmpl": output_path,
        "format": "bestvideo+bestaudio/best",
        "merge_output_format": "mp4",
        "noplaylist": True,
        "extractor_args": {"tiktok": {"webpage_download": ["1"]}},
        "http_headers": {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0 Safari/537.36"},
        "quiet": True,
        "no_warnings": True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = ydl.prepare_filename(info)
        if not os.path.exists(filename):
            filename = filename.rsplit(".", 1)[0] + ".mp4"
        return filename

@bot.message_handler(commands=["start", "help"])
def send_welcome(message):
    bot.reply_to(message, "👋 سلام عليكم Send me a TikTok or Instagram link!\n\n✅ I'll send it back without watermark in best quality 🎬")

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    url = message.text.strip()
    if not is_supported_url(url):
        bot.reply_to(message, "❌ Please send a valid TikTok or Instagram link.")
        return
    status_msg = bot.reply_to(message, "⏳ Downloading... please wait خو بگره!")
    try:
        video_path = download_video(url)
        if os.path.getsize(video_path) > 50 * 1024 * 1024:
            bot.edit_message_text("❌ Video too large (over 50MB).", chat_id=message.chat.id, message_id=status_msg.message_id)
            return
        bot.edit_message_text("✅ Sending your video...", chat_id=message.chat.id, message_id=status_msg.message_id)
        with open(video_path, "rb") as video:
            bot.send_video(message.chat.id, video, supports_streaming=True, caption="✅ Here's your video without watermark!")
    except Exception as e:
        bot.edit_message_text(f"❌ Error: {str(e)}", chat_id=message.chat.id, message_id=status_msg.message_id)
    finally:
        try:
            if "video_path" in locals() and os.path.exists(video_path):
                os.remove(video_path)
        except:
            pass

bot.infinity_polling()
