import discord
import logging
from imdb import Cinemagoer
from discord import app_commands
from discord.ext import commands

ia = Cinemagoer()


class IMDB(commands.Cog):

    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_ready(self):
        logging.info(f"[{__name__}] Cog is ready")

    @app_commands.command(name="imdb", description="Search for a movie/series on IMDb.")
    async def imdb(self, interaction: discord.Interaction, query: str):
        movies = ia.search_movie(query)
        if not movies:
            await interaction.response.send_message('No results found for "' + query + '" on IMDB.', ephemeral=True)
            return
        movie_id = movies[0].movieID
        await interaction.response.send_message("https://www.imdb.com/title/tt{id}/".format(id=movie_id))


async def setup(bot):
    await bot.add_cog(IMDB(bot))
