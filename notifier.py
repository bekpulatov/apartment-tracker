import asyncio
import telegram
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID


async def _send(text: str, image_url: str | None):
    bot = telegram.Bot(token=TELEGRAM_BOT_TOKEN)
    if image_url:
        try:
            await bot.send_photo(chat_id=TELEGRAM_CHAT_ID, photo=image_url, caption=text, parse_mode="HTML")
            return
        except Exception:
            pass
    await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=text, parse_mode="HTML")


def notify(listing: dict):
    text = (
        f"🏠 <b>New apartment found!</b>\n\n"
        f"<b>{listing['title']}</b>\n"
        f"💰 {listing['price']}\n"
        f"📍 {listing['address']}\n"
        f"🔗 <a href=\"{listing['url']}\">View listing ({listing['source']})</a>"
    )
    asyncio.run(_send(text, listing.get("image_url")))
