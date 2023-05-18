import logging as lg

import discord
import requests
import spotipy
from bs4 import BeautifulSoup
from discord import app_commands
from discord.ext import commands
from spotipy.exceptions import SpotifyException
from spotipy.oauth2 import SpotifyClientCredentials

from util.util import get_colors_from_img

sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials())
sp_scope = "user-library-read"

S_DESC = "Sends a link to the song that matches your query the most on Spotify"
SC_DESC = "Sends a link to the song you are currently listening to on Spotify"
SP_ICON = "https://i.imgur.com/XX2a6pf.png"


class Music(commands.Cog):

    def __init__(self, bot: commands.Bot):
        self.bot = bot

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
                embed = mk_sp_embed(result['tracks']['items'][0], intr.user)
                await intr.response.send_message(embed=embed)
            else:
                await intr.response.send_message(
                    'No results found for: ' + query, ephemeral=True)
        except SpotifyException as e:
            lg.error(f"Failed to send song to {name} for query \"{query}\"")
            lg.debug(e)
        else:
            lg.info(f"Sent song to {name} for query \"{query}\"")

    @app_commands.command(name="spc",
                          description=SC_DESC)
    async def spc(self, intr: discord.Interaction):
        user_id = intr.user.id

        if intr.guild.get_member(user_id).status == discord.Status.offline:
            await intr.response.send_message(
                "You have to be online to use this command.",
                ephemeral=True)
            return

        spotify_act = None

        user = intr.user
        activities = intr.guild.get_member(user.id).activities
        for activity in activities:
            if isinstance(activity, discord.Spotify):
                spotify_act = activity

        if spotify_act is None:
            await intr.response.send_message(
                "You not currently listening to anything on Spotify or you "
                "haven't connected Discord to your Spotify account.",
                ephemeral=True)
            return

        try:
            embed = mk_spc_embed(spotify_act, intr.user)
            await intr.response.send_message(embed=embed)
        except Exception as e:
            lg.error(f"Failed to send current song to {intr.user.name}")
            print(e)
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


def get_artist_url(artist):
    artist_name = artist['name']
    artist_id = artist['uri'].split(':')[2]
    return f"[{artist_name}](https://open.spotify.com/artist/{artist_id})"


def get_album_url(album):
    album_name = album['name']
    album_id = album['uri'].split(':')[2]
    return f"[{album_name}](https://open.spotify.com/album/{album_id})"


def mk_sp_embed(song, user: discord.Member) -> discord.Embed:
    artists = song['artists']
    artist = f"By {artists[0]['name']}"
    title = song['name']
    footer = f"On album: {song['album']['name']}"
    album_cover_url = song['album']['images'][0]['url']
    track_url = song['external_urls']['spotify']
    author = f"{user.display_name} is listening to... "

    cl = get_colors_from_img(album_cover_url)[1]

    embed = discord.Embed(title=title, url=f"{track_url}?go=1",
                          color=discord.Color.from_rgb(cl[0], cl[1], cl[2]))
    embed.set_author(name=author, icon_url=user.avatar.url)
    embed.set_footer(text=footer, icon_url=SP_ICON)
    embed.set_thumbnail(url=album_cover_url)

    if len(artists) > 1:
        artist_names = [get_artist_url(art) for art in artists]
        artist += f", _with {', '.join(artist_names[1:])}_"

    embed.description = artist + "\n" + "\u2800" * 43
    return embed


def mk_spc_embed(spotify_act: discord.Spotify,
                 user: discord.Member) -> discord.Embed:
    cl = get_colors_from_img(spotify_act.album_cover_url)[0]

    title = f"{spotify_act.title}"
    description = f"By {spotify_act.artists[0]}"
    footer = f"On album: {spotify_act.album}"
    author = f"{user.display_name} is listening to... "

    embed = discord.Embed(title=title, url=f"{spotify_act.track_url}?go=1",
                          color=discord.Color.from_rgb(cl[0], cl[1], cl[2]))
    embed.set_author(name=author, icon_url=user.avatar.url)
    embed.set_footer(text=footer, icon_url=SP_ICON)
    embed.set_thumbnail(url=spotify_act.album_cover_url)

    if len(spotify_act.artists) > 1:
        description += f", _with {', '.join(spotify_act.artists[1:])}_"

    embed.description = description + "\n" + "\u2800" * 43
    return embed


async def setup(client: commands.Bot):
    await client.add_cog(Music(client))
