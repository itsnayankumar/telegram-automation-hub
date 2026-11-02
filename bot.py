import os
import asyncio

from dotenv import load_dotenv
from yt_dlp import YoutubeDL
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from telegram.ext import MessageHandler, filters
from telegram.ext import TypeHandler, ApplicationHandlerStop

load_dotenv("config.env")

TOKEN = os.getenv("TOKEN")
MY_ID = int(os.getenv("MY_ID"))

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.effective_user.first_name
    await update.message.reply_text("Bot is Online, "+name)

async def help_cmd(update: Update,context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Bot is Helping")

def download_video(url):
    options = {"outtmpl": "downloads/%(title)s.%(ext)s",
    "cookiefile": "cookies.txt",
    }

    with YoutubeDL(options) as ydl:
        info = ydl.extract_info(url, download=True)
        path = ydl.prepare_filename(info)
    return path


async def link_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text.startswith("http"):
        await update.message.reply_text("Downloading......")
        
        try:
            path = await asyncio.to_thread(download_video, text)
            with open(path,"rb") as f:
                await update.message.reply_document(f)
        except:
            await update.message.reply_text("That link didn't work")
        
    else:
        await update.message.reply_text("Send me a link")
      
async def gatekeeper(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user is None or user.id != MY_ID:
        raise ApplicationHandlerStop

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(TypeHandler(Update, gatekeeper), group=-1)
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("help", help_cmd))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, link_handler))
app.run_polling()