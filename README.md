# Discord Twitter/X Scraper Bot

A Discord bot that monitors Twitter/X accounts and automatically posts new tweets to a Discord channel using Puppeteer for web scraping (no API costs).

## Features

- **Discord Commands**:
  - `!follow <username>` - Start monitoring a Twitter account
  - `!unfollow <username>` - Stop monitoring a Twitter account
  - `!list` - Show all monitored accounts

- **Automatic Tweet Posting**: Checks every 3 minutes for new tweets from all followed accounts
- **Duplicate Prevention**: Tracks the last seen tweet to avoid posting duplicates
- **Rich Embeds**: Posts tweets with author name, text, timestamp, and link
- **Cookie Authentication**: Optional X.com login support via cookies.json
- **No API Costs**: Uses Puppeteer browser automation instead of Twitter API

## Setup

### 1. Install Dependencies
```bash
npm install
```

### 2. Configure Environment Variables

Create a `.env` file based on `.env.example`:

```env
DISCORD_BOT_TOKEN=your_bot_token_here
DISCORD_CHANNEL_ID=your_channel_id_here
```

### 3. (Optional) Add Authentication Cookies

For authenticated scraping (better rate limits, access to private accounts):

1. Log into X.com in your browser
2. Press F12 → Application tab → Cookies
3. Export all cookies for x.com
4. Format as JSON array and paste into `cookies.json`:

```json
[
  {
    "name": "auth_token",
    "value": "...",
    "domain": ".x.com",
    "path": "/"
  }
]
```

### 4. Start the Bot

```bash
npm start
```

## Usage

Once running, use these commands in Discord:

- `!follow NFL` - Monitor @NFL account
- `!follow elonmusk` - Monitor @elonmusk account  
- `!list` - See all monitored accounts
- `!unfollow NFL` - Stop monitoring @NFL

New tweets will appear in the configured channel automatically every 3 minutes.

## Files

- **index.js** - Main Discord bot with commands and scheduler
- **scraper.js** - Puppeteer-based Twitter scraper
- **followed.json** - Stores tracked accounts and last seen tweet ID
- **cookies.json** - Optional X.com authentication cookies
- **package.json** - Dependencies

## How It Works

1. When you use `!follow <username>`, the bot stores the account in followed.json
2. Every 3 minutes, the bot checks each followed account for new tweets using Puppeteer
3. If new tweets are found, they're posted to Discord as embeds
4. The bot tracks the last tweet ID to avoid duplicates
5. Use `!unfollow` to stop tracking an account

## Troubleshooting

- **Bot not responding**: Ensure Discord bot token is correct and bot has message permissions
- **No tweets found**: Account might be private or require authentication (add cookies)
- **Channel not found**: Verify DISCORD_CHANNEL_ID is correct

## Technical Details

- Uses **discord.js v14** for Discord integration
- Uses **Puppeteer** with headless Chromium for tweet scraping
- Runs in **no-sandbox mode** for Replit compatibility
- Scrolls to load 10-20+ tweets per check
- Extracts tweet ID, text, timestamp, and URL
