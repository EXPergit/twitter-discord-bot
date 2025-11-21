import discord
from discord.ext import commands, tasks
import os
import json
import asyncio
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# TwiKit for Twitter scraping
from twikit import Client, TooManyRequests

load_dotenv()

DISCORD_TOKEN = os.getenv('DISCORD_BOT_TOKEN')
DISCORD_CHANNEL_ID = int(os.getenv('DISCORD_CHANNEL_ID', 0))

# State files
FOLLOWED_FILE = 'followed.json'
COOKIES_FILE = 'cookies.json'

def load_followed():
    """Load followed accounts"""
    if Path(FOLLOWED_FILE).exists():
        try:
            with open(FOLLOWED_FILE, 'r') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_followed(data):
    """Save followed accounts"""
    with open(FOLLOWED_FILE, 'w') as f:
        json.dump(data, f, indent=2)

# Initialize Discord bot
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# TwiKit client
client = Client('en-US')
followed = load_followed()
client_ready = False

@bot.event
async def on_ready():
    global client_ready
    print(f'✅ Bot logged in as {bot.user}')
    print(f'📢 Target channel: {DISCORD_CHANNEL_ID}')
    print(f'📌 Followed accounts: {list(followed.keys())}')
    
    # Initialize TwiKit client
    if not client_ready:
        try:
            # Try to load cookies if they exist
            if Path(COOKIES_FILE).exists():
                try:
                    cookies = json.load(open(COOKIES_FILE))
                    if cookies and isinstance(cookies, list) and len(cookies) > 0:
                        print('🔄 Loading X.com cookies...')
                        for cookie in cookies:
                            client.cookies.set(cookie.get('name'), cookie.get('value'), 
                                             domain=cookie.get('domain', '.x.com'))
                        print('✅ Cookies loaded')
                except Exception as e:
                    print(f'⚠️ Could not load cookies: {e}')
            
            client_ready = True
            print('✅ TwiKit client ready')
        except Exception as e:
            print(f'⚠️ TwiKit initialization: {e}')
    
    # Start the tweet checker
    if not check_tweets.is_running():
        check_tweets.start()
        print('🔄 Tweet checker started')

@bot.event
async def on_message(message):
    if message.author.bot:
        return
    
    if not message.content.startswith('!'):
        return
    
    await bot.process_commands(message)

@bot.command()
async def follow(ctx, username: str):
    """Follow a Twitter account: !follow NFL"""
    username = username.lstrip('@').lower()
    
    if username in followed:
        await ctx.send(f'Already following @{username}')
        return
    
    try:
        await ctx.send(f'🔍 Fetching tweets from @{username}...')
        
        # Try to get user with retries
        max_retries = 2
        user = None
        for attempt in range(max_retries):
            try:
                user = await client.get_user_by_screen_name(username)
                break
            except TooManyRequests:
                if attempt < max_retries - 1:
                    await asyncio.sleep(5)  # Wait 5 seconds before retry
                else:
                    raise
        
        if not user:
            await ctx.send(f'❌ User @{username} not found')
            return
            
        print(f'✅ Fetched user @{username} (ID: {user.id})')
        
        # Get their recent tweets
        tweets = await client.get_user_tweets(user.id, count=20)
        
        if tweets:
            last_tweet_id = tweets[0].id if tweets else None
            followed[username] = {
                'user_id': user.id,
                'lastTweetId': last_tweet_id,
                'name': user.name
            }
            save_followed(followed)
            tweet_count = len(tweets)
            await ctx.send(f'✅ Following @{username} (found {tweet_count} recent tweets)')
            print(f'✅ Now following @{username}')
        else:
            await ctx.send(f'❌ No tweets found for @{username}')
    
    except TooManyRequests:
        await ctx.send('❌ Rate limited by X.com. Try again in a few minutes.')
        print(f'⚠️ Rate limited while following @{username}')
    except Exception as e:
        error_msg = str(e)[:100]
        await ctx.send(f'❌ Error: {error_msg}')
        print(f'❌ Error fetching @{username}: {e}')

@bot.command()
async def unfollow(ctx, username: str):
    """Unfollow a Twitter account: !unfollow NFL"""
    username = username.lstrip('@').lower()
    
    if username not in followed:
        await ctx.send(f'Not following @{username}')
        return
    
    del followed[username]
    save_followed(followed)
    await ctx.send(f'❌ Unfollowed @{username}')
    print(f'❌ Unfollowed @{username}')

@bot.command(name='list')
async def list_accounts(ctx):
    """List all followed accounts: !list"""
    if not followed:
        await ctx.send('No accounts being followed. Use `!follow <username>`')
        return
    
    usernames = '\n'.join([f'• @{u}' for u in followed.keys()])
    await ctx.send(f'📋 Followed accounts:\n{usernames}')

@tasks.loop(minutes=3)
async def check_tweets():
    """Check followed accounts for new tweets every 3 minutes"""
    if not followed:
        return
    
    channel = bot.get_channel(DISCORD_CHANNEL_ID)
    if not channel:
        print(f'❌ Channel {DISCORD_CHANNEL_ID} not found')
        return
    
    for username, data in list(followed.items()):
        try:
            print(f'🔍 Checking @{username}...')
            user_id = data.get('user_id')
            last_tweet_id = data.get('lastTweetId')
            
            if not user_id:
                print(f'⚠️ No user_id for @{username}')
                continue
            
            # Get recent tweets
            tweets = await client.get_user_tweets(user_id, count=20)
            
            if not tweets:
                print(f'  ℹ️ No tweets found')
                continue
            
            # Find new tweets
            new_tweets = []
            for tweet in tweets:
                if last_tweet_id is None or int(tweet.id) > int(last_tweet_id):
                    new_tweets.append(tweet)
            
            if not new_tweets:
                print(f'  ✓ No new tweets')
                continue
            
            # Post new tweets (reverse order - oldest first)
            for tweet in reversed(new_tweets):
                try:
                    embed = discord.Embed(
                        title=f"New Tweet from @{username}",
                        description=tweet.text[:2000] if tweet.text else "No text",
                        url=f"https://x.com/{username}/status/{tweet.id}",
                        color=discord.Color.blue(),
                        timestamp=datetime.now()
                    )
                    embed.set_author(name=data.get('name', username), url=f"https://x.com/{username}")
                    embed.set_footer(text="Posted from X.com")
                    
                    await channel.send(embed=embed)
                    print(f'  ✅ Posted tweet {tweet.id}')
                    
                except Exception as e:
                    print(f'  ❌ Error posting tweet: {e}')
                
                await asyncio.sleep(0.5)
            
            # Update last tweet ID
            if new_tweets:
                followed[username]['lastTweetId'] = new_tweets[0].id
                save_followed(followed)
                print(f'  💾 Updated last tweet ID')
        
        except TooManyRequests:
            print(f'⚠️ Rate limited for @{username}')
        except Exception as e:
            print(f'❌ Error checking @{username}: {e}')
        
        await asyncio.sleep(1)

@check_tweets.before_loop
async def before_check_tweets():
    """Wait for bot to be ready before starting the loop"""
    await bot.wait_until_ready()

# Error handling
@bot.event
async def on_command_error(ctx, error):
    await ctx.send(f'❌ Error: {str(error)}')
    print(f'Command error: {error}')

# Run bot
if __name__ == '__main__':
    if not DISCORD_TOKEN:
        print('❌ DISCORD_BOT_TOKEN not set in .env')
        exit(1)
    if not DISCORD_CHANNEL_ID or DISCORD_CHANNEL_ID == 0:
        print('❌ DISCORD_CHANNEL_ID not set in .env')
        exit(1)
    
    print('🚀 Starting Discord Twitter bot with TwiKit...')
    bot.run(DISCORD_TOKEN)
