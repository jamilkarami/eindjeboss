import discord
from discord.ext import commands

import logging
from dotenv import load_dotenv
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from spotipy.exceptions import SpotifyException

sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials())
sp_scope = "user-library-read"

class Music(commands.Cog):

    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_ready():
        logging.info(f"{__name__} Cog is ready")

    @commands.command(aliases=["sp"])
    async def spotify(self, ctx, *args):
        query = " ".join(args)
        try:
            result = sp.search(f"{query}", type="track")
            if(len(result['tracks']['items']) > 0):
                await ctx.message.reply(result['tracks']['items'][0]['external_urls']['spotify'])
            else:
                await ctx.message.reply('No results found for: ' + query)
        except SpotifyException as e:
            print(e)

    @commands.command(aliases=["spc"])
    async def spotifycurrent(self, ctx):
        spotify_act = None
        user = ctx.author
        for activity in user.activities:
            if isinstance(activity, discord.Spotify):
                spotify_act = activity

        if spotify_act is None:
            await ctx.message.reply("You are not currently listening to anything on Spotify or you haven't connected Discord to your Spotify account.")
            
        try:
            await ctx.message.reply(activity.track_url)
        except Exception as e:
            print(e)

async def setup(bot):
    await bot.add_cog(Music(bot))