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
        logging.info(f"[{__name__}] Cog is ready")
        periodics = util.util.load_json_file('periodic_messages')
        periodic_message_count = len(periodics.keys())
        plural = "" if periodic_message_count == 1 else "s"
        for periodic in periodics.keys():
            vals = periodics[periodic]

            msg_time = vals['time']
            msg_channel = vals['channel']
            msg = vals['message']

            crontab(msg_time, func=self.send_periodic_message, args=(msg, msg_channel, guild), start=True)
        logging.info(f"[{__name__}] Scheduled {periodic_message_count} periodic message{plural}")


    async def send_periodic_message(self, message, channel_id, guild):
        channel = await guild.fetch_channel(channel_id)
        await channel.send(message)
        

async def setup(bot):
    await bot.add_cog(Periodics(bot))