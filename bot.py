import discord
from discord.ext import commands, tasks
import os
import requests
import json
import asyncio
import time
from datetime import datetime
from pathlib import Path
from urllib.parse import quote
from dotenv import load_dotenv

load_dotenv()

DISCORD_TOKEN = os.getenv('DISCORD_BOT_TOKEN')
DISCORD_CHANNEL_ID = int(os.getenv('DISCORD_CHANNEL_ID', 0))
TWITTER_BEARER_TOKEN = os.getenv('TWITTER_BEARER_TOKEN')

# Embed server URL
EMBED_SERVER_URL = os.getenv('REPLIT_DOMAINS', '').split(',')[0].strip() if os.getenv('REPLIT_DOMAINS') else 'localhost:5000'
if EMBED_SERVER_URL:
    EMBED_SERVER_URL = f"https://{EMBED_SERVER_URL.strip()}" if "://" not in EMBED_SERVER_URL else EMBED_SERVER_URL

# Discord intents
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# JSON for posted tweets
POSTED_TWEETS_FILE = "posted_tweets.json"


# ------------------ Utility: Load/Save ------------------

def load_posted_tweets():
    if Path(POSTED_TWEETS_FILE).exists():
        try:
            return json.load(open(POSTED_TWEETS_FILE))
        except:
            return {}
    return {}


def save_posted_tweets(data):
    json.dump(data, open(POSTED_TWEETS_FILE, "w"), indent=2)


# ------------------ Twitter API Fetcher ------------------

def get_tweets(username):
    """Fetch latest tweets from Twitter API."""
    if not TWITTER_BEARER_TOKEN:
        print("❌ No Twitter Bearer Token found.")
        return []

    try:
        headers = {"Authorization": f"Bearer {TWITTER_BEARER_TOKEN}"}
        max_retries = 3

        user_id = None

        # ------------------ USER LOOKUP ------------------
        for attempt in range(max_retries):
            url = f"https://api.twitter.com/2/users/by/username/{username}"
            r = requests.get(url, headers=headers, timeout=10)

            if r.status_code == 429:
                wait = 2 ** attempt
                print(f"⏳ Rate limited (user lookup). Waiting {wait}s…")
                time.sleep(wait)
                continue

            if r.status_code != 200:
                print(f"❌ User lookup failed [{r.status_code}]")
                return []

            user_id = r.json()["data"]["id"]
            break

        if not user_id:
            print("❌ Failed to retrieve user_id after retries.")
            return []

        # ------------------ FETCH TWEETS ------------------
        tweets_url = f"https://api.twitter.com/2/users/{user_id}/tweets"
        params = {
            "max_results": 5,
            "tweet.fields": "created_at,public_metrics",
            "expansions": "attachments.media_keys,author_id",
            "media.fields": "media_key,type,url,preview_image_url,variants,public_metrics"
        }

        for attempt in range(max_retries):
            r = requests.get(tweets_url, headers=headers, params=params, timeout=10)

            if r.status_code == 429:
                wait = 2 ** attempt
                print(f"⏳ Rate limited (tweets fetch). Waiting {wait}s…")
                time.sleep(wait)
                continue

            if r.status_code != 200:
                print(f"❌ Tweets fetch failed [{r.status_code}]")
                return []

            break

        data = r.json()
        tweets = []
        media_dict = {}

        if "includes" in data and "media" in data["includes"]:
            for m in data["includes"]["media"]:
                media_dict[m["media_key"]] = m

        if "data" in data:
            for t in data["data"]:
                medias = []

                for key in t.get("attachments", {}).get("media_keys", []):
                    if key in media_dict:
                        m = media_dict[key]
                        video_url = None

                        if m.get("type") in ["video", "animated_gif"] and "variants" in m:
                            for v in m["variants"]:
                                if v.get("content_type") == "video/mp4":
                                    video_url = v.get("url")
                                    break

                        medias.append({
                            "type": m.get("type"),
                            "url": m.get("url"),
                            "preview_image_url": m.get("preview_image_url"),
                            "video_url": video_url
                        })

                tweets.append({
                    "id": t["id"],
                    "text": t["text"],
                    "url": f"https://x.com/{username}/status/{t['id']}",
                    "created_at": t.get("created_at", ""),
                    "metrics": t.get("public_metrics", {}),
                    "media": medias
                })

        return tweets

    except Exception as e:
        print(f"❌ Error fetching tweets: {e}")
        return []


# ------------------ Posting Logic ------------------

async def post_one_tweet(tweet, channel, posted, force=False):
    """Post one tweet to Discord."""

    if not force and tweet["id"] in posted:
        return

    image_url = None
    video_url = None

    if tweet["media"]:
        for media in tweet["media"]:
            if media["type"] == "photo":
                image_url = media.get("url")
            elif media["type"] in ["video", "animated_gif"]:
                video_url = media.get("video_url")
                image_url = media.get("preview_image_url", image_url)

    # Build FixTweet-style embed URL
    embed_url = (
        f"{EMBED_SERVER_URL}"
        f"?title=@NFL"
        f"&name=NFL"
        f"&handle=NFL"
        f"&text={quote(tweet['text'])}"
        f"&likes={tweet['metrics'].get('like_count', 0)}"
        f"&retweets={tweet['metrics'].get('retweet_count', 0)}"
        f"&replies={tweet['metrics'].get('reply_count', 0)}"
        f"&views={tweet['metrics'].get('impression_count', 0)}"
    )

    if image_url:
        embed_url += f"&image={quote(image_url)}"
    if video_url:
        embed_url += f"&video={quote(video_url)}"

    # Discord embed
    embed = discord.Embed(description=f"[View Tweet]({tweet['url']})", color=0x1F51BA)
    embed.set_author(name="@NFL", url=tweet["url"])

    m = tweet["metrics"]
    metrics_text = (
        f"💬 {m.get('reply_count', 0)}   "
        f"🔄 {m.get('retweet_count', 0)}   "
        f"❤️ {m.get('like_count', 0)}   "
        f"👁️ {m.get('impression_count', 0)}"
    )
    embed.add_field(name=metrics_text, value="", inline=False)

    if image_url:
        embed.set_image(url=image_url)
    if video_url:
        embed.set_video(url=video_url)

    embed.set_footer(text="X.com")

    await channel.send(embed=embed, content=embed_url)

    posted[tweet["id"]] = True
    print(f"✅ Posted tweet {tweet['id']}")


async def fetch_startup_tweets():
    """Fetch tweets on startup with exponential backoff (max 12 retries)."""
    channel = bot.get_channel(DISCORD_CHANNEL_ID)
    if not channel:
        print("❌ No channel found.")
        return

    print("📌 Fetching top 2 tweets…")

    max_retries = 12
    for attempt in range(max_retries):
        tweets = get_tweets("NFL")

        if tweets:
            print("✅ Startup tweets fetched.")
            posted = load_posted_tweets()
            for t in tweets[:2]:
                await post_one_tweet(t, channel, posted, force=True)
            save_posted_tweets(posted)
            return

        if attempt < max_retries - 1:
            wait = min(5 * (2 ** attempt), 300)  # Exponential backoff, max 5min
            print(f"⏳ Rate limited. Retry {attempt + 1}/{max_retries} in {wait}s…")
            await asyncio.sleep(wait)
    
    print("❌ Failed to fetch tweets after max retries. Giving up for now.")


# ------------------ Discord Events ------------------

@bot.event
async def on_ready():
    print(f"✅ Bot logged in as {bot.user}")
    print(f"📢 Target channel: {DISCORD_CHANNEL_ID}")

    await fetch_startup_tweets()

    if not tweet_checker.is_running():
        tweet_checker.start()
        print("🔄 Tweet checker started")


@tasks.loop(minutes=5)
async def tweet_checker():
    channel = bot.get_channel(DISCORD_CHANNEL_ID)
    if not channel:
        return

    posted = load_posted_tweets()
    tweets = get_tweets("NFL")

    if not tweets:
        print("ℹ️ No tweets found in loop.")
        return

    for tweet in tweets:
        await post_one_tweet(tweet, channel, posted, force=False)

    save_posted_tweets(posted)


@tweet_checker.before_loop
async def before_tweet_checker():
    await bot.wait_until_ready()


@bot.command()
async def check(ctx):
    await ctx.send("🔍 Checking tweets manually…")
    tweets = get_tweets("NFL")
    await ctx.send(f"Found {len(tweets)} tweets.")


# ------------------ Start Bot ------------------

if __name__ == "__main__":
    if not DISCORD_TOKEN or not DISCORD_CHANNEL_ID or not TWITTER_BEARER_TOKEN:
        print("❌ Missing env variables.")
        exit(1)

    print("🚀 Starting Twitter bot…")
    bot.run(DISCORD_TOKEN)
