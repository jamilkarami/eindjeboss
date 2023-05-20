import logging as lg
from datetime import date
from typing import Union

import discord
from aiocron import crontab
from discord import app_commands
from discord.ext import commands

from util.util import get_file, load_json_file, save_json_file
from util.vars.periodics import STATS_SYNC

STATS_FILE_NAME = "command_stats.json"
STATS_BLACKLIST = ["announceevent", "closeticket", "handleticket", "logs",
                   "opentickets", "usertickets"]


class Stats(commands.Cog):

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.comm_stats = self.bot.dbmanager.get_collection('command_stats')
        crontab(STATS_SYNC, self.sync_stats, start=True)

    @commands.Cog.listener()
    async def on_ready(self):
        lg.info(f"[{__name__}] Cog is ready")

    @commands.Cog.listener()
    async def on_app_command_completion(self, intr: discord.Interaction,
                                        command):
        if command.name in self.blacklist:
            return
        self.update_stats(f"/{command.name}")

    def update_stats(self, name):
        stats_file = load_json_file(get_file(STATS_FILE_NAME))
        stats_file[name] = stats_file.get(name, 0) + 1
        save_json_file(stats_file, get_file(STATS_FILE_NAME))

    async def sync_stats(self):
        stats = load_json_file(get_file(STATS_FILE_NAME))
        today = date.today().strftime('%Y/%m/%d')
        await self.comm_stats.update_one({"_id": today}, {"$inc": stats},
                                         upsert=True)
        save_json_file({}, get_file(STATS_FILE_NAME))


async def setup(client: commands.Bot):
    await client.add_cog(Stats(client))
