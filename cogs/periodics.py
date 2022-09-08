import discord
from discord import app_commands
from discord.ext import commands
import logging
import os
import util.util
from aiocron import crontab

class Periodics(commands.Cog):

    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_ready(self):
        guild_id = os.getenv("GUILD_ID")
        guild = await self.client.fetch_guild(guild_id)
        logging.info(f"{__name__} Cog is ready")
        periodics = util.util.load_json_file('periodic_messages')
        logging.info("Scheduling periodic messages")
        for periodic in periodics.keys():
            vals = periodics[periodic]

            msg_time = vals['time']
            msg_channel = vals['channel']
            msg = vals['message']

            crontab(msg_time, func=self.send_periodic_message, args=(msg, msg_channel, guild), start=True)


    async def send_periodic_message(self, message, channel_id, guild):
        channel = await guild.fetch_channel(channel_id)
        await channel.send(message)
        

async def setup(bot):
    await bot.add_cog(Periodics(bot))