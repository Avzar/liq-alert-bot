import os
import asyncio
import aiohttp
from telegram import Bot
from telegram.constants import ParseMode

# === НАСТРОЙКИ ===
TOKEN = os.environ["BOT_TOKEN"]                    # твой токен
CHAT_ID = -1001234567890                           # ID чата/канала, куда слать алерты
MIN_AMOUNT_USD = 150_000                            # только ликвидации от $150k
SYMBOLS = ["BTC", "ETH", "SOL", "XRP", "DOGE"]      # можно добавить любые

# Bybit WebSocket (публичный, без ключа)
WS_URL = "wss://stream.bybit.com/v5/public/linear"

bot = Bot(token=TOKEN)

async def send_alert(msg: str):
    try:
        await bot.send_message(chat_id=CHAT_ID, text=msg, parse_mode=ParseMode.HTML, disable_web_page_preview=True)
    except Exception as e:
        print("Ошибка отправки:", e)

async def main():
    print("Бот ликвидаций запущен — ждёт жирные лики...")
    async with aiohttp.ClientSession() as session:
        async with session.ws_connect(WS_URL) as ws:
            # подписываемся на канал ликвидаций
            await ws.send_json({
                "op": "subscribe",
                "args": ["liquidation.BTCUSDT", "liquidation.ETHUSDT"] + [f"liquidation.{s}USDT" for s in SYMBOLS if s != "BTC" and s != "ETH"]
            })

            async for msg in ws:
                if msg.type == aiohttp.WSMsgType.TEXT:
                    data = msg.json()
                    if data.get("topic", "").startswith("liquidation."):
                        liq = data["data"][0]
                        symbol = liq["symbol"].replace("USDT", "")
                        side = "LONG" if liq["side"] == "Sell" else "SHORT"
                        price = float(liq["price"])
                        size = float(liq["size"])
                        value_usd = price * size

                        if value_usd >= MIN_AMOUNT_USD:
                            text = f"""
LIQ ${value_usd:,.0f}
{symbol}/USDT — <b>{side}</b> ликвидирован
Цена: <code>${price:,.0f}</code>
Объём: {size:,.1f} {symbol}
Биржа: Bybit
                            """.strip()

                            await send_alert(text)
                            print(f"Отправлено: {value_usd:,.0f} {symbol} {side}")

if __name__ == "__main__":
    asyncio.run(main())
