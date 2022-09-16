import discord
from discord.ext import commands
from discord import app_commands

import logging
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from spotipy.exceptions import SpotifyException

sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials())
sp_scope = "user-library-read"


class Music(commands.Cog):

    def __init__(self, client: commands.Bot):
        self.client = client

    @commands.Cog.listener()
    async def on_ready(self):
        logging.info(f"[{__name__}] Cog is ready")

    @app_commands.command(name="sp", description="Sends a link to the song that matches your query the most")
    async def spotify(self, interaction: discord.Interaction, query: str):
        try:
            result = sp.search(f"{query}", type="track")
            if (len(result['tracks']['items']) > 0):
                await interaction.response.send_message(result['tracks']['items'][0]['external_urls']['spotify'])
            else:
                await interaction.response.send_message('No results found for: ' + query)
        except SpotifyException as e:
            logging.debug(e)

    @app_commands.command(name="spc", description="Sends a link to the song you are currently listening to on Spotify")
    async def spotifycurrent(self, interaction: discord.Interaction):
        spotify_act = None

        user = interaction.user
        activities = interaction.guild.get_member(user.id).activities
        for activity in activities:
            if isinstance(activity, discord.Spotify):
                spotify_act = activity

        if spotify_act is None:
            await interaction.response.send_message("You are not currently listening to anything on Spotify or you haven't connected Discord to your Spotify account.", ephemeral=True)
            return

        try:
            await interaction.response.send_message(spotify_act.track_url)
        except Exception as e:
            print(e)


async def setup(bot):
    await bot.add_cog(Music(bot))
