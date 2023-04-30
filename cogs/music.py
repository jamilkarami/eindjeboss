import discord
import logging as lg
import requests
import spotipy
from bs4 import BeautifulSoup
from discord.ext import commands
from discord import app_commands
from spotipy.oauth2 import SpotifyClientCredentials
from spotipy.exceptions import SpotifyException

sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials())
sp_scope = "user-library-read"

S_DESC = "Sends a link to the song that matches your query the most on Spotify"
SC_DESC = "Sends a link to the song you are currently listening to on Spotify"


class Music(commands.Cog):

    def __init__(self, client: commands.Bot):
        self.client = client

    @commands.Cog.listener()
    async def on_ready(self):
        lg.info(f"[{__name__}] Cog is ready")

    @app_commands.command(name="sp",
                          description=S_DESC)
    async def sp(self, intr: discord.Interaction, query: str):
        try:
            name = intr.user.name
            result = sp.search(f"{query}", type="track")
            if len(result['tracks']['items']) > 0:
                await intr.response.send_message(
                    result['tracks']['items'][0]['external_urls']['spotify'])
            else:
                await intr.response.send_message(
                    'No results found for: ' + query)
        except SpotifyException as e:
            lg.error(f"Failed to send song to {name} for query \"{query}\"")
            lg.debug(e)
        else:
            lg.info(f"Sent song to {name} for query \"{query}\"")

    @app_commands.command(name="spc",
                          description=SC_DESC)
    async def spc(self, intr: discord.Interaction):
        spotify_act = None

        user = intr.user
        activities = intr.guild.get_member(user.id).activities
        for activity in activities:
            if isinstance(activity, discord.Spotify):
                spotify_act = activity

        if spotify_act is None:
            await intr.response.send_message(
                "You are not currently listening to anything on Spotify or you"
                " haven't connected Discord to your Spotify account.",
                ephemeral=True)
            return

        try:
            await intr.response.send_message(spotify_act.track_url)
        except Exception as e:
            lg.error(f"Failed to send current song to {intr.user.name}")
            lg.debug(e)
        else:
            lg.info(f"Sent current song to {intr.user.name}")

    @app_commands.command(name="lyrics",
                          description="Sends the lyrics of a song matching"
                          " your query, if they exist.")
    async def lyrics(self, intr: discord.Interaction, query: str):
        try:
            name = intr.user.name
            b_url = 'https://www.musixmatch.com'
            url = f'{b_url}/search/{query.lower().replace(" ", "%20")}/tracks'

            headers = {'Host': 'www.musixmatch.com',
                       'user-agent': 'Mozilla/5.0'}

            content = requests.get(url, headers=headers).content

            soup = BeautifulSoup(content.decode('utf-8'), 'html.parser')
            lyrics_url = b_url + soup.find('a', {'class': 'title'}).get('href')

            lyrics_page = requests.get(lyrics_url, headers=headers).content
            soup = BeautifulSoup(lyrics_page.decode('utf-8'), 'html.parser')

            title = soup.title.string.replace(' Lyrics | Musixmatch', '')

            l_els = soup.select('span[class^="lyrics__content__"]')
            lyr = '\n'.join(el.get_text() for el in l_els) if l_els else \
                '*This song has no available lyrics*'

            embed = discord.Embed(title=title,
                                  description=lyr,
                                  color=discord.Color.green())
            await intr.response.send_message(embed=embed)
        except Exception as e:
            lg.error(f"Failed to send lyrics to {name} for query: {query}")
            lg.debug(e)
        else:
            lg.info(f"Sent lyrics to {name} for query: {query}")


async def setup(client: commands.Bot):
    await client.add_cog(Music(client))
