import { Client, GatewayIntentBits, EmbedBuilder } from 'discord.js';
import { config } from './config.js';

export class DiscordBot {
  constructor() {
    this.client = new Client({
      intents: [
        GatewayIntentBits.Guilds,
        GatewayIntentBits.GuildMessages,
      ],
    });

    this.channel = null;
    this.ready = false;
  }

  async connect() {
    return new Promise((resolve, reject) => {
      this.client.once('ready', async () => {
        console.log(`✅ Discord bot logged in as ${this.client.user.tag}`);

        try {
          this.channel = await this.client.channels.fetch(config.discord.channelId);
          if (!this.channel) {
            throw new Error(`Could not find channel with ID: ${config.discord.channelId}`);
          }
          console.log(`✅ Connected to Discord channel: ${this.channel.name}`);
          this.ready = true;
          resolve();
        } catch (error) {
          reject(error);
        }
      });

      this.client.on('error', (error) => {
        console.error('Discord client error:', error);
      });

      this.client.login(config.discord.token).catch(reject);
    });
  }

  async postTweet(tweet) {
    if (!this.ready || !this.channel) {
      console.error('Discord bot is not ready or channel is not available');
      return;
    }

    try {
      const embed = new EmbedBuilder()
        .setColor(0x1DA1F2)
        .setAuthor({
          name: `${tweet.author.name} (@${tweet.author.username})`,
          iconURL: tweet.author.profile_image_url,
          url: `https://twitter.com/${tweet.author.username}`,
        })
        .setDescription(tweet.text)
        .setURL(`https://twitter.com/${tweet.author.username}/status/${tweet.id}`)
        .setTimestamp(new Date(tweet.created_at))
        .setFooter({ text: 'Twitter' });

      const messageContent = {
        embeds: [embed],
      };

      if (tweet.video) {
        console.log(`📹 Tweet contains video: ${tweet.video.url}`);
        messageContent.content = tweet.video.url;
      }

      await this.channel.send(messageContent);
      console.log(`✅ Posted tweet ${tweet.id} to Discord`);
    } catch (error) {
      console.error('Error posting tweet to Discord:', error);
      throw error;
    }
  }

  disconnect() {
    if (this.client) {
      this.client.destroy();
      console.log('Discord bot disconnected');
    }
  }
}
