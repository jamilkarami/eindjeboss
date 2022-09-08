from discord.ext import commands
import discord
from discord import app_commands
from imdb import Cinemagoer
import logging

ia = Cinemagoer()


class IMDB(commands.Cog):

    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_ready(self):
        logging.info(f"[{__name__}] Cog is ready")

    @app_commands.command(name="imdb")
    async def imdb(self, interaction: discord.Interaction, query: str):
        movies = ia.search_movie(query)
        if not movies:
            await interaction.response.send_message("No results found for \"" + query + "\" on IMDB.")
            return
        movie_id = movies[0].movieID
        await interaction.response.send_message("https://www.imdb.com/title/tt{id}/".format(id=movie_id))
        return


async def setup(bot):
    await bot.add_cog(IMDB(bot))
