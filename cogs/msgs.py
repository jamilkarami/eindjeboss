from discord.ext import commands
from discord import app_commands
import logging
import discord
from util.vars.eind_vars import *
from datetime import datetime
import os
from discord.threads import ThreadMember

CANDY_CHANNEL_ID = os.getenv('CANDY_CHANNEL_ID')


class Messages(commands.Cog, name="Messages"):

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        logging.info(f"[{__name__}] Cog is ready")

    @app_commands.command(name="fc", description="Free Cuntus")
    async def free_cuntus(self, interaction: discord.Interaction):
        await interaction.response.send_message("#FreeCuntus")

    @app_commands.command(name="fa", description="Free Anisha")
    async def free_anisha(self, interaction: discord.Interaction):
        await interaction.response.send_message("#FreeAnisha")

    @app_commands.command(name="fg", description="Free Graggy")
    async def free_graggy(self, interaction: discord.Interaction):
        await interaction.response.send_message("#FreeGraggy")

    @app_commands.command(name="msi",
                          description="The Eindhoven Community Discord's collectively humble opinion on MSI")
    async def f_msi(self, interaction: discord.Interaction):
        await interaction.response.send_message("#FuckMSI")

    @app_commands.command(name="lenovo",
                          description="The Eindhoven Community Discord's collectively humble opinion on Lenovo")
    async def f_lenovo(self, interaction: discord.Interaction):
        await interaction.response.send_message("#FuckLenovo")

    @app_commands.command(name="fontys",
                          description="The Eindhoven Community Discord's collectively humble opinion on Fontys")
    async def f_fontys(self, interaction: discord.Interaction):
        await interaction.response.send_message("#FuckFontys")

    @app_commands.command(name="blaze")
    async def blaze(self, interaction: discord.Interaction):
        await interaction.response.send_message(HARAM_EMOJI)

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user:
            return
        if message.channel.id in CHANNEL_IGNORE_LIST:
            return

        message_content = message.content.lower()

        current_time = datetime.now().strftime('%H:%M')
        times = ["04:20", "4:20", "16:20"]

        if '420' in message_content and str(message.channel.id) == CANDY_CHANNEL_ID and current_time in times:
            await message.reply(f'Blaze it! {HARAM_EMOJI}')
            return

        if TABLE_FLIP in message_content:
            await message.reply(f"Respect tables. {TABLE_FIX}")
            return

        if message_content == "ok":
            await message.add_reaction(WICKED_EMOJI)
            return

        if message_content == "ok?":
            await message.add_reaction(WICKED_EMOJI)
            await message.add_reaction(QUESTION_EMOJI)
            return

        if message_content == "ass":
            await message.add_reaction(ASS_EMOJI)
            return

        return

    @app_commands.command(name="tagall")
    async def tagall(self, interaction: discord.Interaction):
        if type(interaction.channel).__name__ != "Thread":
            await interaction.response.send_message("You can only use this command inside threads.", ephemeral=True)
            return

        users = await interaction.channel.fetch_members()
        message = ""
        user: ThreadMember
        for user in users:
            if user.id != self.bot.user.id:
                message = message + f"<@{user.id}> "
        await interaction.response.send_message(message)


async def setup(bot):
    await bot.add_cog(Messages(bot))
