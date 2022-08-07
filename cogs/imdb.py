from discord.ext import commands
from imdb import Cinemagoer
import logging

ia = Cinemagoer()

class IMDB(commands.Cog):

    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_ready(self):
        logging.info(f"{__name__} Cog is ready")

    @commands.command(aliases=["mv", "sr"])
    async def imdb(self, ctx, *args):
        query = " ".join(args)
        movies = ia.search_movie(query)
        if not movies:
            await ctx.message.reply("No results found for \"" + query + "\" on IMDB.") 
            return
        movie_id = movies[0].movieID
        await ctx.message.reply("https://www.imdb.com/title/tt{id}/".format(id = movie_id))
        return

async def setup(bot):
    await bot.add_cog(IMDB(bot))