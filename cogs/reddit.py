import asyncpraw
import discord
import logging as lg
import os
import random
import re
from discord.ext import commands
from discord import app_commands
from util.vars.eind_vars import (
    REDDIT_USER_AGENT,
    CHANNEL_IGNORE_LIST,
    CAT_SUBS,
    DOG_SUBS,
    CAR_SUBS,
    HOT_WHEELS_SUB
)
from util.vars.periodic_reminders import TOP_REDDIT_DT
from aiocron import crontab

SUBREDDIT_REGEX = "(?<!reddit.com)/r/[a-zA-Z0-9]{3,}"
I_REDDIT_REGEX = "https://i.redd.it/[a-zA-Z0-9]*.(png|jpg)"
I_IMGUR_REGEX = "https://i.imgur.com/[a-zA-Z0-9]*.(png|jpg)"
ANIMALS_CHANNEL_ID = int(os.getenv("ANIMALS_CHANNEL_ID"))
CARS_CHANNEL_ID = int(os.getenv("CARS_CHANNEL_ID"))
FOOD_CHANNEL_ID = int(os.getenv("FOOD_CHANNEL_ID"))
CATS = "cats"
DOGS = "rarepuppers"
CARS = "carporn"
FOOD = "foodporn"
RANDOM_STR = "Sends a random %s picture off of reddit."


class Reddit(commands.Cog):
    reddit = asyncpraw.Reddit(
        client_id=os.getenv("REDDIT_ID"),
        client_secret=os.getenv("REDDIT_SECRET"),
        user_agent=REDDIT_USER_AGENT
    )

    @commands.Cog.listener()
    async def on_ready(self):
        lg.info(f"[{__name__}] Cog is ready")
        crontab(TOP_REDDIT_DT, func=self.schedule_pic,
                args=(ANIMALS_CHANNEL_ID, [CATS, DOGS], False), start=True)
        crontab(TOP_REDDIT_DT, func=self.schedule_pic,
                args=(CARS_CHANNEL_ID, CARS, True), start=True)
        crontab(TOP_REDDIT_DT, func=self.schedule_pic,
                args=(FOOD_CHANNEL_ID, FOOD, True), start=True)

    def __init__(self, client: discord.Client):
        self.client = client

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.client.user:
            return
        if message.channel.name in CHANNEL_IGNORE_LIST:
            return

        message_content = message.content.lower()
        matches = set(re.findall(SUBREDDIT_REGEX, message_content))

        if matches:
            await self.handle_reddit_matches(matches, message)

    @app_commands.command(name="randomcat",
                          description=RANDOM_STR % "cat")
    async def send_random_cat(self, intr: discord.Interaction):
        await intr.response.defer()
        await intr.followup.send(
            await self.get_red_post(random.choice(CAT_SUBS), 50))

    @app_commands.command(name="randomdog",
                          description=RANDOM_STR % "dog")
    async def send_random_dog(self, intr: discord.Interaction):
        await intr.response.defer()
        await intr.followup.send(
            await self.get_red_post(random.choice(DOG_SUBS), 50))

    @app_commands.command(name="car",
                          description=RANDOM_STR % "car")
    async def send_random_car(self, intr: discord.Interaction):
        await intr.response.defer()
        await intr.followup.send(
            await self.get_red_post(random.choice(CAR_SUBS), 50))

    @app_commands.command(name="hotwheels",
                          description=RANDOM_STR % "hot wheels")
    async def send_random_hot_wheel(self, intr: discord.Interaction):
        await intr.response.defer()
        await intr.followup.send(
            await self.get_red_post(HOT_WHEELS_SUB, 100))

    async def get_red_post(self, subreddit, limit):
        sub = await self.reddit.subreddit(subreddit)
        posts = [post async for post in sub.hot(limit=limit)]
        chosen_post = posts[random.randint(0, len(posts) - 1)]
        while not re.match(I_REDDIT_REGEX, chosen_post.url) \
                and not re.match(I_IMGUR_REGEX, chosen_post.url):
            chosen_post = random.choice(posts)
        return chosen_post.url

    async def schedule_pic(self, channel_id, subs, include_title):
        channel = await self.client.fetch_channel(channel_id)
        sub_name = subs if str == type(subs) else random.choice(subs)
        subreddit = await self.reddit.subreddit(sub_name)

        async for submission in subreddit.top("day", limit=1):
            post = submission

        title = f"**Top post on /r/{sub_name} today: **"

        if include_title:
            title = title + post.title
        description = post.url
        payload = f"{title}\n{description}"

        await channel.send(payload)

    async def handle_reddit_matches(self, matches, message):
        m_cnt = len(matches)
        ext = 's'[:m_cnt ^ 1]
        payload = f"Found {m_cnt} subreddit link{ext} in your message:\n"
        safe_matches = await self.get_safe_matches(matches)

        if not safe_matches:
            return

        for match in safe_matches:
            payload = payload + f"https://www.reddit.com{match}\n"

        await message.reply(payload)

    async def get_safe_matches(self, matches):
        safe_matches = []
        for match in matches:
            subreddit = await self.reddit.subreddit(match[3:], fetch=True)
            if not subreddit.over18:
                safe_matches.append(match)

        return safe_matches


async def setup(bot):
    await bot.add_cog(Reddit(bot))
