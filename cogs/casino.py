import logging
from discord.ext import commands
import discord
from discord import app_commands
import random
import time


class Casino(commands.Cog):

    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_ready(self):
        logging.info(f"{__name__} Cog is ready")

    @app_commands.command()
    async def roll(self, interaction: discord.Interaction, max: int = None):
        if not max:
            max = 20

        random.seed(time.time())
        num = random.randint(1, max)

        await interaction.response.send_message("You roll a D{max}. You get: {num}.".format(max=str(max), num=str(num)))
        return

    @app_commands.command(name="8ball")
    async def ball(self, interaction: discord.Interaction):
        options = ["Yes ✅", "It is decidedly so ✅", "All signs point to yes ✅", "Definitely ✅",
                   "No ❌", "I don't think so ❌", "Don't count on it ❌", "My sources say nope ❌"]
        random.seed(time.time())
        message = f"Magic 8 ball says: {random.choice(options)}"
        await interaction.response.send_message(message)
        return

    @app_commands.command()
    async def coin(self, interaction: discord.Interaction):
        options = ["Heads", "Tails"]
        random.seed(time.time())
        message = f"You flip a coin. It lands on: {random.choice(options)}"
        await interaction.response.send_message(message)
        return


async def setup(bot):
    await bot.add_cog(Casino(bot))
