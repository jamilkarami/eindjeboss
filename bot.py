# bot.py
from asyncio.windows_events import NULL
import os
import time
import random
from numbers import Number

import discord
import wikipediaapi
import wikipedia
from wikipedia.exceptions import PageError, DisambiguationError
from discord.ext import commands, tasks
from dotenv import load_dotenv
from googletrans import Translator
from googletrans.constants import LANGUAGES

import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from spotipy.exceptions import SpotifyException

from imdb import Cinemagoer


BOOK_EMOJI = "📖"
BONK_TRIGGERS = ["Mommy", "Daddy"]
CHANNEL_IGNORE_LIST = ["👾・akinator"]

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

translator = Translator()
wiki = wikipediaapi.Wikipedia('en')
sp_scope = "user-library-read"
sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials())
ia = Cinemagoer()

intents = discord.Intents.all()
client = commands.Bot(command_prefix="!", case_insensitive=True, intents=intents)

@client.event
async def on_ready():
    print(f'{client.user.name} has connected to Discord!')

@client.command()
async def bonk(ctx):
    await ctx.message.reference.resolved.reply("<a:bonk:995996313650999387>")

@client.command()
async def wiki(ctx, *args):
    query = " ".join(args)
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
    await ctx.message.reply(embed=embed)
    return

@client.command(aliases=["tr"])
async def translate(ctx, *args):
    src = None if not args else args[0]
    
    if ctx.message.reference:
        await ctx.message.reference.resolved.reply(translate_message(ctx.message.reference.resolved, src))
    else:
        await ctx.message.reply("\"!translate\" can only be used as a reply to another message")
    return

@client.command(aliases=["sp"])
async def spotify(ctx, *args):
    query = " ".join(args)
    try:
        result = sp.search(f"{query}", type="track")
        if(len(result['tracks']['items']) > 0):
            await ctx.message.reply(result['tracks']['items'][0]['external_urls']['spotify'])
        else:
            await ctx.message.reply('No results found for: ' + query)
    except SpotifyException as e:
        print(e)

@client.command(aliases=["spc"])
async def spotifycurrent(ctx):
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

@client.command(aliases=["mv", "sr"])
async def imdb(ctx, *args):
    query = " ".join(args)
    movies = ia.search_movie(query)
    if not movies:
        await ctx.message.reply("No results found for \"" + query + "\" on IMDB.") 
        return
    movie_id = movies[0].movieID
    await ctx.message.reply("https://www.imdb.com/title/tt{id}/".format(id = movie_id))
    return

@client.command(aliases=[])
async def roll(ctx, *args):
    max = 20 if not args else int(args[0])

    random.seed(time.time())
    num = random.randint(1, max)

    await ctx.message.reply("You roll a D{max}. You get: {num}.".format(max = str(max), num = str(num)))
    return

@client.event
async def on_message(message):
    if message.author == client.user:
        return
    if message.channel.name in CHANNEL_IGNORE_LIST:
        return
        
    message_content = message.content.lower()

    # Bonk users
    if any(word.lower() in message_content for word in BONK_TRIGGERS):
        await message.reply("<a:bonk:995996313650999387>")
        return

    await client.process_commands(message)
    
@client.event
async def on_reaction_add(reaction, user):
    if reaction.message.author == client.user:
        return

    # Translate by reaction
    if reaction.emoji == BOOK_EMOJI:
        src_msg = "You asked me to translate the following message: " + reaction.message.content
        dst_msg = translate_message(reaction.message, None)

        await user.send(content=src_msg)
        await user.send(content=dst_msg)
        return

def translate_message(message, src):
    translated = translator.translate(message.content) if not src else translator.translate(message.content, src=src)
    lang = LANGUAGES[translated.src]
    return "Translated from (" + lang.capitalize() + "): " + translated.text

client.run(TOKEN)