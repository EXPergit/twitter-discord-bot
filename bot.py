import discord
from discord.ext import commands, tasks
import os
import requests
import re
import asyncio
from dotenv import load_dotenv

# =========================
# 환경 변수 로드
# =========================
load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
DISCORD_CHANNEL_ID = int(os.getenv("DISCORD_CHANNEL_ID"))
TWITTER_USERNAME = "jiecia48"

# =========================
# 디스코드 봇 설정
# =========================
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

# =========================
# 전역 상태
# =========================
posted_tweets = set()

# =========================
# HTTP 헤더 (403 회피용)
# =========================
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.google.com/",
    "Connection": "keep-alive",
}

# =========================
# Twstalker 파서
# =========================
def fetch_tweets_from_twstalker():
    url = f"https://twstalker.com/{TWITTER_USERNAME}"
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)

        print(f"🌐 Twstalker status: {r.status_code}")

        if r.status_code != 200:
            return []

        # 트윗 ID 추출
        tweet_ids = set(re.findall(r"/status/(\d+)", r.text))

        if not tweet_ids:
            print("⚠️ No tweets found in HTML")
            return []

        tweets = sorted(tweet_ids, reverse=True)
        print(f"✅ Tweets found: {tweets[:5]}")

        return tweets[:5]

    except Exception as e:
        print(f"❌ Twstalker error: {e}")
        return []

# =========================
# 주기적 트윗 체크
# =========================
@tasks.loop(minutes=3)
async def check_tweets():
    await bot.wait_until_ready()
    channel = bot.get_channel(DISCORD_CHANNEL_ID)

    if channel is None:
        print("❌ Channel not found")
        return

    print("🔍 Checking for new tweets...")

    tweets = fetch_tweets_from_twstalker()

    if not tweets:
        print("⚠️ No tweets fetched")
        return

    for tweet_id in tweets:
        if tweet_id in posted_tweets:
            continue

        tweet_url = f"https://twitter.com/{TWITTER_USERNAME}/status/{tweet_id}"
        await channel.send(tweet_url)

        posted_tweets.add(tweet_id)
        print(f"📨 Posted: {tweet_url}")

        await asyncio.sleep(2)

# =========================
# 이벤트
# =========================
@bot.event
async def on_ready():
    print(f"🤖 Logged in as {bot.user}")
    check_tweets.start()

# =========================
# 실행
# =========================
if __name__ == "__main__":
    bot.run(DISCORD_TOKEN)# ======================
# MAIN LOOP
# ======================
@tasks.loop(minutes=2)
async def tweet_loop():
    channel = bot.get_channel(DISCORD_CHANNEL_ID)
    print(f"🔗 Channel fetched: {channel}")

    if not channel:
        print("❌ Channel not found")
        return

    tweets = get_tweets_from_html()
    if not tweets:
        print("⚠️ No tweets found from HTML")
        return

    new_count = 0
    for tweet_id in tweets:
        if tweet_id in posted_tweets:
            continue

        url = f"https://fxtwitter.com/{USERNAME}/status/{tweet_id}"
        print(f"✉️ Sending tweet: {tweet_id}")
        await channel.send(url)

        posted_tweets.append(tweet_id)
        new_count += 1

    if new_count:
        save_posted(posted_tweets)
        print(f"📊 Posted {new_count} new tweet(s)")
    else:
        print("✓ No new tweets to post")

@tweet_loop.before_loop
async def before_loop():
    await bot.wait_until_ready()
    delay = random.randint(0, 10)
    print(f"⏱️ Initial delay: {delay}s")
    await asyncio.sleep(delay)

# ======================
# COMMANDS
# ======================
@bot.command()
async def tweet(ctx, url: str):
    match = re.search(r"(?:twitter\.com|x\.com)/([^/]+)/status/(\d+)", url)
    if not match:
        return await ctx.send("❌ Invalid tweet URL")

    user, tweet_id = match.groups()
    fx = f"https://fxtwitter.com/{user}/status/{tweet_id}"

    try:
        await ctx.message.delete()
    except:
        pass

    await ctx.send(fx)

@bot.command()
async def status(ctx):
    await ctx.send(
        f"✅ **Bot Status**\n"
        f"📺 Channel: <#{DISCORD_CHANNEL_ID}>\n"
        f"📝 Tracked tweets: {len(posted_tweets)}\n"
        f"🔄 Loop running: {tweet_loop.is_running()}"
    )

@bot.command()
async def clear(ctx):
    global posted_tweets
    posted_tweets = []
    save_posted(posted_tweets)
    await ctx.send("🧹 Cleared tweet history")

# ======================
# RUN
# ======================
bot.run(DISCORD_TOKEN)
