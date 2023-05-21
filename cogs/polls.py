import logging as lg

import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import Modal, TextInput

from bot import Eindjeboss
from util.vars.eind_vars import NO_EMOJI, NUMBER_EMOJIS, YES_EMOJI


class Polls(commands.Cog):

    def __init__(self, bot: Eindjeboss):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        lg.info(f"[{__name__}] Cog is ready")

    class poll_modal(Modal, title="Create a Poll"):
        poll_title = TextInput(
            label="Poll Title", style=discord.TextStyle.short,
            placeholder="Knitting session with your grandma")

        option_1 = TextInput(label="Option 1", style=discord.TextStyle.short,
                             placeholder="Option 1")
        option_2 = TextInput(label="Option 2", style=discord.TextStyle.short,
                             placeholder="Option 2")
        option_3 = TextInput(label="Option 3", style=discord.TextStyle.short,
                             placeholder="Option 3", required=False)
        option_4 = TextInput(label="Option 4", style=discord.TextStyle.short,
                             placeholder="Option 4", required=False)

        async def on_submit(self, intr: discord.Interaction) -> None:
            message = f"**{self.poll_title.value}**\n\n"
            options = [self.option_1,
                       self.option_2,
                       self.option_3,
                       self.option_4]
            options = [option for option in options if option.value]

            for i in range(len(options)):
                message = message + f"{NUMBER_EMOJIS[i]}  {options[i].value}\n"

            message = message + "‎"
            await intr.response.send_message(message)
            msg_reaction = await intr.original_response()

            for i in range(len(options)):
                await msg_reaction.add_reaction(NUMBER_EMOJIS[i])

        async def on_error(self, intr: discord.Interaction,
                           error: Exception) -> None:
            await intr.response.send_message(
                "There was an error with the poll. Please try again.",
                ephemeral=True)
            lg.error(error)

        async def on_timeout(self) -> None:
            return

    @app_commands.command(name="poll",
                          description="Create a poll with up to 4 options")
    async def poll(self, intr: discord.Interaction):
        await intr.response.send_modal(self.poll_modal())
        lg.info("Sent poll to %s", intr.user.name)

    @app_commands.command(name="yesno",
                          description="Shortcut to a yes/no poll")
    async def yesno(self, intr: discord.Interaction, title: str):
        await intr.response.send_message(title)
        resp = await intr.original_response()
        await resp.add_reaction(YES_EMOJI)
        await resp.add_reaction(NO_EMOJI)
        lg.info("Sent yes/no poll to %s", intr.user.name)


async def setup(client: commands.Bot):
    await client.add_cog(Polls(client))
