import asyncio
import aiohttp
import time

# ←←←←←←←←←←←←←←←←←←←←←←←←
TOKEN   = "8496146526:AAEneNpQgY2py4ALB1ws-HMLrKqUoX7psfs"  # твой токен
CHAT_ID = 2113159677                                         # твой личный ID или -100xxxxxxxxxx (канал)
# ←←←←←←←←←←←←←←←←←←←←←←←←

MIN_LIQ_USD = 20000          # минимальная ликвидация
CHECK_INTERVAL = 1800         # 30 минут = 1800 секунд
SYMBOLS = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "DOGEUSDT", "XRPUSDT"]

async def send(msg):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": msg, "parse_mode": "HTML"}
    async with aiohttp.ClientSession() as s:
        async with s.post(url, json=payload):
            pass

last_heartbeat = 0

async def main():
    global last_heartbeat
    print("Бот ликвидаций запущен — жду жирные лики...")
    await send("Бот ликвидаций запущен и работает 24/7")

    async with aiohttp.ClientSession() as session:
        async with session.ws_connect("wss://stream.bybit.com/v5/public/linear") as ws:
            await ws.send_json({"op": "subscribe", "args": [f"liquidation.{s}" for s in SYMBOLS]})

            async for msg in ws:
                if msg.type != aiohttp.WSMsgType.TEXT:
                    continue
                try:
                    data = msg.json()
                    if "data" not in data:
                        continue
                    liq = data["data"][0]
                    symbol = liq["symbol"][:-4]
                    side = "LONG" if liq["side"] == "Sell" else "SHORT"
                    price = float(liq["price"])
                    size = float(liq["size"])
                    value = price * size

                    if value >= MIN_LIQ_USD:
                        text = f"""
LIQ ${value:,.0f}
{symbol}/USDT — <b>{side}</b> ликвидирован
Цена: <code>${price:,.0f}</code>
Объём: {size:.3f} {symbol}
Bybit • только что
                        """.strip()
                        await send(text)
                        last_heartbeat = time.time()  # сбрасываем таймер

                except Exception as e:
                    continue

                # Heartbeat каждые 30 минут, если тишина
                if time.time() - last_heartbeat > CHECK_INTERVAL:
                    await send("Я жив! Ликвидаций > $200k пока нет")
                    last_heartbeat = time.time()

asyncio.run(main())
