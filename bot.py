import discord
from discord.ext import commands, tasks
import os
import json
import re
import feedparser
from dotenv import load_dotenv

# =====================
# 환경 변수 로드
# =====================
load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
DISCORD_CHANNEL_ID = int(os.getenv("DISCORD_CHANNEL_ID"))

# =====================
# Discord 설정
# =====================
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# =====================
# 설정값
# =====================
POSTED_FILE = "posted_tweets.json"
TWITTER_USERNAME = "jiecia48"

NITTER_INSTANCES = [
    "https://nitter.net",
    "https://nitter.poast.org",
    "https://nitter.privacyredirect.com",
    "https://xcancel.com",
]

USER_AGENT = "Mozilla/5.0 (DiscordBot RSS Reader)"

# =====================
# 유틸 함수
# =====================
def load_posted():
    if os.path.exists(POSTED_FILE):
        try:
            with open(POSTED_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return []
    return []

def save_posted(tweet_ids):
    with open(POSTED_FILE, "w") as f:
        json.dump(tweet_ids[-100:], f, indent=2)

posted_tweets = load_posted()

# =====================
# RSS 수집 로직
# =====================
def get_tweets_from_rss():
    for base in NITTER_INSTANCES:
        rss_url = f"{base}/{TWITTER_USERNAME}/rss"
        try:
            feed = feedparser.parse(
                rss_url,
                request_headers={"User-Agent": USER_AGENT}
            )

            if not feed.entries:
                print(f"⚠️ RSS 비어 있음: {base}")
                continue

            print(f"✅ RSS 성공: {base}")
            tweets = []

            for entry in feed.entries[:10]:
                match = re.search(r"/status/(\d+)", entry.link)
                if not match:
                    continue

                tweets.append({
                    "id": match.group(1),
                    "link": entry.link,
                    "text": entry.title
                })

            return tweets

        except Exception as e:
            print(f"❌ RSS 오류 ({base}): {e}")

    return []

# =====================
# 이벤트
# =====================
@bot.event
async def on_ready():
    print(f"✅ 로그인 완료: {bot.user}")
    print(f"📺 채널 ID: {DISCORD_CHANNEL_ID}")
    print(f"📝 저장된 트윗 수: {len(posted_tweets)}")
    tweet_loop.start()

# =====================
# 자동 트윗 루프
# =====================
@tasks.loop(minutes=2)
async def tweet_loop():
    channel = bot.get_channel(DISCORD_CHANNEL_ID)

    if not channel:
        print("❌ 채널을 찾을 수 없음")
        return

    print("🔍 트윗 확인 중...")

    tweets = get_tweets_from_rss()
    if not tweets:
        print("⚠️ 가져온 트윗 없음")
        return

    new_count = 0

    for tweet in tweets:
        tweet_id = tweet["id"]

        if tweet_id in posted_tweets:
            continue

        fxtwitter_url = f"https://fxtwitter.com/{TWITTER_USERNAME}/status/{tweet_id}"
        await channel.send(fxtwitter_url)

        posted_tweets.append(tweet_id)
        new_count += 1
        print(f"✅ 전송 완료: {tweet_id}")

    if new_count > 0:
        save_posted(posted_tweets)
        print(f"📊 새 트윗 {new_count}개 전송")
    else:
        print("✓ 새 트윗 없음")

# =====================
# 수동 명령어
# =====================
@bot.command()
async def tweet(ctx, url: str):
    match = re.search(r"(?:twitter\.com|x\.com)/([^/]+)/status/(\d+)", url)
    if not match:
        return await ctx.send("❌ 올바른 트윗 URL이 아닙니다.", delete_after=5)

    username, tweet_id = match.groups()
    fxtwitter_url = f"https://fxtwitter.com/{username}/status/{tweet_id}"

    try:
        await ctx.message.delete()
    except Exception:
        pass

    await ctx.send(fxtwitter_url)
    print(f"✅ 수동 트윗 전송: {tweet_id}")

@bot.command()
async def status(ctx):
    await ctx.send(
        f"✅ **봇 상태**\n"
        f"📺 채널: <#{DISCORD_CHANNEL_ID}>\n"
        f"📝 저장된 트윗: {len(posted_tweets)}\n"
        f"🔄 루프 실행 중: {tweet_loop.is_running()}"
    )

@bot.command()
async def clear(ctx):
    global posted_tweets
    posted_tweets = []
    save_posted(posted_tweets)
    await ctx.send("✅ 트윗 기록 초기화 완료")

# =====================
# 실행
# =====================
bot.run(DISCORD_TOKEN)
