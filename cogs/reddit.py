import discord
from discord.ext import commands
from discord import app_commands
from vars.eind_vars import *
import re
import praw
import os
from vars.eind_vars import *

SUBREDDIT_REGEX = "(?<!reddit.com)\/r\/[a-zA-Z0-9]{3,}"

class Reddit(commands.Cog):

    reddit = praw.Reddit(
        client_id=os.getenv("REDDIT_ID"),
        client_secret=os.getenv("REDDIT_SECRET"),
        user_agent=REDDIT_USER_AGENT
    )

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user:
            return
        if message.channel.name in CHANNEL_IGNORE_LIST:
            return
        
        message_content = message.content.lower()
        matches = re.findall(SUBREDDIT_REGEX, message_content)

        if matches:
            await self.handle_reddit_matches(matches, message)
        
        return

    @app_commands.command(name="cats", description="Gets a random cat post from /r/cats")
    async def cats(self, interaction : discord.Interaction):
        post = next(iter(self.reddit.subreddit("cats").top("day", limit=1)))

        title=f"**Top post on /r/cats today: {post.title}**"
        description=post.url
        payload = f"{title}\n{description}"
        await interaction.response.send_message(payload)
        return
    
    async def handle_reddit_matches(self, matches, message):
        plural = "s" if len(matches) > 1 else ""
        payload = f"Found {len(matches)} subreddit link{plural} in your message:\n"

        for match in matches:
            payload = payload + f"https://www.reddit.com{match}\n"
        
        await message.reply(payload)
        return

async def setup(bot):
    await bot.add_cog(Reddit(bot))