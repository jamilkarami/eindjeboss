# bot.py
from asyncio.windows_events import NULL
from fnmatch import translate
import os
import random

import discord
from discord.ext import commands, tasks
from dotenv import load_dotenv
from googletrans import Translator
from googletrans.constants import LANGUAGES

BOOK_EMOJI = "📖"
BONK_TRIGGERS = ["Mommy", "Daddy"]

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

translator = Translator()

client = discord.Client()
bot = commands.Bot("/")

@client.event
async def on_ready():
    print(f'{client.user.name} has connected to Discord!')

@client.event
async def on_message(message):
    if message.author == client.user:
        return
    
    # Translate by reply
    if message.reference and message.content.lower() in ["!translate","!tr"]:
        await message.reference.resolved.reply(translate_message(message.reference.resolved), mention_author=False)
        return

    # Bonk users
    if any(word.lower() in message.content.lower() for word in BONK_TRIGGERS):
        await message.reply("<a:bonk:995996313650999387>")
        return
    
@client.event
async def on_reaction_add(reaction, user):
    if reaction.message.author == client.user:
        return

    # Translate by reaction
    if reaction.emoji == BOOK_EMOJI:
        src_msg = "You asked me to translate the following message: " + reaction.message.content
        dst_msg = translate_message(reaction.message)

        await user.send(content=src_msg)
        await user.send(content=dst_msg)
        return

def translate_message(message):
    translated = translator.translate(message.content)
    lang = LANGUAGES[translated.src]
    return "Translated from (" + lang.capitalize() + "): " + translated.text

# Cat pic per day
@tasks.loop(hours=24)
async def called_once_a_day():
    message_channel = bot.get_channel(1)
    print(f"Got channel {message_channel}")
    await message_channel.send("Your message")

@called_once_a_day.before_loop
async def before():
    await bot.wait_until_ready()
    print("Finished waiting")

client.run(TOKEN)