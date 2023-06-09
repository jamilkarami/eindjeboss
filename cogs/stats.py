import datetime
from datetime import timedelta
import logging as lg

import discord
from aiocron import crontab
from discord.ext import commands

from bot import Eindjeboss
from util.util import get_file, load_json_file, save_json_file
from util.vars.periodics import STATS_SYNC

STATS_FILE_NAME = "command_stats.json"
STATS_BLACKLIST = ["announceevent", "closeticket", "createsetting",
                   "handleticket", "logs", "opentickets", "set", "usertickets"]


class Stats(commands.Cog):

    def __init__(self, bot: Eindjeboss):
        self.bot = bot
        self.comm_stats = self.bot.dbmanager.get_collection('command_stats')
        crontab(STATS_SYNC, self.sync_stats, start=True)

    @commands.Cog.listener()
    async def on_ready(self):
        lg.info(f"[{__name__}] Cog is ready")

    @commands.Cog.listener()
    async def on_app_command_completion(self, intr: discord.Interaction,
                                        command):
        if command.name in STATS_BLACKLIST:
            return
        name = command.name
        if command.name == "Translate Message":
            name = "translate (context)"
        if command.name == "Report Message":
            name = "modmail (context)"
        self.update_stats(f"/{name}")

    def update_stats(self, name):
        stats_file = load_json_file(get_file(STATS_FILE_NAME))
        stats_file[name] = stats_file.get(name, 0) + 1
        save_json_file(stats_file, get_file(STATS_FILE_NAME))

    @commands.Cog.listener()
    async def on_command_completion(self, ctx: commands.Context):
        cmd_name = ctx.command.name
        if cmd_name in STATS_BLACKLIST:
            return
        self.update_stats(f"!{cmd_name}")

    async def sync_stats(self):
        stats = load_json_file(get_file(STATS_FILE_NAME))
        today = datetime.date.today() - timedelta(days=1)
        trunc = datetime.datetime(today.year, today.month, today.day)
        data = {
            "_id": today.strftime("%Y/%m/%d"),
            "date": trunc,
            "usage": stats,
        }
        await self.comm_stats.insert_one(data)
        save_json_file({}, get_file(STATS_FILE_NAME))


async def setup(client: commands.Bot):
    await client.add_cog(Stats(client))
