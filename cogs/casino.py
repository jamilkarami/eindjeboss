import discord
import random
import logging
from util.vars.eind_vars import *
from discord import app_commands
from discord.ext import commands

DEFAULT_ROLL = 20
ROLL_FOR_TEXT = "roll for "
HEY_ARNOL_TEXT = "hey arnol, "
EIGHT_BALL_OPTIONS = ["Yes ✅", "It is decidedly so ✅", "All signs point to yes ✅", "Definitely ✅",
            "No ❌", "I don't think so ❌", "Don't count on it ❌", "My sources say nope ❌"]

class Casino(commands.Cog):

    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.client.user:
            return
        if message.channel.name in CHANNEL_IGNORE_LIST:
            return

        message_content : str = message.content.lower()

        if message_content.startswith(ROLL_FOR_TEXT):
            reason_for_roll = message_content[len(ROLL_FOR_TEXT):]
            random.seed()
            num = random.randint(1, DEFAULT_ROLL)
            await message.reply(f"You roll a D20 for _\"{reason_for_roll}\"_. You get a {num}.")
            return

        if message_content.startswith(HEY_ARNOL_TEXT) and message_content.endswith("?"):
            random.seed()
            answer = random.choice(EIGHT_BALL_OPTIONS)
            await message.reply(answer)
            return

        return


    @commands.Cog.listener()
    async def on_ready(self):
        logging.info(f"[{__name__}] Cog is ready")

    @app_commands.command()
    async def roll(self, interaction: discord.Interaction, max: int = None):
        if not max:
            max = DEFAULT_ROLL
        if max < 2:
            await interaction.response.send_message("The maximum can only be 2 and above. Please try again.", ephemeral=True)
            return

        random.seed()
        num = random.randint(1, max)

        await interaction.response.send_message("You roll a D{max}. You get: {num}.".format(max=str(max), num=str(num)))
        return

    @app_commands.command(name="8ball")
    async def ball(self, interaction: discord.Interaction):
        random.seed()
        message = f"Magic 8 ball says: {random.choice(EIGHT_BALL_OPTIONS)}"
        await interaction.response.send_message(message)
        return

    @app_commands.command()
    async def coin(self, interaction: discord.Interaction):
        options = ["Heads", "Tails"]
        random.seed()
        message = f"You flip a coin. It lands on: {random.choice(options)}"
        await interaction.response.send_message(message)
        return

    @app_commands.command(name="chooseforme", description="Let Arnol choose from a list of options. Handy for when you don't know what to pick.")
    async def choose(self, interaction: discord.Interaction, options: str):
        split_options = [x.strip().capitalize() for x in options.split(',')]
        response_options = ", ".join([f"**{x}**" for x in split_options])
        random.seed()
        choice = random.choice(
            split_options) if "takumi" not in options.lower() else "Takumi"
        response_text = f"You asked me to choose from {response_options}.\n\nI choose: **{choice}**"

        await interaction.response.send_message(response_text)
        return
        


async def setup(bot):
    await bot.add_cog(Casino(bot))
