import traceback

import discord
from discord.ext import commands

from bot import Eindjeboss

ERROR_MSG = "Something went wrong. Please try again later."


class ExceptionHandler(commands.Cog):

    def __init__(self, bot: Eindjeboss):
        self.bot = bot
        self.bot.tree.error(coro=self.__dispatch_to_app_command_handler)

    async def __dispatch_to_app_command_handler(self, interaction, error):
        self.bot.dispatch("app_command_error", interaction, error)

    @commands.Cog.listener()
    async def on_app_command_error(self, intr: discord.Interaction,
                                   err: discord.app_commands.AppCommandError):
        stacktrace = traceback.format_exception(None, err, None)
        msg = "Exception in command **/%s** (%s)\n"

        if not hasattr(intr.message, "jump_url"):
            jump_url = "ephemeral"
        else:
            jump_url = intr.message.jump_url

        await self.bot.alert_owner(msg % (intr.command.name, jump_url))

        log_msg = ""

        for line in stacktrace:
            if len(log_msg) + len(line) > 2000:
                await self.bot.alert_owner(f'```{log_msg}```')
                log_msg = ""
            log_msg = log_msg + line
        await self.bot.alert_owner(f'```{log_msg}```')

        if intr.response.is_done():
            await intr.edit_original_response(content=ERROR_MSG)
            return
        await intr.response.send_message(ERROR_MSG, ephemeral=True)


async def setup(client: Eindjeboss):
    await client.add_cog(ExceptionHandler(client))
