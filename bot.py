import telebot
import yt_dlp
import os
import tempfile

BOT_TOKEN = os.environ.get("BOT_TOKEN")
bot = telebot.TeleBot(BOT_TOKEN)

SUPPORTED_DOMAINS = [
    "tiktok.com", "instagram.com", "instagr.am",
    "youtube.com", "youtu.be", "twitter.com",
    "x.com", "facebook.com", "fb.watch"
]

def is_supported_url(url):
    return any(domain in url for domain in SUPPORTED_DOMAINS)

def download_content(url, mode="video", quality="best"):
    tmpdir = tempfile.mkdtemp()
    output_path = os.path.join(tmpdir, "%(title)s.%(ext)s")

    if mode == "audio":
        ydl_opts = {
            "outtmpl": output_path,
            "format": "bestaudio/best",
            "postprocessors": [{"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": "192"}],
            "quiet": True,
            "no_warnings": True,
            "http_headers": {"User-Agent": "Mozilla/5.0"},
        }
    else:
        if quality == "hd":
            fmt = "bestvideo[height<=1080]+bestaudio/best"
        elif quality == "sd":
            fmt = "bestvideo[height<=480]+bestaudio/best"
        else:
            fmt = "bestvideo+bestaudio/best"

        ydl_opts = {
            "outtmpl": output_path,
            "format": fmt,
            "merge_output_format": "mp4",
            "noplaylist": False,
            "extractor_args": {"tiktok": {"webpage_download": ["1"]}},
            "http_headers": {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0 Safari/537.36"},
            "quiet": True,
            "no_warnings": True,
        }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        entries = info.get("entries", None)
        if entries:
            photos = []
            for entry in entries:
                filename = ydl.prepare_filename(entry)
                for ext in ["jpg", "jpeg", "png", "webp", "mp4"]:
                    alt = filename.rsplit(".", 1)[0] + f".{ext}"
                    if os.path.exists(alt):
                        photos.append(alt)
                        break
                if os.path.exists(filename):
                    photos.append(filename)
            if photos:
                return "photos", list(set(photos))

        filename = ydl.prepare_filename(info)
        if mode == "audio":
            filename = filename.rsplit(".", 1)[0] + ".mp3"
        if not os.path.exists(filename):
            filename = filename.rsplit(".", 1)[0] + ".mp4"
        return "video" if mode != "audio" else "audio", filename

user_states = {}

@bot.message_handler(commands=["start", "help"])
def send_welcome(message):
    bot.reply_to(message, (
        "👋 Welcome to the Ultimate Downloader Bot!\n\n"
        "🎬 TikTok (no watermark)\n"
        "📸 TikTok Photos\n"
        "📱 Instagram Reels & Posts\n"
        "🎥 YouTube Shorts\n"
        "🐦 Twitter/X Videos\n"
        "📘 Facebook Videos\n\n"
        "Just send me any link and choose what you want!\n"
        "Better than SnapTik & TikMate 😎"
    ))

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    url = message.text.strip()

    if not is_supported_url(url):
        bot.reply_to(message, "❌ Please send a valid video link!")
        return

    user_states[message.chat.id] = url

    markup = telebot.types.InlineKeyboardMarkup()
    markup.row(
        telebot.types.InlineKeyboardButton("🎬 Video (Best)", callback_data="best"),
        telebot.types.InlineKeyboardButton("📺 HD 1080p", callback_data="hd")
    )
    markup.row(
        telebot.types.InlineKeyboardButton("📱 SD 480p", callback_data="sd"),
        telebot.types.InlineKeyboardButton("🎵 MP3 Audio", callback_data="audio")
    )

    bot.reply_to(message, "⚡ Choose download quality:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    chat_id = call.message.chat.id
    url = user_states.get(chat_id)

    if not url:
        bot.answer_callback_query(call.id, "❌ Please send a link first!")
        return

    mode = "audio" if call.data == "audio" else "video"
    quality = call.data if call.data in ["hd", "sd"] else "best"

    bot.answer_callback_query(call.id)
    status_msg = bot.send_message(chat_id, "⏳ Downloading... please wait!")

    try:
        content_type, content = download_content(url, mode=mode, quality=quality)

        if content_type == "photos":
            bot.edit_message_text(f"✅ Sending {len(content)} photo(s)...", chat_id=chat_id, message_id=status_msg.message_id)
            media = []
            for photo in content:
                with open(photo, "rb") as f:
                    media.append(telebot.types.InputMediaPhoto(f.read()))
            bot.send_media_group(chat_id, media)

        elif content_type == "audio":
            bot.edit_message_text("✅ Sending audio...", chat_id=chat_id, message_id=status_msg.message_id)
            with open(content, "rb") as audio:
                bot.send_audio(chat_id, audio, caption="🎵 Here's your MP3!")

        else:
            if os.path.getsize(content) > 50 * 1024 * 1024:
                bot.edit_message_text("❌ Video too large (over 50MB).", chat_id=chat_id, message_id=status_msg.message_id)
                return
            bot.edit_message_text("✅ Sending your video...", chat_id=chat_id, message_id=status_msg.message_id)
            with open(content, "rb") as video:
                bot.send_video(chat_id, video, supports_streaming=True, caption="✅ Here's your video without watermark!")

    except Exception as e:
        bot.edit_message_text(f"❌ Error: {str(e)}", chat_id=chat_id, message_id=status_msg.message_id)

    finally:
        user_states.pop(chat_id, None)
        try:
            if content_type == "photos":
                for p in content:
                    if os.path.exists(p): os.remove(p)
            elif os.path.exists(content):
                os.remove(content)
        except:
            pass

bot.infinity_polling()
