import discord
from discord.ext import commands, tasks
import os
import aiohttp
import asyncio
from dotenv import load_dotenv

# =========================
# ENV
# =========================
load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
DISCORD_CHANNEL_ID = int(os.getenv("DISCORD_CHANNEL_ID"))
TWITTER_USERNAME = "jiecia48"

FX_API = f"https://api.fxtwitter.com/{TWITTER_USERNAME}"

# =========================
# Discord
# =========================
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

last_tweet_id = None

# =========================
# FxTwitter Fetch
# =========================
async def fetch_tweets():
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(FX_API, timeout=15) as r:
                print(f"🌐 FxTwitter status: {r.status}")
                if r.status != 200:
                    return []

                data = await r.json()

        tweets = []

        # Case 1: tweets list
        if isinstance(data.get("tweets"), list):
            for t in data["tweets"]:
                tid = t.get("id")
                if tid:
                    tweets.append(tid)

        # Case 2: timeline.tweets dict (fallback)
        elif isinstance(data.get("timeline", {}).get("tweets"), dict):
            tweets = list(data["timeline"]["tweets"].keys())

        print(f"✅ Parsed tweet IDs: {tweets[:5]}")
        return tweets

    except Exception as e:
        print(f"❌ FxTwitter error: {e}")
        return []

# =========================
# Loop (⚠️ on_ready보다 위에!)
# =========================
@tasks.loop(minutes=3)
async def check_tweets():
    global last_tweet_id

    await bot.wait_until_ready()

    try:
        channel = await bot.fetch_channel(DISCORD_CHANNEL_ID)
    except Exception:
        print("❌ Channel not found")
        return

    print("🔍 Checking tweets...")

    tweets = await fetch_tweets()
    if not tweets:
        print("⚠️ No tweets found")
        return

    newest = tweets[0]

    # 첫 실행 시 기준점만 설정
    if last_tweet_id is None:
        last_tweet_id = newest
        print(f"🧠 Initial tweet set: {newest}")
        return

    new_tweets = []
    for tid in tweets:
        if tid == last_tweet_id:
            break
        new_tweets.append(tid)

    for tid in reversed(new_tweets):
        url = f"https://x.com/{TWITTER_USERNAME}/status/{tid}"
        await channel.send(url)
        print(f"📨 Posted: {url}")
        await asyncio.sleep(2)

    if new_tweets:
        last_tweet_id = newest

# =========================
# Events
# =========================
@bot.event
async def on_ready():
    print(f"🤖 Logged in as {bot.user}")
    if not check_tweets.is_running():
        check_tweets.start()

# =========================
# Run
# =========================
if __name__ == "__main__":
    bot.run(DISCORD_TOKEN)
