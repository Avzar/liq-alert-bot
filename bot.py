import asyncio
import aiohttp
from telegram import Bot

# ←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←
# СЮДА ВСТАВЬ СВОЙ ТОКЕН И ЧАТ
TOKEN = "7281945672:AAHxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"   # ← твой токен
CHAT_ID = 987654321                                        # ← твой личный ID или -100xxxxxxxxxx (канал)
# ←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←

MIN_AMOUNT = 150000  # только ликвидации от $150k

async def main():
    bot = Bot(token=TOKEN)
    print("Бот ликвидаций запущен — жду жирные лики...")

    async with aiohttp.ClientSession() as session:
        async with session.ws_connect("wss://stream.bybit.com/v5/public/linear") as ws:
            await ws.send_json({"op": "subscribe", "args": ["liquidation.BTCUSDT", "liquidation.ETHUSDT"]})

            async for msg in ws:
                if msg.type != aiohttp.WSMsgType.TEXT:
                    continue
                data = msg.json()
                if not data.get("data"):
                    continue

                liq = data["data"][0]
                symbol = liq["symbol"][:-4]  # убираем USDT
                side = "LONG" if liq["side"] == "Sell" else "SHORT"
                price = float(liq["price"])
                size = float(liq["size"])
                value = price * size

                if value >= MIN_AMOUNT:
                    text = f"""
LIQ ${value:,.0f}
{symbol}/USDT — <b>{side}</b> ликвидирован
Цена: <code>${price:,.0f}</code>
Объём: {size:.2f} {symbol}
Bybit • только что
                    """.strip()

                    await bot.send_message(chat_id=CHAT_ID, text=text, parse_mode="HTML")
                    print(f"Отправлено: {value:,.0f} {symbol} {side}")

asyncio.run(main())
