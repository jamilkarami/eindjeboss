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
FILE_DIR = os.getenv("FILE_DIR")
SETTING_VALS = {"_id", "description", "value"}


class Eindjeboss(commands.Bot):

    def __init__(self) -> None:
        intents = discord.Intents.all()
        super().__init__(command_prefix="!", case_insensitive=True, intents=intents,
                         owner_id=int(os.getenv("OWNER_ID")))
        self.file_dir = FILE_DIR

    async def setup_hook(self):
        if hasattr(time, "tzset"):
            os.environ["TZ"] = "Europe/Amsterdam"
            time.tzset()

        if os.path.exists(TEMP) and os.path.isdir(TEMP):
            shutil.rmtree(TEMP)
        shutil.copytree("default_files", FILE_DIR, dirs_exist_ok=True)

        self.dbmanager = DbManager()
        self.settings = self.dbmanager.get_collection("settings")
        self.cmds = self.dbmanager.get_collection("commands")
        await self.load_extensions()
        await self.load_settings()

    async def sync_and_update(self):
        cmds = await self.tree.sync()
        cmd_mentions = {f"/{cmd.name}": cmd.mention for cmd in cmds}
        await self.cmds.drop()
        await self.cmds.insert_one(cmd_mentions)

    async def get_setting(self, name: str, default=None):
        name = name.lower()
        try:
            return getattr(self, name)
        except AttributeError:
            msg = "Setting %s not found. Defaulting to %s" % (name, default)
            logging.info(msg)
            await self.alert_owner(msg)
            return default

    async def load_extensions(self):
        for filename in os.listdir("./cogs"):
            if not filename.endswith("py"):
                continue
            extension_name = f"cogs.{filename[:-3]}"
            logging.info(f"Loading extension: {extension_name}")
            await self.load_extension(extension_name)
        logging.info("Finished loading extensions")

    async def load_settings(self):
        settings = await self.settings.find({}).to_list(length=88675309)
        for setting in settings:
            self.__setattr__(setting["_id"], setting["value"])
        logging.info("Finished loadings settings")

    async def load_activity(self):
        activity_type = discord.ActivityType[await self.get_setting("activitytype")]
        status = await self.get_setting("activitystatus")

        activity = discord.Activity(type=activity_type, detail="", name=status)
        await self.change_presence(activity=activity)

    async def add_setting(self, setting):
        if setting.keys() != SETTING_VALS:
            raise ValueError(f"Setting {setting} does not match expected fields")

        self.__setattr__(setting["_id"], setting["value"])
        await self.settings.insert_one(setting)
        logging.info("Added setting %s with value %s", setting["_id"], setting["value"])

    async def update_setting(self, setting):
        self.__setattr__(setting["_id"], setting["value"])
        return await self.settings.find_one_and_update({"_id": setting["_id"]},
                                                       {"$set": {"value": setting["value"]}})

    async def get_settings(self):
        settings = await self.settings.find({}).to_list(length=88675309)
        return settings

    async def alert_owner(self, message):
        owner = await self.fetch_user(self.owner_id)
        await owner.send(message)

    async def alert_mods(self, message):
        ticket_channel_id = await self.get_setting("modmail_channel", None)
        channel = await self.fetch_channel(ticket_channel_id)

        await channel.send(message)


async def main():
    logging_dir = f"{FILE_DIR}/logs"
    logging_file_name = logging_dir + "/eindjeboss.log"

    os.makedirs(logging_dir, exist_ok=True)
    if not Path(logging_file_name).is_file():
        open(logging_file_name, "a").close()

    log_format = logging.Formatter("%(asctime)s %(levelname)-8s %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
    log_handler = RotatingFileHandler(filename=logging_file_name, mode="a", maxBytes=5 * 1024 * 1024, backupCount=10,
                                      encoding=None, delay=False)

    discord.utils.setup_logging(handler=log_handler, formatter=log_format)

    client = Eindjeboss()

    @client.event
    async def on_ready():
        await client.load_activity()
        print(f"{client.user.name} is ready to serve.")

    async with client:
        await client.start(os.getenv("DISCORD_TOKEN"))


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Powering down...")
