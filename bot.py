import os
import re
import asyncio
import threading
from flask import Flask
from telethon import TelegramClient, events

# Telegram API credentials
api_id = 22017572
api_hash = '8f4fadf436adb0fc6365c3c68632b709'
BOT_TOKEN = '7535489123:AAEFRpbkfoiIQ7p9mg0Ggf4jOD8HXjn3exY'

# Telegram chat IDs
source_chat_ids = [-1002682944548, -1001939510590]
destination_chat_ids = [-1002564741429, -1002565613612]

# Clients
user_client = TelegramClient('user_session', api_id, api_hash)
bot_client = TelegramClient('bot_session', api_id, api_hash)

# Regex patterns to detect card-like messages
patterns = [
    re.compile(r'(\d{16})\|(\d{1,2})\|(\d{2,4})\|(\d{3,4})'),
    re.compile(r'(\d{16}) (\d{1,2}) (\d{2,4}) (\d{3,4})'),
    re.compile(r'(\d{16}) (\d{1,2})/(\d{2,4}) (\d{3,4})'),
    re.compile(r'CC\s*#[: ]*(\d{16}).*?\|?Exp[: ]*(\d{2})(\d{2}).*?\|?CCV[: ]*(\d{3,4})'),
    re.compile(r'(?s)(\d{16})\s*\n\s*(\d{1,2})/(\d{2,4})\s*\n\s*(\d{3,4})'),
    re.compile(r'(\d{16})\s+(\d{1,2})/(\d{2,4})\s+(\d{3,4})\s+[\w\s]+'),
    re.compile(r'(\d{16})[^\d]{1,5}(\d{1,2})[^\d]{1,5}(\d{2,4})[^\d]{1,5}(\d{3,4})'),
]

def normalize_cc_format(cc, mm, yy, cvv):
    mm = mm.zfill(2)
    yy = '20' + yy if len(yy) == 2 else yy
    cvv = cvv.zfill(3)
    return f"{cc}|{mm}|{yy}|{cvv}"

@user_client.on(events.NewMessage(chats=source_chat_ids))
async def handler(event):
    try:
        message = event.raw_text.strip()

        for pattern in patterns:
            match = pattern.search(message)
            if match:
                cc, mm, yy, cvv = match.groups()
                formatted_cc = normalize_cc_format(cc, mm, yy, cvv)

                for dest in destination_chat_ids:
                    try:
                        await bot_client.send_message(dest, formatted_cc)
                        print(f"✅ Sent to {dest}: {formatted_cc}")
                    except Exception as e:
                        print(f"❌ Failed to send to {dest}: {e}")
                return

        print("❌ No match found")
    except Exception as e:
        print(f"❌ Handler error: {e}")

# Web server for Render (keep service alive)
app = Flask(__name__)

@app.route('/')
@app.route('/alive')
def alive():
    return '🤖 Bot is alive and running!', 200

def run_web():
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)

# Main bot function
async def main():
    try:
        await user_client.start()
        await bot_client.start(bot_token=BOT_TOKEN)
        print("🤖 Telegram bot started...")
        await user_client.run_until_disconnected()
    except Exception as e:
        print(f"❌ Main error: {e}")
    finally:
        await user_client.disconnect()
        await bot_client.disconnect()

# Run both web and bot
if __name__ == '__main__':
    threading.Thread(target=run_web).start()
    asyncio.run(main())
