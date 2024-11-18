import logging as lg
from datetime import datetime

import discord
import pytz
from discord import app_commands
from discord.ext import commands

from bot import Eindjeboss
from util.vars.eind_vars import (ASS_EMOJI, CHANNEL_IGNORE_LIST,
                                 EXCLAMATION_EMOJI,
                                 QUESTION_EMOJI, TABLE_FIX, TABLE_FLIP,
                                 WICKED_EMOJI)

SPONTAAN_STR = "**SPONTAAN. REIZEN. DRANKJES MET DE MEIDEN. SHOPPEN. \
SPECIAALBIER. SUSHI. SARCASME. DANSJES. BOULDEREN. TATOEAGES. UITGAAN. \
TERRASJES.**"
ICE_CREAM_STR = "ICE CREAM\nYES WERE GETTING ICE CREAM\nTODAY\nSTRIJP\nBY PURCHASING IT\nITS LEGAL YES\nYES"
TZ = "Europe/Amsterdam"


class Messages(commands.GroupCog, name="msg"):

    def __init__(self, bot: Eindjeboss):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        lg.info(f"[{__name__}] Cog is ready")

    @app_commands.command(name="spontaan")
    async def spontaan(self, interaction: discord.Interaction):
        await interaction.response.send_message(SPONTAAN_STR)

    @app_commands.command(name="misterstinkie")
    async def stinkie(self, interaction: discord.Interaction):
        await interaction.response.send_message("He will be euthanized.")

    @app_commands.command(name="icecream")
    async def icecream(self, interaction: discord.Interaction):
        await interaction.response.send_message(ICE_CREAM_STR)

    @commands.Cog.listener()
    async def on_message(self, msg: discord.Message):
        if msg.author == self.bot.user:
            return
        if msg.channel.id in CHANNEL_IGNORE_LIST:
            return

        msg_cont = msg.content.lower()

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

        if msg_cont == "ok!?":
            await msg.add_reaction(WICKED_EMOJI)
            await msg.add_reaction(EXCLAMATION_EMOJI)
            await msg.add_reaction(QUESTION_EMOJI)
            return

        if msg_cont == "ass":
            await msg.add_reaction(ASS_EMOJI)


async def setup(client: Eindjeboss):
    await client.add_cog(Messages(client))
