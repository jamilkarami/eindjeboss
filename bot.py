import asyncio
import logging
import os
import shutil
import time
from logging.handlers import RotatingFileHandler
from pathlib import Path

import discord
from discord.ext import commands
from dotenv import load_dotenv

from util.db import DbManager

load_dotenv()
TEMP = "temp"
STATUS = os.getenv("BOT_STATUS")
FILE_DIR = os.getenv("FILE_DIR")


class Eindjeboss(commands.Bot):

    def __init__(self) -> None:
        intents = discord.Intents.all()
        activity = discord.Activity(
            type=discord.ActivityType.listening, detail="", name=STATUS)
        super().__init__(command_prefix="!", case_insensitive=True,
                         intents=intents, activity=activity,
                         owner_id=os.getenv('RAGDOLL_ID'))

    async def setup_hook(self):
        if hasattr(time, 'tzset'):
            os.environ['TZ'] = 'Europe/Amsterdam'
            time.tzset()

        if os.path.exists(TEMP) and os.path.isdir(TEMP):
            shutil.rmtree(TEMP)
        shutil.copytree("default_files", FILE_DIR, dirs_exist_ok=True)

        self.dbmanager = DbManager()
        await self.load_extensions()
        await self.tree.sync()

    async def load_extensions(self):
        for filename in os.listdir("./cogs"):
            if not filename.endswith('py'):
                continue
            extension_name = f"cogs.{filename[:-3]}"
            logging.info(f"Loading extension: {extension_name}")
            await self.load_extension(extension_name)


async def main():
    TOKEN = os.getenv("DISCORD_TOKEN")

    logging_file_name = f"{FILE_DIR}/logs/eindjeboss.log"

    if not Path(logging_file_name).is_file():
        open(logging_file_name, 'a').close()

    log_format = logging.Formatter('%(asctime)s %(levelname)-8s %(message)s',
                                   datefmt='%Y-%m-%d %H:%M:%S')
    log_handler = RotatingFileHandler(logging_file_name, mode='a',
                                      maxBytes=5*1024*1024, backupCount=10,
                                      encoding=None, delay=0)

    discord.utils.setup_logging(handler=log_handler, formatter=log_format)

    client = Eindjeboss()

    @client.event
    async def on_ready():
        print(f"{client.user.name} is ready to serve.")

    async with client:
        await client.start(TOKEN)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Powering down...")
