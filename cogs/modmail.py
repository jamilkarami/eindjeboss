import logging as lg

import discord
from discord import app_commands
from discord.ext import commands

from bot import Eindjeboss
from .tickets import TicketModal


class Modmail(commands.Cog):

    def __init__(self, bot: Eindjeboss):
        self.bot = bot
        self.ctx_menu = app_commands.ContextMenu(
            name="Report Message",
            callback=self.report_message,
        )
        self.bot.tree.add_command(self.ctx_menu)
        self.tickets = self.bot.dbmanager.get_collection("tickets")

    @commands.Cog.listener()
    async def on_ready(self):
        lg.info(f"[{__name__}] Cog is ready")

    @app_commands.command(name="modmail")
    async def modmail(self, intr: discord.Interaction):
        await intr.response.send_modal(TicketModal(self.tickets, self.bot))
        lg.info("Sent ticket modal to %s", intr.user.display_name)

    async def report_message(self, intr: discord.Interaction, msg: discord.Message):
        await intr.response.send_modal(TicketModal(self.tickets, self.bot, msg))
        lg.info("Sent ticket modal to %s for message %s", intr.user.display_name, msg.jump_url)


async def setup(client: Eindjeboss):
    await client.add_cog(Modmail(client))
