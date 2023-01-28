import discord
import logging
import os
import requests
from discord import app_commands
from discord.ext import commands
from util.vars.eind_vars import *

API_NINJAS_KEY = os.getenv('API_NINJAS_KEY')
FACTS_API_URL = 'https://api.api-ninjas.com/v1/facts?limit=1'
HEADERS = {'X-Api-Key': API_NINJAS_KEY}

class Facts(commands.Cog):

    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_ready(self):
        logging.info(f"[{__name__}] Cog is ready")

    @app_commands.command(name="fact", description="Get a random fact")
    async def fact(self, interaction: discord.Interaction):
        try:
            resp = requests.get(FACTS_API_URL, headers=HEADERS).json()
            fact = resp[0]['fact']
            await interaction.response.send_message(fact)
            logging.info(f'Sent random fact to {interaction.user.name}')
        except Exception as e:
            await interaction.response.send_message("Failed to get your random fact. Please try again.", ephemeral=True)
            logging.error(e)

async def setup(bot):
    await bot.add_cog(Facts(bot))