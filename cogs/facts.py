import logging as lg
import os

import discord
import requests
from discord import app_commands
from discord.ext import commands

from bot import Eindjeboss

API_NINJAS_KEY = os.getenv("API_NINJAS_KEY")
FACTS_API_URL = "https://api.api-ninjas.com/v1/facts?limit=1"
HEADERS = {"X-Api-Key": API_NINJAS_KEY}


class Facts(commands.Cog):

    def __init__(self, bot: Eindjeboss):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        lg.info(f"[{__name__}] Cog is ready")

    @app_commands.command(name="fact", description="Get a random fact")
    async def fact(self, interaction: discord.Interaction):
        try:
            resp = requests.get(FACTS_API_URL, headers=HEADERS).json()
            fact = resp[0]["fact"]
            await interaction.response.send_message(fact)
            lg.info(f"Sent random fact to {interaction.user.name}")
        except Exception as e:
            await interaction.response.send_message(
                "Failed to get random fact. Please try again.", ephemeral=True
            )
            lg.error(e)


async def setup(client: Eindjeboss):
    await client.add_cog(Facts(client))
