import json

import discord
import logging
import spotipy
import requests
import re
from bs4 import BeautifulSoup
from discord.ext import commands
from discord import app_commands
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
            if len(result['tracks']['items']) > 0:
                await interaction.response.send_message(result['tracks']['items'][0]['external_urls']['spotify'])
                logging.info(f"Sent song to {interaction.user.name} for query \"{query}\"")
            else:
                await interaction.response.send_message('No results found for: ' + query)
        except SpotifyException as e:
            logging.error(f"Failed to send song to {interaction.user.name} for query \"{query}\"")
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
            await interaction.response.send_message("You are not currently listening to anything on Spotify or you "
                                                    "haven't connected Discord to your Spotify account.",
                                                    ephemeral=True) 
            return

        try:
            await interaction.response.send_message(spotify_act.track_url)
            logging.info(f"Sent current song to {interaction.user.name}")
        except Exception as e:
            logging.error(f"Failed to send current song to {interaction.user.name}")
            logging.debug(e)

    @app_commands.command(name="lyrics", description="Sends the lyrics of a song matching your query, if they exist.")
    async def lyrics(self, interaction: discord.Interaction, query: str):
        try:
            base_url = 'https://www.musixmatch.com'
            url = f'{base_url}/search/{query.lower().replace(" ", "%20")}/tracks'

            headers = {'Host': 'www.musixmatch.com',
                    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.142 Safari/537.36'}

            content = requests.get(url, headers=headers).content

            soup = BeautifulSoup(content.decode('utf-8'), 'html.parser')
            lyrics_url = base_url + soup.find('a', {'class': 'title'}).get('href')

            lyrics_page = requests.get(lyrics_url, headers=headers).content
            soup = BeautifulSoup(lyrics_page.decode('utf-8'), 'html.parser')

            title = soup.title.string.replace(' Lyrics | Musixmatch', '')

            lyrics_els = soup.select('span[class^="lyrics__content__"]')
            lyrics = '\n'.join(el.get_text() for el in lyrics_els) if lyrics_els else '*This song has no available lyrics*'

            embed = discord.Embed(title=title, description=lyrics)
            await interaction.response.send_message(embed=embed)
        except Exception as e:
            logging.error(f"Failed to send lyrics to {interaction.user.name} for query \"{query}\"")
            logging.debug(e)

async def setup(bot):
    await bot.add_cog(Music(bot))
