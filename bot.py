import discord
from discord.ext import commands, tasks
import os
import requests
import json
from pathlib import Path
from urllib.parse import quote
from dotenv import load_dotenv
import re

# ===============================
# LOAD ENV + DEBUG PRINT
# ===============================

load_dotenv()

print("=== TOKEN DEBUG ===")
print("TOKEN:", os.getenv("TWITTER_BEARER_TOKEN"))
print("LENGTH:", len(os.getenv("TWITTER_BEARER_TOKEN") or "NONE"))
print("===================")

DISCORD_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
DISCORD_CHANNEL_ID = int(os.getenv("DISCORD_CHANNEL_ID", 0))

# YOUR DOMAIN SERVICES
EMBED_SERVER_URL = "https://ridiculous-cindra-oknonononon-1d15a38f.koyeb.app/"
CDN_PROXY = "https://cdn.ahazek.org/get?url="

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
}

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

POSTED_TWEETS_FILE = "posted_tweets.json"


# ===============================
# LOAD / SAVE
# ===============================

def load_posted():
    if Path(POSTED_TWEETS_FILE).exists():
        try:
            return json.load(open(POSTED_TWEETS_FILE))
        except:
            return {}
    return {}

def save_posted(data):
    json.dump(data, open(POSTED_TWEETS_FILE, "w"), indent=2)


# ===============================
# VXTwitter Fetch (Primary Source)
# ===============================

def get_tweets(username):
    """
    ALWAYS use VXTwitter because your Twitter API token does not have
    access to v2 tweet endpoints. VXTwitter returns tweet text, images,
    video URLs, and stats reliably.
    """
    try:
        print("USING VX TWITTER FOR:", username)

        r = requests.get(
            f"https://api.vxtwitter.com/user/{username}",
            timeout=10,
            headers=HEADERS
        )

        if r.status_code != 200:
            print("VX ERROR:", r.status_code)
            return []

        data = r.json()
        tweets = []

        for t in data.get("tweets", [])[:5]:
            media = []
            for m in t.get("media", []):
                media.append({
                    "type": m.get("type"),
                    "url": m.get("url"),
                    "preview_image_url": m.get("thumbnail_url"),
                    "video_url": m.get("url") if m.get("type") in ["video", "gif"] else None
                })

            tweets.append({
                "id": str(t["id"]),
                "text": t["text"],
                "url": t["url"],
                "metrics": t.get("stats", {}),
                "media": media
            })

        print("VX RETURNED IDS:", [tw["id"] for tw in tweets])
        return tweets

    except Exception as e:
        print("VX CRASH:", e)
        return []


# ===============================
# AUTO POST SYSTEM
# ===============================

async def send_tweet(tweet, channel, posted, force=False):
    if not force and tweet["id"] in posted:
        return

    image_url = None
    video_url = None

    # extract media
    for m in tweet.get("media", []):
        if m["type"] == "photo":
            image_url = m["url"]
        elif m["type"] in ["video", "animated_gif", "gif"]:
            raw = m["video_url"]
            video_url = CDN_PROXY + quote(raw, safe="")
            image_url = m.get("preview_image_url", image_url)

    # basic embed
    embed = discord.Embed(description=tweet["text"], color=0x1DA1F2)
    embed.set_author(
        name="NFL (@NFL)",
        url=tweet["url"],
        icon_url="https://abs.twimg.com/icons/apple-touch-icon-192x192.png"
    )

    stats = tweet["metrics"]
    embed.add_field(name="💬", value=stats.get("reply_count", 0))
    embed.add_field(name="🔁", value=stats.get("retweet_count", 0))
    embed.add_field(name="❤️", value=stats.get("like_count", 0))
    embed.add_field(name="👁", value=stats.get("view_count", 0))

    if image_url:
        embed.set_image(url=image_url)

    await channel.send(embed=embed)

    # auto-poster sends video as separate message
    if video_url:
        await channel.send(video_url)

    posted[tweet["id"]] = True
    save_posted(posted)


# ===============================
# STARTUP
# ===============================

async def startup():
    await bot.wait_until_ready()
    ch = bot.get_channel(DISCORD_CHANNEL_ID)
    if not ch:
        print("Channel not found")
        return

    tweets = get_tweets("NFL")
    posted = load_posted()

    # always post top 2 on restart
    for t in tweets[:2]:
        await send_tweet(t, ch, posted, force=True)

    save_posted(posted)


@bot.event
async def on_ready():
    print("Logged in as:", bot.user)
    bot.loop.create_task(startup())
    tweet_loop.start()


@tasks.loop(minutes=1)
async def tweet_loop():
    ch = bot.get_channel(DISCORD_CHANNEL_ID)
    posted = load_posted()
    tweets = get_tweets("NFL")

    for t in tweets:
        await send_tweet(t, ch, posted)

    save_posted(posted)


# ===============================
# !tweet COMMAND (FixTweet Style)
# ===============================

TWEET_URL_REGEX = r"(?:twitter\.com|x\.com)/([^/]+)/status/(\d+)"

@bot.command()
async def tweet(ctx, url: str):
    match = re.search(TWEET_URL_REGEX, url)
    if not match:
        return await ctx.send("❌ Invalid Twitter/X link.")

    username = match.group(1)
    tweet_id = match.group(2)

    print("USERNAME EXTRACTED:", username)
    print("TWEET ID:", tweet_id)

    tweets = get_tweets(username)
    print("FOUND TWEET IDS:", [str(t["id"]) for t in tweets])

    target = next((t for t in tweets if str(t["id"]) == str(tweet_id)), None)

    if not target:
        return await ctx.send("❌ Tweet not found.")

    image_url = None
    video_url = None

    for m in target.get("media", []):
        if m["type"] == "photo":
            image_url = m["url"]
        elif m["type"] in ["video", "animated_gif", "gif"]:
            raw = m["video_url"]
            video_url = CDN_PROXY + quote(raw, safe="")
            image_url = m.get("preview_image_url", image_url)

    embed_url = (
        f"{EMBED_SERVER_URL}"
        f"?title=@{username}"
        f"&name={username}"
        f"&handle={username}"
        f"&text={quote(target['text'])}"
        f"&likes={target['metrics'].get('like_count', 0)}"
        f"&retweets={target['metrics'].get('retweet_count', 0)}"
        f"&replies={target['metrics'].get('reply_count', 0)}"
        f"&views={target['metrics'].get('view_count', 0)}"
    )

    if image_url:
        embed_url += "&image=" + quote(image_url)
    if video_url:
        embed_url += "&video=" + quote(video_url)

    print("EMBED_URL:", embed_url)

    await ctx.send(embed_url)


# ===============================
# RUN THE BOT
# ===============================

bot.run(DISCORD_TOKEN)
