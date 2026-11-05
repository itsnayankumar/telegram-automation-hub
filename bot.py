import os
import asyncio

from dotenv import load_dotenv
from yt_dlp import YoutubeDL
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    TypeHandler,
    ApplicationHandlerStop,
    filters,
)

load_dotenv("config.env")

TOKEN = os.getenv("TOKEN")
MY_ID = int(os.getenv("MY_ID"))


# ---------- gatekeeper: runs first, blocks everyone except you ----------
async def gatekeeper(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user is None or user.id != MY_ID:
        raise ApplicationHandlerStop


# ---------- download logic (normal function, no Telegram inside) ----------
def download_video(url, mode="video"):
    options = {"outtmpl": "downloads/%(title)s.%(ext)s"}

    # only use cookies if the file exists
    if os.path.exists("cookies.txt"):
        options["cookiefile"] = "cookies.txt"

    if mode == "audio":
        options["format"] = "bestaudio/best"
        options["postprocessors"] = [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
        }]

    with YoutubeDL(options) as ydl:
        info = ydl.extract_info(url, download=True)
        # the real final file (after mp3 conversion or merging)
        downloads = info.get("requested_downloads")
        if downloads:
            path = downloads[0]["filepath"]
        else:
            path = ydl.prepare_filename(info)
    return path


# ---------- commands ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.effective_user.first_name
    await update.message.reply_text("Bot is Online, " + name)


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Send a link to get the video.\n"
        "/audio <link> to get the audio as MP3.\n"
        "/say <words> to test arguments."
    )


async def say(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) == 0:
        await update.message.reply_text("Usage: /say <words>")
        return
    await update.message.reply_text(" ".join(context.args))


async def audio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) == 0:
        await update.message.reply_text("Usage: /audio <link>")
        return

    url = context.args[0]
    if not url.startswith("http"):
        await update.message.reply_text("That doesn't look like a link")
        return

    await update.message.reply_text("Downloading audio......")
    try:
        path = await asyncio.to_thread(download_video, url, "audio")
        with open(path, "rb") as f:
            await update.message.reply_document(f)
    except Exception as e:
        print("Error:", e)
        await update.message.reply_text("That link didn't work")


# ---------- plain messages (links) ----------
async def link_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if not text.startswith("http"):
        await update.message.reply_text("Send me a link")
        return

    await update.message.reply_text("Downloading......")
    try:
        path = await asyncio.to_thread(download_video, text)
        with open(path, "rb") as f:
            await update.message.reply_document(f)
    except Exception as e:
        print("Error:", e)
        await update.message.reply_text("That link didn't work")


# ---------- build and run ----------
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(TypeHandler(Update, gatekeeper), group=-1)
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("help", help_cmd))
app.add_handler(CommandHandler("say", say))
app.add_handler(CommandHandler("audio", audio))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, link_handler))
app.run_polling()