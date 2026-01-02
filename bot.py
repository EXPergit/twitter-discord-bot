import discord
from discord.ext import commands, tasks
import os
import requests
import asyncio
from dotenv import load_dotenv

# =========================
# ENV
# =========================
load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
DISCORD_CHANNEL_ID = int(os.getenv("DISCORD_CHANNEL_ID"))
TWITTER_USERNAME = "jiecia48"

# =========================
# Discord
# =========================
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

posted_tweets = set()

# =========================
# FxTwitter API
# =========================
FX_API = f"https://api.fxtwitter.com/{TWITTER_USERNAME}"

def fetch_tweets():
    try:
        r = requests.get(FX_API, timeout=15)
        print(f"🌐 FxTwitter status: {r.status_code}")

        if r.status_code != 200:
            return []

        data = r.json()

        tweets = []
        for t in data.get("tweets", []):
            tweet_id = str(t.get("id"))
            if tweet_id:
                tweets.append(tweet_id)

        print(f"✅ Tweets fetched: {tweets[:5]}")
        return tweets[:5]

    except Exception as e:
        print(f"❌ FxTwitter error: {e}")
        return []

# =========================
# Loop
# =========================
@tasks.loop(minutes=3)
async def check_tweets():
    await bot.wait_until_ready()
    channel = bot.get_channel(DISCORD_CHANNEL_ID)

    if not channel:
        print("❌ Channel not found")
        return

    print("🔍 Checking tweets...")

    tweets = fetch_tweets()
    if not tweets:
        print("⚠️ No tweets")
        return

    for tid in tweets:
        if tid in posted_tweets:
            continue

        url = f"https://twitter.com/{TWITTER_USERNAME}/status/{tid}"
        await channel.send(url)

        posted_tweets.add(tid)
        print(f"📨 Posted: {url}")
        await asyncio.sleep(2)

# =========================
# Events
# =========================
@bot.event
async def on_ready():
    print(f"🤖 Logged in as {bot.user}")
    check_tweets.start()

# =========================
# Run
# =========================
if __name__ == "__main__":
    bot.run(DISCORD_TOKEN)
