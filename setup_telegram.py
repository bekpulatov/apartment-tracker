"""
Run this once after creating your Telegram bot to get your chat ID.
Steps:
  1. Message @BotFather on Telegram → /newbot → follow prompts → copy the token
  2. Copy .env.example to .env and paste the token
  3. Send any message to your new bot on Telegram
  4. Run: python setup_telegram.py
  5. Copy the chat_id printed and paste it into .env as TELEGRAM_CHAT_ID
"""
import requests
import os
from dotenv import load_dotenv

load_dotenv()

token = os.getenv("TELEGRAM_BOT_TOKEN")
if not token:
    print("ERROR: TELEGRAM_BOT_TOKEN not set in .env")
    exit(1)

r = requests.get(f"https://api.telegram.org/bot{token}/getUpdates")
data = r.json()

if not data.get("ok"):
    print(f"ERROR: {data}")
    exit(1)

updates = data.get("result", [])
if not updates:
    print("No messages found. Make sure you sent a message to your bot first, then re-run.")
    exit(1)

for update in updates:
    msg = update.get("message") or update.get("channel_post")
    if msg:
        chat = msg["chat"]
        print(f"Found chat:")
        print(f"  chat_id : {chat['id']}")
        print(f"  username: @{chat.get('username', 'N/A')}")
        print(f"\nAdd this to your .env:")
        print(f"  TELEGRAM_CHAT_ID={chat['id']}")
        break
