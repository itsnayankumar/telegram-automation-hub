import os
import asyncio

from dotenv import load_dotenv
from yt_dlp import YoutubeDL
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    TypeHandler,
    ApplicationHandlerStop,
    filters,
)

# ---------- config ----------
load_dotenv("config.env")

TOKEN = os.getenv("TOKEN")
MY_ID_RAW = os.getenv("MY_ID")

if not TOKEN or not MY_ID_RAW:
    raise SystemExit(
        "Missing TOKEN or MY_ID. Copy config.env.example to config.env and fill it in."
    )

MY_ID = int(MY_ID_RAW)

MAX_UPLOAD = 50 * 1024 * 1024  # Telegram's upload limit for bots (50 MB)

QUALITIES = {
    "360": "360p",
    "720": "720p",
    "1080": "1080p",
    "audio": "Audio (MP3)",
}


# ---------- gatekeeper: runs first, blocks everyone except you ----------
async def gatekeeper(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user is None or user.id != MY_ID:
        raise ApplicationHandlerStop


# ---------- download logic (normal function, no Telegram inside) ----------
def download_video(url, choice="720"):
    options = {
        "outtmpl": "downloads/%(title).80s.%(ext)s",
        "noplaylist": True,
    }

    # only use cookies if the file exists
    if os.path.exists("cookies.txt"):
        options["cookiefile"] = "cookies.txt"

    if choice == "audio":
        options["format"] = "bestaudio/best"
        options["postprocessors"] = [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
        }]
    else:
        h = choice
        options["format"] = (
            f"bestvideo[height<={h}][ext=mp4]+bestaudio[ext=m4a]"
            f"/best[height<={h}][ext=mp4]"
            f"/best[height<={h}]"
            f"/best"
        )
        options["merge_output_format"] = "mp4"

    with YoutubeDL(options) as ydl:
        info = ydl.extract_info(url, download=True)

        # the real final file (after merging or mp3 conversion)
        downloads = info.get("requested_downloads")
        if downloads:
            path = downloads[0]["filepath"]
        else:
            path = ydl.prepare_filename(info)

        if choice == "audio" and not os.path.exists(path):
            path = os.path.splitext(path)[0] + ".mp3"

    return path


# ---------- download + send + clean up ----------
async def deliver(chat_id, context, url, choice):
    path = None
    try:
        path = await asyncio.to_thread(download_video, url, choice)

        size = os.path.getsize(path)
        if size > MAX_UPLOAD:
            mb = round(size / (1024 * 1024))
            await context.bot.send_message(
                chat_id=chat_id,
                text=f"The file is {mb} MB, over Telegram's 50 MB bot limit. Try a lower quality.",
            )
            return

        with open(path, "rb") as f:
            await context.bot.send_document(chat_id=chat_id, document=f)

    except Exception as e:
        print("Error:", e)
        await context.bot.send_message(chat_id=chat_id, text="That link didn't work")

    finally:
        # delete the file from disk so downloads/ doesn't fill up
        if path and os.path.exists(path):
            os.remove(path)


# ---------- commands ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.effective_user.first_name
    await update.message.reply_text("Bot is Online, " + name)


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Send me a link, then pick a quality with the buttons.\n"
        "/audio <link> downloads MP3 audio straight away."
    )


async def audio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) == 0:
        await update.message.reply_text("Usage: /audio <link>")
        return

    url = context.args[0]
    if not url.startswith("http"):
        await update.message.reply_text("That doesn't look like a link")
        return

    await update.message.reply_text("Downloading audio......")
    await deliver(update.effective_chat.id, context, url, "audio")


# ---------- plain messages: a link shows the quality buttons ----------
def quality_keyboard():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("360p", callback_data="360"),
            InlineKeyboardButton("720p", callback_data="720"),
            InlineKeyboardButton("1080p", callback_data="1080"),
        ],
        [InlineKeyboardButton("Audio (MP3)", callback_data="audio")],
    ])


async def link_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if not text.startswith("http"):
        await update.message.reply_text("Send me a link")
        return

    msg = await update.message.reply_text(
        "Choose quality:", reply_markup=quality_keyboard()
    )
    # remember which link belongs to this button message
    context.user_data[msg.message_id] = text


# ---------- a button was clicked ----------
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()  # stops the loading spinner on the button

    choice = query.data
    url = context.user_data.pop(query.message.message_id, None)

    if url is None or choice not in QUALITIES:
        await query.edit_message_text("That request expired. Send the link again.")
        return

    await query.edit_message_text("Downloading " + QUALITIES[choice] + "......")
    await deliver(query.message.chat_id, context, url, choice)


# ---------- build and run ----------
app = (
    ApplicationBuilder()
    .token(TOKEN)
    .read_timeout(120)
    .write_timeout(120)
    .build()
)

app.add_handler(TypeHandler(Update, gatekeeper), group=-1)
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("help", help_cmd))
app.add_handler(CommandHandler("audio", audio))
app.add_handler(CallbackQueryHandler(button_handler))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, link_handler))
app.run_polling()