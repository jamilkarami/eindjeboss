import json
import logging as lg
import os
from datetime import datetime

import discord
import pytz
import requests
from discord import app_commands
from discord.ext import commands

from bot import Eindjeboss
from util.vars.eind_vars import (ASS_EMOJI, CHANNEL_IGNORE_LIST,
                                 EXCLAMATION_EMOJI, HARAM_EMOJI,
                                 QUESTION_EMOJI, TABLE_FIX, TABLE_FLIP,
                                 WICKED_EMOJI)

C_CH_ID = os.getenv("CANDY_CHANNEL_ID")
MSG_URL = "https://discord.com/api/v9/guilds/{}/messages/search?author_id={}"

SPONTAAN_STR = "SPONTAAN. REIZEN. DRANKJES MET DE MEIDEN. SHOPPEN. \
SPECIAALBIER. SUSHI. SARCASME. DANSJES. BOULDEREN. TATOEAGES. UITGAAN. \
TERRASJES."
OPINION = "The Eindhoven Community Discord's collectively humble opinion on %s"
TZ = "Europe/Amsterdam"
MAX_MEMBERS_TAG = 50
MSG_TOTAL_DESC = "Find out how many messages you (or someone else) \
have/has sent in total in this server."


class Messages(commands.Cog, name="Messages"):

    def __init__(self, bot: Eindjeboss):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        lg.info(f"[{__name__}] Cog is ready")

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

    @app_commands.command(name="spontaan")
    async def spontaan(self, interaction: discord.Interaction):
        await interaction.response.send_message(SPONTAAN_STR)

    @app_commands.command(name="misterstinkie")
    async def stinkie(self, interaction: discord.Interaction):
        await interaction.response.send_message("He will be euthanized.")

    @app_commands.command(name="blaze")
    async def blaze(self, interaction: discord.Interaction):
        await interaction.response.send_message(HARAM_EMOJI)

    @commands.Cog.listener()
    async def on_message(self, msg):
        if msg.author == self.bot.user:
            return
        if msg.channel.id in CHANNEL_IGNORE_LIST:
            return

        msg_cont = msg.content.lower()

        cur_time = datetime.now(pytz.timezone(TZ)).strftime("%H:%M")
        times = ["04:20", "4:20", "16:20"]

        if '420' in msg_cont and \
                str(msg.channel.id) == C_CH_ID and cur_time in times:
            await msg.reply(f'Blaze it! {HARAM_EMOJI}')
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

    @app_commands.command(name="tagall")
    async def tagall(self, intr: discord.Interaction):
        if type(intr.channel).__name__ != "Thread":
            await intr.response.send_message(
                "You can only use this command inside threads.",
                ephemeral=True)
            return

        users = await intr.channel.fetch_members()
        if len(users) > MAX_MEMBERS_TAG:
            await intr.response.send_message(
                "This thread has too many members. (>%s)" % MAX_MEMBERS_TAG,
                ephemeral=True)
            return

        message = ""

        for user in users:
            if user.id != self.bot.user.id:
                message = message + f"<@{user.id}> "
        await intr.response.send_message(message)
        lg.info("Tagged everyone in thread %s on behalf of %s",
                intr.channel.name, intr.user.name)

    @app_commands.command(name="mymsgtotal",
                          description=MSG_TOTAL_DESC,)
    async def msgtotal(self, intr: discord.Interaction,
                       user: discord.Member = None):
        guild_id = intr.guild_id
        if not user:
            user = intr.user
        ttl_msg = self.get_total_messages(guild_id, user.id)

        await intr.response.send_message(
            "%s has sent a total of around %s messages in this server."
            % (user.mention, ttl_msg))
        lg.info("Sent message total for %s to %s", user.name, intr.user.name)

    def get_total_messages(self, guild_id, user_id):
        url = MSG_URL.format(guild_id, user_id)
        data = requests.get(url=url, headers={
            "Authorization": os.getenv("DISCORD_AUTH_HEADER")})
        return json.loads(data.content)["total_results"]


async def setup(client: commands.Bot):
    await client.add_cog(Messages(client))
