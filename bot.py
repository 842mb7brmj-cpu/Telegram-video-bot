import telebot
import yt_dlp
import os
import tempfile
import requests

BOT_TOKEN = os.environ.get("BOT_TOKEN")
bot = telebot.TeleBot(BOT_TOKEN)

SUPPORTED_DOMAINS = [
    "tiktok.com", "instagram.com", "instagr.am",
    "youtube.com", "youtu.be", "twitter.com",
    "x.com", "facebook.com", "fb.watch"
]

def is_supported_url(url):
    return any(domain in url for domain in SUPPORTED_DOMAINS)

def get_tiktok_photos(url):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        session = requests.Session()
        response = session.get(url, headers=headers, allow_redirects=True)
        final_url = response.url
        api_url = "https://tikwm.com/api/"
        payload = {"url": final_url, "hd": 1}
        api_response = requests.post(api_url, data=payload, headers=headers)
        data = api_response.json()
        photos = []
        if data.get("code") == 0:
            images = data.get("data", {}).get("images", [])
            for img in images:
                if isinstance(img, dict):
                    photos.append(img.get("url", ""))
                else:
                    photos.append(img)
        return [p for p in photos if p]
    except:
        return []

def get_tiktok_video(url, quality="hd"):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        session = requests.Session()
        response = session.get(url, headers=headers, allow_redirects=True)
        final_url = response.url
        api_url = "https://tikwm.com/api/"
        payload = {"url": final_url, "hd": 1}
        api_response = requests.post(api_url, data=payload, headers=headers)
        data = api_response.json()
        if data.get("code") == 0:
            if quality == "hd":
                return data.get("data", {}).get("hdplay") or data.get("data", {}).get("play")
            else:
                return data.get("data", {}).get("play")
        return None
    except:
        return None

def get_instagram_video(url):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        api_url = "https://tikwm.com/api/"
        payload = {"url": url, "hd": 1}
        api_response = requests.post(api_url, data=payload, headers=headers)
        data = api_response.json()
        if data.get("code") == 0:
            return data.get("data", {}).get("hdplay") or data.get("data", {}).get("play")
        return None
    except:
        return None

def download_video_file(video_url):
    try:
        tmpdir = tempfile.mkdtemp()
        video_path = os.path.join(tmpdir, "video.mp4")
        response = requests.get(video_url, headers={"User-Agent": "Mozilla/5.0"}, stream=True)
        with open(video_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        return video_path
    except:
        return None

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
            "http_headers": {
                "User-Agent": "Mozilla/5.0 (Linux; Android 12; Pixel 6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Mobile Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
                "Accept-Encoding": "gzip, deflate, br",
                "Connection": "keep-alive",
            },
            "quiet": True,
            "no_warnings": True,
        }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = ydl.prepare_filename(info)
        if mode == "audio":
            filename = filename.rsplit(".", 1)[0] + ".mp3"
        if not os.path.exists(filename):
            filename = filename.rsplit(".", 1)[0] + ".mp4"
        return "video" if mode != "audio" else "audio", filename

user_states = {}

def show_quality_buttons(message):
    markup = telebot.types.InlineKeyboardMarkup()
    markup.row(
        telebot.types.InlineKeyboardButton("🎬 Best Quality", callback_data="best"),
        telebot.types.InlineKeyboardButton("📺 HD 1080p", callback_data="hd")
    )
    markup.row(
        telebot.types.InlineKeyboardButton("📱 SD 480p", callback_data="sd"),
        telebot.types.InlineKeyboardButton("🎵 MP3 Audio", callback_data="audio")
    )
    bot.reply_to(message, "⚡ Choose your download format:", reply_markup=markup)

@bot.message_handler(commands=["start", "help"])
def send_welcome(message):
    bot.reply_to(message,
        "👋 Welcome to the Ultimate Downloader Bot! 🔥\n\n"
        "👑 Owner: @.unknown.0x0 on TikTok\n\n"
        "📥 I can download from:\n"
        "🎵 TikTok (no watermark)\n"
        "📸 TikTok Photo Slideshows\n"
        "📱 Instagram Reels & Posts\n"
        "🎥 YouTube Shorts\n"
        "🐦 Twitter/X Videos\n"
        "📘 Facebook Videos\n\n"
        "⚡ Just send me any link!\n"
        "Better than SnapTik & TikMate 😎🔥"
    )

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    url = message.text.strip()
    if not is_supported_url(url):
        bot.reply_to(message, "❌ Invalid link! Please send a supported link!")
        return

    user_states[message.chat.id] = url

    if "tiktok.com" in url:
        status_msg = bot.reply_to(message, "⏳ Checking TikTok link... 🔄")
        try:
            headers = {"User-Agent": "Mozilla/5.0"}
            response = requests.get(url, headers=headers, allow_redirects=True)
            final_url = response.url
            if "/photo/" in final_url:
                bot.edit_message_text("📸 Photo slideshow detected! Downloading...", chat_id=message.chat.id, message_id=status_msg.message_id)
                photo_urls = get_tiktok_photos(url)
                if photo_urls:
                    media = []
                    for photo_url in photo_urls:
                        media.append(telebot.types.InputMediaPhoto(photo_url))
                    bot.delete_message(message.chat.id, status_msg.message_id)
                    bot.send_media_group(message.chat.id, media)
                    bot.send_message(message.chat.id, "✅ Here are your photos! 📸🔥")
                    return
                else:
                    bot.edit_message_text("❌ Could not download photos!", chat_id=message.chat.id, message_id=status_msg.message_id)
                    return
        except Exception as e:
            bot.edit_message_text(f"❌ Error: {str(e)}", chat_id=message.chat.id, message_id=status_msg.message_id)
            return
        bot.delete_message(message.chat.id, status_msg.message_id)
        show_quality_buttons(message)
        return

    if "instagram.com" in url:
        if "/stories/" in url:
            bot.reply_to(message, "❌ Instagram Stories require login and are not supported yet 😔\n\nTry sending a Reel or Post instead!")
            return
        status_msg = bot.reply_to(message, "⏳ Downloading Instagram video... 🔄")
        try:
            video_url = get_instagram_video(url)
            if video_url:
                video_path = download_video_file(video_url)
                if video_path:
                    bot.delete_message(message.chat.id, status_msg.message_id)
                    with open(video_path, "rb") as video:
                        bot.send_video(message.chat.id, video, supports_streaming=True, caption="✅ Here is your Instagram video! 📱🔥")
                    os.remove(video_path)
                    return
            bot.delete_message(message.chat.id, status_msg.message_id)
            bot.send_message(message.chat.id, "❌ Could not download Instagram video! Try again.")
            return
        except Exception as​​​​​​​​​​​​​​​​
