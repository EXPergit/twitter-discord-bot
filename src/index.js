import { DiscordBot } from './discordBot.js';
import { TwitterService } from './twitterService.js';
import { config, validateConfig } from './config.js';

class TwitterDiscordBot {
  constructor() {
    this.discord = new DiscordBot();
    this.twitter = new TwitterService();
    this.polling = false;
    this.pollTimeout = null;
  }

  async start() {
    console.log('🚀 Starting Twitter to Discord bot...');

    if (!validateConfig()) {
      console.error('❌ Bot cannot start due to configuration errors');
      console.error('\n📝 Setup Instructions:');
      console.error('1. Copy .env.example to .env');
      console.error('2. Fill in your Discord bot token and channel ID');
      console.error('3. Add your Twitter API credentials (Bearer token is required)');
      console.error('4. Set the Twitter username to monitor');
      process.exit(1);
    }

    try {
      await this.discord.connect();
      console.log(`📊 Monitoring Twitter user: @${config.twitter.username}`);
      console.log(`⏱️  Poll interval: ${config.pollIntervalMs / 1000} seconds`);

      await this.twitter.getUserId();

      this.startPolling();
    } catch (error) {
      console.error('❌ Failed to start bot:', error);
      process.exit(1);
    }
  }

  async startPolling() {
    if (this.polling) {
      return;
    }

    this.polling = true;
    await this.poll();
  }

  async poll() {
    try {
      console.log('🔍 Checking for new tweets...');
      const tweets = await this.twitter.getLatestTweets();

      if (tweets.length > 0) {
        console.log(`📬 Found ${tweets.length} new tweet(s)`);
        for (const tweet of tweets) {
          await this.discord.postTweet(tweet);
          await this.sleep(1000);
        }
      } else {
        console.log('📭 No new tweets');
      }
    } catch (error) {
      if (error.message === 'RATE_LIMIT') {
        console.log('⏳ Rate limited. Waiting 15 minutes...');
        await this.sleep(15 * 60 * 1000);
      } else {
        console.error('Error during polling:', error.message);
      }
    }

    if (this.polling) {
      this.pollTimeout = setTimeout(() => this.poll(), config.pollIntervalMs);
    }
  }

  sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  stop() {
    console.log('🛑 Stopping bot...');
    this.polling = false;
    if (this.pollTimeout) {
      clearTimeout(this.pollTimeout);
    }
    this.discord.disconnect();
  }
}

const bot = new TwitterDiscordBot();

process.on('SIGINT', () => {
  bot.stop();
  process.exit(0);
});

process.on('SIGTERM', () => {
  bot.stop();
  process.exit(0);
});

bot.start();
