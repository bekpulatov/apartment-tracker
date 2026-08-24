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
    lines = [
        "🏠 <b>New place found!</b>\n",
        f"<b>{listing['title']}</b>",
        f"💰 {listing['price']}",
        f"📍 {listing['address']}",
    ]
    if listing.get("walk_minutes") is not None:
        lines.append(f"🚶 ~{listing['walk_minutes']} min walk from home")
    if listing.get("bonfire"):
        lines.append("🔥 Might have bonfire space (yard/private house mentioned)")
    lines.append(f"🔗 <a href=\"{listing['url']}\">View listing ({listing['source']})</a>")

    text = "\n".join(lines)
    asyncio.run(_send(text, listing.get("image_url")))
