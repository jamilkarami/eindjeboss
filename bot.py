import asyncio
import discord
import logging
import os
import shutil
import time
from discord.ext import commands
from dotenv import load_dotenv
from logging.handlers import RotatingFileHandler
from pathlib import Path

TEMP = "temp"


async def main():
    load_dotenv()
    TOKEN = os.getenv("DISCORD_TOKEN")
    STATUS = os.getenv("BOT_STATUS")
    FILE_DIR = os.getenv("FILE_DIR")

    logging_file_name = f"{FILE_DIR}/logs/eindjeboss.log"

    if not Path(logging_file_name).is_file():
        open(logging_file_name, 'a').close()

    log_format = logging.Formatter('%(asctime)s %(levelname)-8s %(message)s',
                                   datefmt='%Y-%m-%d %H:%M:%S')
    log_handler = RotatingFileHandler(logging_file_name, mode='a',
                                      maxBytes=5*1024*1024, backupCount=10,
                                      encoding=None, delay=0)
    log_handler.setFormatter(log_format)
    log_handler.setLevel(logging.INFO)

    app_log = logging.getLogger('root')
    app_log.setLevel(logging.INFO)
    app_log.addHandler(log_handler)

    intents = discord.Intents.all()
    activity = discord.Activity(
        type=discord.ActivityType.listening, detail="", name=STATUS
    )
    intents.members = True
    client = commands.Bot(
        command_prefix="!", case_insensitive=True,
        intents=intents, activity=activity
    )

    @client.event
    async def on_ready():
        print(f"{client.user.name} is ready to serve.")

    @client.event
    async def on_connect():
        print(f"{client.user.name} has connected to discord!")
        if hasattr(time, 'tzset'):
            os.environ['TZ'] = 'Europe/Amsterdam'
            time.tzset()
        await client.tree.sync()

    async def load_extensions():
        for filename in os.listdir("cogs"):
            if not filename.endswith("py"):
                continue
            extension_name = f"cogs.{filename[:-3]}"
            logging.info("Loading extension: %s" % extension_name)
            await client.load_extension(extension_name)

    def prepare_files():
        if os.path.exists(TEMP) and os.path.isdir(TEMP):
            shutil.rmtree(TEMP)
        shutil.copytree("default_files", FILE_DIR, dirs_exist_ok=True)

    async with client:
        prepare_files()
        await load_extensions()
        await client.start(TOKEN)


try:
    asyncio.run(main())
except KeyboardInterrupt:
    print("Eindjeboss powering down...")
