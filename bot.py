# bot.py
import os
import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv
from vars.eind_vars import *
import asyncio
import logging

async def main():
    logging.basicConfig(filename='eindjeboss.log', format='%(asctime)s %(levelname)-8s %(message)s', level=logging.INFO, datefmt='%Y-%m-%d %H:%M:%S')

    intents = discord.Intents.all()
    client = commands.Bot(command_prefix="!", case_insensitive=True, intents=intents)

    load_dotenv()
    TOKEN = os.getenv('DISCORD_TOKEN')

    @client.event
    async def on_ready():
        print(f'{client.user.name} has connected to Discord!')

    @client.event
    async def on_connect():
        await client.tree.sync()
        print("Commands Synced!")

    async def load_extensions():
        for filename in os.listdir("./cogs"):
            ignore_list = ["eind_vars.py"]
            if filename.endswith(".py") and filename not in ignore_list:
                extension_name = f"cogs.{filename[:-3]}"
                logging.info(f"Loading extension: {extension_name}")
                await client.load_extension(extension_name)

    async with client:
        await load_extensions()
        await client.start(TOKEN)

asyncio.run(main())