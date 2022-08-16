import discord
from discord.ext import commands
from discord import app_commands
from vars.eind_vars import *
import re
import asyncpraw
import os
from vars.eind_vars import *
import logging
import dateparser
import time
from dotenv import load_dotenv
import asyncio
from vars.periodic_reminders import TOP_REDDIT_CAT_DT

SUBREDDIT_REGEX = "(?<!reddit.com)\/r\/[a-zA-Z0-9]{3,}"
CHANNEL_ID = int(os.getenv("ANIMALS_CHANNEL_ID"))

class Reddit(commands.Cog):

    reddit = asyncpraw.Reddit(
        client_id=os.getenv("REDDIT_ID"),
        client_secret=os.getenv("REDDIT_SECRET"),
        user_agent=REDDIT_USER_AGENT
    )

    load_dotenv()
    CAT_CHAN_ID = os.getenv("ANIMALS_CHANNEL_ID")

    @commands.Cog.listener()
    async def on_ready(self):
        logging.info(f"{__name__} Cog is ready")
        await self.schedule_cat_pic()

    def __init__(self, bot : discord.Client):
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
            await message.reply(self.get_reddit_matches(matches))
        
        return

    async def schedule_cat_pic(self):
        cat_time = dateparser.parse(TOP_REDDIT_CAT_DT, settings={'PREFER_DATES_FROM': 'future'})
        if cat_time.timestamp() < time.time():
            cat_time = dateparser.parse(f"tomorrow {TOP_REDDIT_CAT_DT}", settings={'PREFER_DATES_FROM': 'future'})
            
        wait_time = cat_time.timestamp() - time.time()

        channel = await self.bot.fetch_channel(CHANNEL_ID)

        logging.info(f"Will send cat pic in {wait_time} seconds")
        await asyncio.sleep(wait_time)

        post = next(iter(self.reddit.subreddit("cats").top("day", limit=1)))
        title=f"**Top post on /r/cats today: {post.title}**"
        description=post.url
        payload = f"{title}\n{description}"

        await channel.send(payload)
        return
    
    def get_reddit_matches(self, matches):
        plural = "s" if len(matches) > 1 else ""
        payload = f"Found {len(matches)} subreddit link{plural} in your message:\n"

        for match in matches:
            payload = payload + f"https://www.reddit.com{match}\n"
        
        return payload

async def setup(bot):
    await bot.add_cog(Reddit(bot))