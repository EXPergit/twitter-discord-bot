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

last_tweet_id = None  # 중복 방지

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

        timeline = data.get("timeline", {})
        instructions = timeline.get("instructions", [])

        for inst in instructions:
            if inst.get("type") != "TimelineAddEntries":
                continue

            for entry in inst.get("entries", []):
                content = entry.get("content", {})
                item = content.get("itemContent", {})
                tweet = (
                    item.get("tweet_results", {})
                    .get("result", {})
                )

                tid = tweet.get("rest_id")
                if tid:
                    tweets.append(tid)

        return tweets

    except Exception as e:
        print(f"❌ FxTwitter error: {e}")
        return []

# =========================
# Loop
# =========================
@tasks.loop(minutes=3)
async def fetch_tweets():
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(FX_API, timeout=15) as r:
                print(f"🌐 FxTwitter status: {r.status}")
                if r.status != 200:
                    return []

                data = await r.json()

        tweets = []

        # ✅ Case 1: "tweets" 배열 (가장 흔함)
        if isinstance(data.get("tweets"), list):
            for t in data["tweets"]:
                tid = t.get("id")
                if tid:
                    tweets.append(tid)

        # ✅ Case 2: timeline.tweets 딕셔너리
        elif isinstance(data.get("timeline", {}).get("tweets"), dict):
            tweets = list(data["timeline"]["tweets"].keys())

        print(f"✅ Parsed tweet IDs: {tweets[:5]}")
        return tweets

    except Exception as e:
        print(f"❌ FxTwitter error: {e}")
        return []

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
