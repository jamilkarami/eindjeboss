from discord.ext import commands
from discord import app_commands
import logging
import discord


class Messages(commands.Cog, name="Messages"):

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        logging.info(f"{__name__} Cog is ready")

    @app_commands.command(name="fc", description="Free Cuntus")
    async def free_cuntus(self, interaction: discord.Interaction):
        await interaction.response.send_message("#FreeCuntus")

    @app_commands.command(name="msi", description="The Eindhoven Community Discord's collectively humble opinion on MSI")
    async def f_msi(self, interaction: discord.Interaction):
        await interaction.response.send_message("#FuckMSI")

    @app_commands.command(name="lenovo", description="The Eindhoven Community Discord's collectively humble opinion on Lenovo")
    async def f_lenovo(self, interaction: discord.Interaction):
        await interaction.response.send_message("#FuckLenovo")


async def setup(bot):
    await bot.add_cog(Messages(bot))
