# Twitter to Discord Bot

A Node.js Discord bot that monitors a specific Twitter account and automatically posts new tweets to a designated Discord channel. The bot detects and embeds videos so they play directly in Discord.

## Features

- **Real-time Tweet Monitoring**: Polls Twitter API v2 to fetch new tweets from a specified account
- **Video Embedding**: Automatically detects videos in tweets and embeds them in Discord messages
- **Smart Tweet Tracking**: Remembers the last processed tweet to avoid duplicates
- **Rate Limit Handling**: Implements exponential backoff for Twitter API rate limits
- **Rich Embeds**: Posts tweets with author information, timestamps, and proper formatting
- **Configurable**: Easy setup via environment variables

## Prerequisites

Before running this bot, you need:

1. **Discord Bot Token**
   - Go to [Discord Developer Portal](https://discord.com/developers/applications)
   - Create a new application and add a bot
   - Copy the bot token
   - Invite the bot to your server with permissions: Send Messages, Embed Links

2. **Discord Channel ID**
   - Enable Developer Mode in Discord (User Settings > Advanced > Developer Mode)
   - Right-click the channel where you want tweets posted
   - Click "Copy Channel ID"

3. **Twitter API Credentials**
   - Apply for a Twitter Developer account at [developer.twitter.com](https://developer.twitter.com)
   - Create a new app and generate API keys
   - You need the Bearer Token (required for API v2)

## Installation

1. Clone this repository or copy the files to your project

2. Install dependencies:
```bash
npm install
```

3. Create a `.env` file by copying the example:
```bash
cp .env.example .env
```

4. Edit `.env` and fill in your credentials:
```env
DISCORD_BOT_TOKEN=your_discord_bot_token_here
DISCORD_CHANNEL_ID=your_channel_id_here
TWITTER_BEARER_TOKEN=your_twitter_bearer_token_here
TWITTER_USERNAME=twitter_account_to_monitor
POLL_INTERVAL_MS=60000
```

## Configuration

Edit the `.env` file with these variables:

| Variable | Description | Required |
|----------|-------------|----------|
| `DISCORD_BOT_TOKEN` | Your Discord bot token | Yes |
| `DISCORD_CHANNEL_ID` | The Discord channel ID where tweets will be posted | Yes |
| `TWITTER_BEARER_TOKEN` | Your Twitter API Bearer Token | Yes |
| `TWITTER_USERNAME` | The Twitter username to monitor (without @) | Yes |
| `POLL_INTERVAL_MS` | How often to check for new tweets (milliseconds) | No (default: 60000) |

### Optional Twitter API Credentials

For enhanced functionality, you can also provide:
- `TWITTER_API_KEY`
- `TWITTER_API_SECRET`
- `TWITTER_ACCESS_TOKEN`
- `TWITTER_ACCESS_SECRET`

## Usage

Start the bot:
```bash
npm start
```

The bot will:
1. Connect to Discord
2. Verify the Twitter account exists
3. Start polling for new tweets
4. Post new tweets to your Discord channel with embedded videos

## How It Works

### Tweet Monitoring
- The bot polls the Twitter API every 60 seconds (configurable)
- Fetches up to 10 recent tweets from the monitored account
- Only posts tweets that are newer than the last processed tweet
- Saves the last tweet ID to prevent duplicates across restarts

### Video Detection
The bot detects videos in two ways:
1. **Native Twitter Videos**: Extracts video URLs from tweet media attachments
2. **External Video Links**: Detects YouTube, Vimeo, and other video platform links

### Discord Posting
- Creates rich embeds with author info, tweet text, and timestamp
- If a video is detected, includes the video URL for automatic embedding
- Discord will auto-embed Twitter videos and external video links

## Rate Limiting

The bot handles Twitter API rate limits gracefully:
- Detects 429 (Too Many Requests) responses
- Automatically waits 15 minutes before retrying
- Logs rate limit events for monitoring

## Error Handling

- Validates configuration on startup
- Logs all errors with descriptive messages
- Continues running after recoverable errors
- Graceful shutdown on SIGINT/SIGTERM

## File Structure

```
├── src/
│   ├── index.js           # Main application entry point
│   ├── config.js          # Configuration management
│   ├── discordBot.js      # Discord bot implementation
│   └── twitterService.js  # Twitter API integration
├── .env                   # Your configuration (not in git)
├── .env.example          # Example configuration
├── package.json          # Node.js dependencies
└── README.md             # This file
```

## Troubleshooting

### Bot doesn't post tweets
- Verify your Twitter Bearer Token is valid
- Check that the Twitter username is correct
- Ensure the bot has been invited to your Discord server
- Verify the Discord channel ID is correct
- Check the console logs for error messages

### Rate limit errors
- Reduce `POLL_INTERVAL_MS` to check less frequently
- Ensure you're not running multiple instances of the bot

### Videos not embedding
- Discord may not support all video formats
- External videos (YouTube, Vimeo) should embed automatically
- Twitter videos are posted as direct links

## License

MIT
