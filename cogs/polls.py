import discord
from discord.ext import commands
from discord import app_commands
from discord.ui import Modal, TextInput
from util.vars.eind_vars import *
import logging


class Polls(commands.Cog):

    @commands.Cog.listener()
    async def on_ready(self):
        logging.info(f"{__name__} Cog is ready")

    class poll_modal(Modal, title="Create a Poll"):
        poll_title = TextInput(label="Poll Title", style=discord.TextStyle.short,
                               placeholder="Knitting session with your grandma")

        option_1 = TextInput(
            label="Option 1", style=discord.TextStyle.short, placeholder="Option 1")
        option_2 = TextInput(
            label="Option 2", style=discord.TextStyle.short, placeholder="Option 2")
        option_3 = TextInput(label="Option 3", style=discord.TextStyle.short,
                             placeholder="Option 3", required=False)
        option_4 = TextInput(label="Option 4", style=discord.TextStyle.short,
                             placeholder="Option 4", required=False)

        async def on_submit(self, interaction: discord.Interaction) -> None:
            message = f"**{self.poll_title.value}**\n\n"
            options = [self.option_1, self.option_2,
                       self.option_3, self.option_4]
            options = [option for option in options if option.value]

            for i in range(len(options)):
                message = message + f"{NUMBER_EMOJIS[i]}  {options[i].value}\n"

            message = message + "‎"
            await interaction.response.send_message(message)
            msg_reaction = await interaction.original_response()

            for i in range(len(options)):
                await msg_reaction.add_reaction(NUMBER_EMOJIS[i])

            return

    @app_commands.command(name="poll", description="Create a poll with up to 4 options")
    async def poll(self, interaction: discord.Interaction):
        await interaction.response.send_modal(self.poll_modal())
        return

    @app_commands.command(name="yesno", description="Shortcut to a yes/no poll")
    async def yesno(self, interaction: discord.Interaction, title: str):
        await interaction.response.send_message(title)
        resp = await interaction.original_response()
        await resp.add_reaction(YES_EMOJI)
        await resp.add_reaction(NO_EMOJI)
        return


async def setup(bot):
    await bot.add_cog(Polls(bot))
