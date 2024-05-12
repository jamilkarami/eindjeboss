import logging as lg
from datetime import datetime

import discord
import pytz
from discord import app_commands
from discord.ext import commands

from bot import Eindjeboss
from util.vars.eind_vars import (ASS_EMOJI, CHANNEL_IGNORE_LIST,
                                 EXCLAMATION_EMOJI, HARAM_EMOJI,
                                 QUESTION_EMOJI, TABLE_FIX, TABLE_FLIP,
                                 WICKED_EMOJI)

SPONTAAN_STR = "SPONTAAN. REIZEN. DRANKJES MET DE MEIDEN. SHOPPEN. \
SPECIAALBIER. SUSHI. SARCASME. DANSJES. BOULDEREN. TATOEAGES. UITGAAN. \
TERRASJES."
ICE_CREAM_STR = "ICE CREAM\nYES WERE GETTING ICE CREAM\nTODAY\nSTRIJP\nBY PURCHASING IT\nITS LEGAL YES\nYES"
OPINION = "The Eindhoven Community Discord's collectively humble opinion on %s"
TZ = "Europe/Amsterdam"


class Messages(commands.GroupCog, name="msg"):

    def __init__(self, bot: Eindjeboss):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        lg.info(f"[{__name__}] Cog is ready")

    @app_commands.command(name="msi",
                          description=OPINION % "MSI")
    async def f_msi(self, interaction: discord.Interaction):
        await interaction.response.send_message("#FuckMSI")

    @app_commands.command(name="meta",
                          description=OPINION % "Meta")
    async def f_meta(self, interaction: discord.Interaction):
        await interaction.response.send_message("#FuckMeta")

    @app_commands.command(name="lenovo",
                          description=OPINION % "Lenovo")
    async def f_lenovo(self, interaction: discord.Interaction):
        await interaction.response.send_message("#FuckLenovo")

    @app_commands.command(name="fontys",
                          description=OPINION % "Fontys")
    async def f_fontys(self, interaction: discord.Interaction):
        await interaction.response.send_message("#FuckFontys")

    @app_commands.command(name="summa",
                          description=OPINION % "Summa")
    async def f_summa(self, interaction: discord.Interaction):
        await interaction.response.send_message("#FuckSumma")

    @app_commands.command(name="solutio365",
                          description=OPINION % "Solutio365")
    async def solutio365(self, interaction: discord.Interaction):
        await interaction.response.send_message("#FuckSolutio365")

    @app_commands.command(name="dhl",
                          description=OPINION % "DHL")
    async def dhl(self, interaction: discord.Interaction):
        await interaction.response.send_message("#FuckDHL")

    @app_commands.command(name="spontaan")
    async def spontaan(self, interaction: discord.Interaction):
        await interaction.response.send_message(SPONTAAN_STR)

    @app_commands.command(name="misterstinkie")
    async def stinkie(self, interaction: discord.Interaction):
        await interaction.response.send_message("He will be euthanized.")

    @app_commands.command(name="blaze")
    async def blaze(self, interaction: discord.Interaction):
        await interaction.response.send_message(HARAM_EMOJI)

    @app_commands.command(name="icecream")
    async def icecream(self, interaction: discord.Interaction):
        await interaction.response.send_message(ICE_CREAM_STR)

    @commands.Cog.listener()
    async def on_message(self, msg: discord.Message):
        if msg.author == self.bot.user:
            return
        if msg.channel.id in CHANNEL_IGNORE_LIST:
            return

        tz = await self.bot.get_setting("timezone")
        ft_channel_id = await self.bot.get_setting("420_channel_id")

        msg_cont = msg.content.lower()

        cur_time = datetime.now(pytz.timezone(tz)).strftime("%H:%M")
        times = ["04:20", "4:20", "16:20"]
        times_tt = ["04:22", "4:22", "16:22"]

        if '420' in msg_cont and \
                msg.channel.id == ft_channel_id and cur_time in times:
            await msg.reply(f'Blaze it! {HARAM_EMOJI}')
            return

        if '422' in msg_cont and \
                msg.channel.id == ft_channel_id and cur_time in times_tt:
            await msg.reply(f'422 is 420 too {HARAM_EMOJI}')
            return

        if TABLE_FLIP in msg_cont:
            await msg.reply(f"Respect tables. {TABLE_FIX}")
            return

        if msg_cont == "ok" or msg_cont == "--- -.-":
            await msg.add_reaction(WICKED_EMOJI)
            return

        if msg_cont == "ok?":
            await msg.add_reaction(WICKED_EMOJI)
            await msg.add_reaction(QUESTION_EMOJI)
            return

        if msg_cont == "ok!":
            await msg.add_reaction(WICKED_EMOJI)
            await msg.add_reaction(EXCLAMATION_EMOJI)
            return

        if msg_cont == "ass":
            await msg.add_reaction(ASS_EMOJI)


async def setup(client: Eindjeboss):
    await client.add_cog(Messages(client))
