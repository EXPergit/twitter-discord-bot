import discord
from discord.ext import tasks
import os
import json
import asyncio
from datetime import datetime
from dotenv import load_dotenv
import snscrape.modules.twitter as sntwitter
import time

load_dotenv()

DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
DISCORD_CHANNEL_ID = os.getenv("DISCORD_CHANNEL_ID")
TWITTER_USERNAME = os.getenv("TWITTER_USERNAME", "nikhilraj__")
POLL_INTERVAL_SECONDS = int(os.getenv("POLL_INTERVAL_SECONDS", "60"))

LAST_TWEET_FILE = "last_tweet.json"


class TwitterDiscordBot(discord.Client):
    def __init__(self):
        intents = discord.Intents.default()
        super().__init__(intents=intents)
        
        self.channel = None
        self.last_tweet_id = self.load_last_tweet_id()
        self.last_request_time = 0

    def load_last_tweet_id(self):
        if os.path.exists(LAST_TWEET_FILE):
            try:
                with open(LAST_TWEET_FILE, "r") as f:
                    return json.load(f).get("last_tweet_id")
            except Exception as e:
                print(f"⚠️ Error loading last tweet: {e}")
        return None

    def save_last_tweet_id(self, tweet_id):
        try:
            with open(LAST_TWEET_FILE, "w") as f:
                json.dump({"last_tweet_id": tweet_id}, f)
            self.last_tweet_id = tweet_id
        except Exception as e:
            print(f"⚠️ Error saving last tweet: {e}")

    async def on_ready(self):
        print(f"✅ Logged in as {self.user}")

        if not DISCORD_CHANNEL_ID:
            print("❌ DISCORD_CHANNEL_ID not set")
            await self.close()
            return

        self.channel = self.get_channel(int(DISCORD_CHANNEL_ID))
        if not self.channel:
            print(f"❌ Channel {DISCORD_CHANNEL_ID} not found")
            await self.close()
            return

        print(f"📡 Monitoring Twitter @{TWITTER_USERNAME}")
        print(f"🔑 Using snscrape (FREE - no API keys needed)")
        print(f"⏱️ Poll interval: {POLL_INTERVAL_SECONDS}s")

        self.check_tweets.start()

    @tasks.loop(seconds=POLL_INTERVAL_SECONDS)
    async def check_tweets(self):
        print("🔍 Checking for new tweets…")

        tweets = await self.get_new_tweets()
        if not tweets:
            print("📭 No new tweets")
            return

        print(f"📬 Found {len(tweets)} new tweet(s)")
        for tweet in tweets:
            await self.post_tweet_to_discord(tweet)
            await asyncio.sleep(1)

    @check_tweets.before_loop
    async def before_check_tweets(self):
        await self.wait_until_ready()

    async def get_new_tweets(self):
        """Fetch tweets using snscrape (completely FREE)"""
        # Rate limiting to avoid overwhelming Twitter
        now = time.time()
        min_interval = 10
        if now - self.last_request_time < min_interval:
            wait_time = min_interval - (now - self.last_request_time)
            await asyncio.sleep(wait_time)
        
        self.last_request_time = time.time()
        
        try:
            print(f"🌐 Fetching tweets from @{TWITTER_USERNAME} via snscrape...")
            
            tweets = []
            
            # Try to scrape with retry logic
            for retry in range(3):
                try:
                    # Get tweets from the user's timeline
                    scraper = sntwitter.TwitterProfileScraper(TWITTER_USERNAME)
                    
                    tweet_count = 0
                    for tweet in scraper.get_items():
                        # Limit to 10 tweets per check
                        if tweet_count >= 10:
                            break
                        
                        tweet_id = str(tweet.id)
                        
                        # Skip tweets we've already seen
                        if self.last_tweet_id and int(tweet_id) <= int(self.last_tweet_id):
                            continue
                        
                        tweet_text = tweet.content if tweet.content else ""
                        
                        # Skip very short tweets (likely errors)
                        if len(tweet_text.strip()) < 3:
                            continue
                        
                        tweets.append({
                            'id': tweet_id,
                            'content': tweet_text[:280],
                            'url': f"https://twitter.com/{TWITTER_USERNAME}/status/{tweet_id}",
                            'created_at': tweet.date
                        })
                        
                        tweet_count += 1
                    
                    if tweets:
                        print(f"✅ Successfully fetched {len(tweets)} new tweet(s)")
                        self.save_last_tweet_id(tweets[0]["id"])
                        return tweets
                    else:
                        print(f"⏭️ No new tweets found")
                        return []
                    
                except Exception as e:
                    error_msg = str(e)
                    
                    # Check if it's a rate limit or blocking error
                    if "blocked" in error_msg.lower() or "429" in error_msg or "rate" in error_msg.lower():
                        wait_time = (2 ** retry) * 5  # Exponential backoff: 5s, 10s, 20s
                        print(f"⚠️ Rate limited/blocked. Retry {retry + 1}/3 in {wait_time}s...")
                        await asyncio.sleep(wait_time)
                        continue
                    else:
                        print(f"❌ Error on attempt {retry + 1}: {error_msg[:80]}")
                        if retry < 2:
                            await asyncio.sleep(2 ** retry)
                            continue
                        else:
                            raise
            
            return []

        except Exception as e:
            print(f"❌ Failed to fetch tweets: {str(e)[:100]}")
            return []

    async def post_tweet_to_discord(self, tweet):
        try:
            embed = discord.Embed(
                description=tweet.get("content", "")[:2000],
                color=0x1DA1F2,
                timestamp=tweet.get('created_at', datetime.now()),
                url=tweet.get("url", "")
            )

            embed.set_author(
                name=f"@{TWITTER_USERNAME}",
                url=f"https://twitter.com/{TWITTER_USERNAME}",
            )

            embed.set_footer(text="Twitter • via snscrape")

            await self.channel.send(embed=embed)
            print(f"✅ Posted tweet {tweet['id']} to Discord")

        except Exception as e:
            print(f"❌ Error posting tweet: {e}")


def validate_config():
    errors = []
    
    if not DISCORD_BOT_TOKEN:
        errors.append("DISCORD_BOT_TOKEN is required")
    if not DISCORD_CHANNEL_ID:
        errors.append("DISCORD_CHANNEL_ID is required")
    if not TWITTER_USERNAME:
        errors.append("TWITTER_USERNAME is required")
    
    if errors:
        print("❌ Configuration errors:")
        for error in errors:
            print(f"  - {error}")
        return False
    
    return True


if __name__ == "__main__":
    print("🚀 Starting Twitter to Discord bot (FREE - snscrape)...")
    
    if not validate_config():
        exit(1)
    
    bot = TwitterDiscordBot()
    bot.run(DISCORD_BOT_TOKEN)
