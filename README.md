# FetchBot

A private Telegram bot that downloads videos and audio from links using [yt-dlp](https://github.com/yt-dlp/yt-dlp) and sends the file back to you. Send a link, tap a quality button, and get the file in the chat.

Built with Python and [python-telegram-bot](https://python-telegram-bot.org/) as a learning project.

## Features

- Send any supported link and choose **360p, 720p, 1080p, or MP3 audio** with inline buttons
- `/audio <link>` for direct MP3 download
- **Owner-only:** a gatekeeper blocks every user except the Telegram ID in your config
- Downloads run in a background thread, so the bot stays responsive
- Files are deleted from disk after they are sent
- Clear messages for failed links and for files over Telegram's 50 MB bot upload limit

## Requirements

- Python 3.10 or newer
- [ffmpeg](https://ffmpeg.org/) (merging video and audio, converting to MP3)
- A JavaScript runtime such as [Deno](https://deno.com/) (YouTube downloads need it; see [Troubleshooting](#troubleshooting))
- A Telegram bot token from [@BotFather](https://t.me/BotFather)

## Setup

```bash
# 1. Clone the repo
git clone <repo-url>
cd <repo-folder>

# 2. Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Create your config file
cp config.env.example config.env
```

Open `config.env` and fill in:

```
TOKEN=your-bot-token-from-botfather
MY_ID=your-telegram-user-id
```

Don't know your user ID? Message a bot such as @userinfobot, or temporarily add a command that replies with `update.effective_user.id`.

## Run

```bash
python bot.py
```

Open your bot in Telegram and send `/start`. Stop it with `Ctrl+C`.

## Usage

| Command / action | What it does |
|---|---|
| `/start` | Checks that the bot is online |
| `/help` | Shows a short help message |
| Send a link | Shows quality buttons (360p, 720p, 1080p, Audio) |
| `/audio <link>` | Downloads the audio as MP3 immediately |

## Project structure

```
.
├── bot.py                 # the whole bot
├── requirements.txt       # Python dependencies
├── config.env.example     # template for your secrets
├── config.env             # your real secrets (never committed)
└── downloads/             # temporary files (never committed)
```

## Troubleshooting

**"Only images are available" or "Requested format is not available" on YouTube**
yt-dlp needs a JavaScript runtime and its challenge-solver scripts to read YouTube. Install Deno, reopen your terminal so it is on your PATH, and update yt-dlp with its extras:

```bash
pip install -U "yt-dlp[default]"
deno --version
```

The exact steps change over time, so check the [yt-dlp EJS wiki page](https://github.com/yt-dlp/yt-dlp/wiki/EJS) if this does not match what you see.

**"Sign in to confirm your age"**
Age-restricted videos need a logged-in session. Export your browser cookies to a file named `cookies.txt` in the project folder; the bot uses it automatically when it exists. Treat this file like a password: it is listed in `.gitignore`, and you should never share or commit it.

**File over 50 MB**
Telegram bots can upload files up to 50 MB through the standard Bot API. Choose a lower quality or use audio only.

**`ModuleNotFoundError`**
Your virtual environment is not active. Run `source .venv/bin/activate` and try again.

**Downloads break after working for a while**
Sites change often. Update yt-dlp: `pip install -U "yt-dlp[default]"`.

## Security notes

- Keep `config.env` and `cookies.txt` out of Git. Both are in `.gitignore`.
- If your bot token ever leaks, send `/revoke` to @BotFather and put the new token in `config.env`.
- The bot only answers the Telegram user ID in `MY_ID`.

## Responsible use

Only download content you own, content that is in the public domain or licensed for it, or content you otherwise have the right to save. You are responsible for following the terms of the sites you use and the copyright laws that apply to you.

## Ideas for later

- A `/history` command
- Playlist support
- Running on a small server or on Termux so it stays online
- A file-size estimate before downloading