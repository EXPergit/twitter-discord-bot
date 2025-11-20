import discord
from discord.ext import tasks
import os
import json
import asyncio
from datetime import datetime
from dotenv import load_dotenv
from zenrows import ZenRowsClient
from bs4 import BeautifulSoup
import re

load_dotenv()

DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
DISCORD_CHANNEL_ID = os.getenv("DISCORD_CHANNEL_ID")
TWITTER_USERNAME = os.getenv("TWITTER_USERNAME", "nikhilraj__")
ZENROWS_API_KEY = os.getenv("ZENROWS_API_KEY")
POLL_INTERVAL_SECONDS = int(os.getenv("POLL_INTERVAL_SECONDS", "60"))

LAST_TWEET_FILE = "last_tweet.json"


class TwitterDiscordBot(discord.Client):
    def __init__(self):
        intents = discord.Intents.default()
        super().__init__(intents=intents)
        
        self.channel = None
        self.last_tweet_id = self.load_last_tweet_id()
        self.client = ZenRowsClient(ZENROWS_API_KEY) if ZENROWS_API_KEY else None

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
        print(f"🔑 Using ZenRows API with JS rendering")
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
        if not self.client:
            print("❌ ZenRows client not initialized")
            return []

        try:
            url = f"https://twitter.com/{TWITTER_USERNAME}"
            
            print(f"🌐 Fetching {url} via ZenRows...")
            response = self.client.get(url, params={
                "js_render": "true",
                "premium_proxy": "true"
            })
            
            html = response.text
            print(f"📄 Received {len(html)} bytes of HTML")
            
            tweets = self.parse_tweets_from_html(html)
            print(f"✅ Parsed {len(tweets)} tweets from HTML")
            
            if tweets:
                self.save_last_tweet_id(tweets[0]["id"])
            
            return tweets

        except Exception as e:
            print(f"❌ Error fetching tweets: {e}")
            return []

    def parse_tweets_from_html(self, html):
        """Parse tweets from Twitter HTML"""
        tweets = []
        
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # Debug: Check what's actually in the HTML
            all_links = soup.find_all('a', href=True)
            status_links = [l for l in all_links if re.search(r'/status/\d+', l.get('href', ''))]
            print(f"📊 Total links: {len(all_links)}, Status links: {len(status_links)}")
            
            if status_links:
                print(f"📝 Sample status links: {[l['href'][:80] for l in status_links[:3]]}")
            
            # Try to find tweet data in script tags
            script_tags = soup.find_all('script', {'type': 'application/json'})
            print(f"🔍 Found {len(script_tags)} JSON script tags")
            
            for script in script_tags:
                try:
                    data = json.loads(script.string)
                    tweets.extend(self._extract_tweets_from_json(data))
                except:
                    pass
            
            # Fallback: Extract tweets from status links
            if not tweets and status_links:
                print("🔄 Extracting tweets from status links...")
                
                seen_ids = set()
                for link in status_links[:10]:
                    href = link.get('href', '')
                    match = re.search(r'/status/(\d+)', href)
                    if not match:
                        continue
                    
                    tweet_id = match.group(1)
                    
                    if tweet_id in seen_ids:
                        continue
                    seen_ids.add(tweet_id)
                    
                    if self.last_tweet_id and int(tweet_id) <= int(self.last_tweet_id):
                        continue
                    
                    # Get parent container and extract text
                    parent = link.find_parent(['div', 'article', 'section'])
                    if parent:
                        text = parent.get_text(strip=True)[:280]
                        if text and len(text) > 10:
                            tweets.append({
                                'id': tweet_id,
                                'content': text,
                                'url': f"https://twitter.com/{TWITTER_USERNAME}/status/{tweet_id}",
                                'media_url': None
                            })
            
            print(f"💾 Total tweets extracted: {len(tweets)}")
            return list(reversed(tweets))[:10]
            
        except Exception as e:
            print(f"❌ Error parsing HTML: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def _extract_tweets_from_json(self, data, tweets=None):
        """Recursively extract tweet objects from JSON structure"""
        if tweets is None:
            tweets = []
        
        if isinstance(data, dict):
            # Check if this looks like a tweet object
            if 'id_str' in data and 'text' in data:
                tweet_id = str(data.get('id_str', ''))
                text = data.get('text', '')
                if tweet_id and text and not (self.last_tweet_id and int(tweet_id) <= int(self.last_tweet_id)):
                    tweets.append({
                        'id': tweet_id,
                        'content': text[:280],
                        'url': f"https://twitter.com/{TWITTER_USERNAME}/status/{tweet_id}",
                        'media_url': None
                    })
            
            for value in data.values():
                self._extract_tweets_from_json(value, tweets)
        
        elif isinstance(data, list):
            for item in data[:50]:  # Limit to prevent infinite recursion
                self._extract_tweets_from_json(item, tweets)
        
        return tweets

    async def post_tweet_to_discord(self, tweet):
        try:
            embed = discord.Embed(
                description=tweet.get("content", ""),
                color=0x1DA1F2,
                timestamp=datetime.now(),
                url=tweet.get("url", "")
            )

            embed.set_author(
                name=f"@{TWITTER_USERNAME}",
                url=f"https://twitter.com/{TWITTER_USERNAME}",
            )

            embed.set_footer(text="Twitter")

            content = tweet.get("media_url") or None

            await self.channel.send(content=content, embed=embed)
            print(f"✅ Posted tweet {tweet['id']} to Discord")

        except Exception as e:
            print(f"❌ Error posting tweet: {e}")


def validate_config():
    errors = []
    
    if not DISCORD_BOT_TOKEN:
        errors.append("DISCORD_BOT_TOKEN is required")
    if not DISCORD_CHANNEL_ID:
        errors.append("DISCORD_CHANNEL_ID is required")
    if not ZENROWS_API_KEY:
        errors.append("ZENROWS_API_KEY is required")
    
    if errors:
        print("❌ Configuration errors:")
        for error in errors:
            print(f"  - {error}")
        return False
    
    return True


if __name__ == "__main__":
    print("🚀 Starting Twitter to Discord bot (ZenRows)...")
    
    if not validate_config():
        exit(1)
    
    bot = TwitterDiscordBot()
    bot.run(DISCORD_BOT_TOKEN)
