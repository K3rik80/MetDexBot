import asyncio
import requests
import time
from telegram import Bot
from datetime import datetime, timedelta

# Telegram Bot Token und Chat ID
TELEGRAM_TOKEN = ''
CHAT_ID = ''

# Dexscreener API URL für neue Token-Paare in Meteora
DEXSCREENER_API_URL = 'https://api.dexscreener.com/latest/dex/solana/search?q=Meteora'

# Erstelle eine Instanz des Telegram Bots
bot = Bot(token=TELEGRAM_TOKEN)

async def get_dex_data():
    try:
        response = requests.get(DEXSCREENER_API_URL)
        if response.status_code == 200:
            data = response.json()
            return data
        else:
            print("Fehler beim Abrufen der Daten von der API. Statuscode:", response.status_code)
            return None
    except Exception as e:
        print("Fehler beim Abrufen der Daten von der API:", e)
        return None

def filter_data(data):
    try:
        if data is None or 'pairs' not in data or not isinstance(data['pairs'], list):
            print("Fehler beim Filtern der Daten: Datenformat ungültig.")
            print("Inhalt von 'data':", data)
            return []

        filtered_pools = []
        current_time = datetime.utcnow()
        one_hour_ago = current_time - timedelta(hours=1)

        for pool in data['pairs']:
            if pool['chainId'] == 'solana' and pool['dexId'] == 'meteora' and 'DYN' not in pool['labels']:
                volume_1h = pool['volume']['h1']
                liquidity_usd = pool['liquidity']['usd']
                pair_created_at = datetime.utcfromtimestamp(pool['pairCreatedAt'] / 1000)

                # Deine Kriterien für die Benachrichtigung
                if volume_1h > 10 and liquidity_usd > 100 and pair_created_at > one_hour_ago:
                    filtered_pools.append({
                        'url': pool['url'],
                        'volume_1h': volume_1h,
                        'liquidity_usd': liquidity_usd
                    })
        return filtered_pools
    except Exception as e:
        print("Fehler beim Filtern der Daten:", e)
        return []

async def send_notification(pools):
    try:
        for pool in pools:
            message = f"Neuer Pool gefunden!\nVolume (1h): {pool['volume_1h']}\nLiquidity: {pool['liquidity_usd']}\nURL: {pool['url']}"
            await bot.send_message(chat_id=CHAT_ID, text=message)
    except Exception as e:
        print("Fehler beim Senden der Benachrichtigung:", e)

async def job():
    print("Job wird ausgeführt...")
    data = await get_dex_data()
    if data:
        print("Daten erfolgreich abgerufen.")
        filtered_pools = filter_data(data)
        if filtered_pools:
            print("Filterung abgeschlossen. Anzahl gefilterter Pools:", len(filtered_pools))
            await send_notification(filtered_pools)
        else:
            print("Keine passenden Pools gefunden.")
    else:
        print("Keine Daten von der API erhalten.")

# Plane den Job alle 1 Minute (kannst du anpassen)
async def main():
    while True:
        await job()
        await asyncio.sleep(60)

if __name__ == "__main__":
    asyncio.run(main())
