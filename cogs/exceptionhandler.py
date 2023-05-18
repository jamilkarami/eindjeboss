import os
import traceback

import discord
from discord.ext import commands


class ExceptionHandler(commands.Cog):

    def __init__(self, client: commands.Bot):
        self.client = client
        self.client.tree.error(coro=self.__dispatch_to_app_command_handler)

    async def __dispatch_to_app_command_handler(self, interaction, error):
        self.client.dispatch("app_command_error", interaction, error)

    @commands.Cog.listener()
    async def on_app_command_error(self, intr: discord.Interaction,
                                   err: discord.app_commands.AppCommandError):
        rd_id = os.getenv('RAGDOLL_ID')
        user = await intr.guild.fetch_member(rd_id)
        stacktrace = ''.join(traceback.format_exception(err))
        msg = "Exception in command **/%s**\n```logs\n%s```"
        await user.send(msg % (intr.command.name, stacktrace))


async def setup(client: commands.Bot):
    await client.add_cog(ExceptionHandler(client))
