import discord
from discord import app_commands
from discord.ext import commands

import logging
import wikipedia
import wikipediaapi
from wikipedia.exceptions import PageError, DisambiguationError

wiki = wikipediaapi.Wikipedia('en')

class Wiki(commands.Cog):

    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_ready(self):
        logging.info(f"{__name__} Cog is ready")

    @app_commands.command(name="wiki")
    async def wiki(self, interaction: discord.Interaction, query: str):
        embed = discord.Embed()
        url = wikipedia.page(f"{query}", auto_suggest=False).url

        try:
            summary = wikipedia.summary(f"{query}", auto_suggest=False, sentences=3)
            payload = summary + f" [link]({url})"
        except PageError as e:
            payload  = "Could not find page for query: " + f"{query}"
            print(e)
        except DisambiguationError as e:
            summary = wikipedia.summary(e.options[0], auto_suggest=False, sentences=3)
            payload = summary + f" [(link)]({url})"

        embed.description = payload
        await interaction.response.send_message(embed=embed)
        return

async def setup(bot):
    await bot.add_cog(Wiki(bot))