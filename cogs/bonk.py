from discord.ext import commands
from discord import app_commands
import discord
from util.vars.eind_vars import *
import logging
from util.util import *
from table2ascii import table2ascii as t2a, PresetStyle
import os
import itertools
import time
from datetime import datetime
import math
import discord.errors
from discord.errors import Forbidden

N_CHANNEL_ID = os.getenv('N_CHANNEL_ID')


class Bonk(commands.Cog, name="Bonk"):

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        logging.info(f"[{__name__}] Cog is ready")

    @commands.command()
    async def bonk(self, ctx):
        if not ctx.message.reference:
            await ctx.message.reply("I need someone to bonk. (call !bonk as a reply to another message)")
            return

        guild = ctx.guild
        bonk_timeout_role = discord.utils.get(guild.roles, id=int(os.getenv("BONK_TIMEOUT_ROLE_ID")))

        bonker = ctx.message.author
        bonkee = ctx.message.reference.resolved.author
        last_bonk_time = self.get_last_bonk(bonker)
        current_time = time.time()
        time_diff = current_time - last_bonk_time if last_bonk_time else math.inf

        if guild.get_member(bonkee.id) is None:
            await ctx.message.reply("This user is not currently on the server.")
            return

        if ctx.message.channel.id == int(N_CHANNEL_ID):
            await ctx.message.reply("This is a bonk-free zone.")
            return

        if bonkee == self.bot.user:
            await ctx.message.reply(f"No u {BONK_EMOJI}")
            await ctx.message.add_reaction(BONK_EMOJI)
            self.add_to_leaderboard(bonker)
            self.save_last_bonk(bonker)
            logging.info(f"{bonker.name} tried to bonk me and failed miserably.")
            return

        if bonkee == bonker:
            await ctx.message.reply("No self-bonking.")
            return

        bonk_timeout = BONK_TIMEOUT_SLOW if bonk_timeout_role in bonker.roles else BONK_TIMEOUT

        if time_diff < bonk_timeout:
            next_bonk_time = last_bonk_time + bonk_timeout
            time_until_bonk = next_bonk_time - current_time
            bonk_time_hm = datetime.fromtimestamp(next_bonk_time).strftime("%H:%M")

            hours_until_bonk = int(time_until_bonk // 3600)
            minutes_until_bonk = int((time_until_bonk % 3600) // 60)
            seconds_until_bonk = int((time_until_bonk % 3600) % 60)

            str_time_to_bonk = ""
            if hours_until_bonk:
                str_time_to_bonk = str_time_to_bonk + f" {hours_until_bonk} hours"
            if minutes_until_bonk:
                str_time_to_bonk = str_time_to_bonk + f" {minutes_until_bonk} minutes"
            if seconds_until_bonk:
                str_time_to_bonk = str_time_to_bonk + f" {seconds_until_bonk} seconds"

            msg = "You're on bonk timeout. " if bonk_timeout_role in bonker.roles else "You can only bonk once every 5 minutes. "
            msg = msg + f"You can bonk again in{str_time_to_bonk} (at {bonk_time_hm}). Please wait."
            await ctx.message.reply(msg)
            return

        self.add_to_leaderboard(bonkee)
        self.save_last_bonk(bonker)
        try:
            await ctx.message.reference.resolved.add_reaction(BONK_EMOJI)
        except Forbidden as e:
            await ctx.channel.send(f"{bonkee.mention} has likely blocked Arnol and therefore the bonk reaction cannot be added to their message. Shame.")
            logging.info(f"Failed to add bonk reaction to {bonkee.name}'s message. They have likely blocked this bot.")
        logging.info(f"{bonker.name} bonked {bonkee.name}.")
        return

    @app_commands.command(name="bonktimeout")
    async def bonk_timeout(self, interaction: discord.Interaction, member: discord.Member):
        guild = interaction.guild
        moderator_role = discord.utils.get(guild.roles, id=int(os.getenv("MODERATOR_ROLE_ID")))
        bonk_timeout_role = discord.utils.get(guild.roles, id=int(os.getenv("BONK_TIMEOUT_ROLE_ID")))

        if moderator_role not in interaction.user.roles:
            await interaction.response.send_message("You are not allowed to use this command.", ephemeral=True)
            return

        if bonk_timeout_role not in member.roles:
            await member.add_roles(bonk_timeout_role)
            logging.info(f"Added bonk timeout role to {member.name}")
            await interaction.response.send_message(f"{member.mention} is now on bonk timeout.")
        else:
            await member.remove_roles(bonk_timeout_role)
            logging.info(f"Removed bonk timeout role from {member.name}")
            await interaction.response.send_message(f"{member.mention} is not on bonk timeout anymore.")

        return

    @app_commands.command(name="hallofshame")
    async def bonk_leaderboard(self, interaction: discord.Interaction):
        output, total = self.get_top_n(10)
        embed_title = f"Hall of Shame ({total} total bonks)"

        embed = discord.Embed(title=embed_title, description=f"```{output}```")
        await interaction.response.send_message(embed=embed)
        logging.info(f"Sent bonk leaderboard to {interaction.user.name}")

    def get_top_n(self, num):
        body = []

        leaderboard = load_json_file(get_file(BONK_LEADERBOARD_FILE))
        filtered_leaderboard = dict(itertools.islice(leaderboard['bonks'].items(), num))
        total = leaderboard['total_bonks']

        for k, v in filtered_leaderboard.items():
            percentage = round(v['score']*100/total, 2)
            body.append([v['name'], f"{v['score']} ({percentage}%)"])

        output = t2a(
            header=["Name", "Bonks"],
            body=body,
            style=PresetStyle.ascii_borderless
        )

        return output, total

    def add_to_leaderboard(self, author):
        bonk_file = get_file(BONK_LEADERBOARD_FILE)
        leaderboard = load_json_file(bonk_file)
        author_id = str(author.id)

        bonks = leaderboard['bonks']

        if str(author.id) in bonks.keys():
            bonks[author_id] = {'name': author.name, 'score': bonks[author_id]['score'] + 1}
        else:
            bonks[author_id] = {'name': author.name, 'score': 1}

        leaderboard['total_bonks'] = leaderboard['total_bonks'] + 1

        bonks = {k: v for (k, v) in sorted(bonks.items(), key=lambda x: x[1]['score'], reverse=True)}
        leaderboard['bonks'] = bonks
        save_json_file(leaderboard, bonk_file)

    def get_last_bonk(self, author):
        last_bonks = load_json_file(get_file(LAST_BONK_FILE))
        author_id = str(author.id)
        if (author_id not in last_bonks.keys()):
            return None
        return last_bonks[author_id]["last_bonk"]

    def save_last_bonk(self, author):
        last_bonk_file = get_file(LAST_BONK_FILE)
        last_bonks = load_json_file(last_bonk_file)
        author_id = str(author.id)
        last_bonks[author_id] = {'name': author.name, 'last_bonk': time.time()}
        save_json_file(last_bonks, last_bonk_file)


async def setup(bot: commands.Bot):
    await bot.add_cog(Bonk(bot))
