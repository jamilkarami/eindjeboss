import logging as lg
import os

import discord
import requests
from discord import app_commands
from discord.ext import commands

from bot import Eindjeboss

API_KEY = os.getenv("GOOGLE_SEARCH_API_KEY")

url = (
    "https://www.googleapis.com/customsearch/v1?key=%s"
    "&cx=%s&q=%s&num=1&searchType=image&safe=active"
)


class Images(commands.Cog, name="Images"):

    def __init__(self, bot: Eindjeboss):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        lg.info(f"[{__name__}] Cog is ready")

    @app_commands.command(name="img")
    async def img(self, intr: discord.Interaction, query: str):
        search_engine_id = await self.bot.get_setting("gc_search_engine_id")
        req_url = url % (API_KEY, search_engine_id, query)

        data = requests.get(req_url).json()
        if "items" not in data:
            await intr.response.send_message("No result found.", ephemeral=True)
            return

        results = data.get("items")

        msg = "\n".join([res.get("link") for res in results])
        await intr.response.send_message(msg)


async def setup(client: Eindjeboss):
    await client.add_cog(Images(client))
