import discord
import os
import itertools
import time
import logging
import math
import discord.errors
import matplotlib.pyplot as plt
from util.vars.eind_vars import *
from util.util import *
from datetime import datetime
from discord.ext import commands
from discord import app_commands
from discord.errors import Forbidden

N_CHANNEL_ID = os.getenv("N_CHANNEL_ID")
HALL_OF_SHAME_FILE = "hallofshame.png"


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

        bonk_timeout = (BONK_TIMEOUT_SLOW if bonk_timeout_role in bonker.roles else BONK_TIMEOUT)

        if time_diff < bonk_timeout:
            msg = self.get_timeout_str(bonk_timeout, bonk_timeout_role, bonker, current_time, last_bonk_time)
            await ctx.message.reply(msg)
            return

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

        self.add_to_leaderboard(bonkee)
        self.save_last_bonk(bonker)
        try:
            await ctx.message.reference.resolved.add_reaction(BONK_EMOJI)
        except Forbidden:
            await ctx.channel.send(
                f"{bonkee.mention} has likely blocked Arnol and therefore the bonk reaction ({BONK_EMOJI}) "
                f"cannot be added to their message. Shame.")
            logging.info(f"Failed to add bonk reaction to {bonkee.name}'s message. They have likely blocked this bot.")
        logging.info(f"{bonker.name} bonked {bonkee.name}.")

    def get_timeout_str(self, bonk_timeout, bonk_timeout_role, bonker, current_time, last_bonk_time):
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
        msg = ("You're on bonk timeout. " if bonk_timeout_role in bonker.roles else
               "You can only bonk once every 5 minutes. ")
        msg = (msg + f"You can bonk again in{str_time_to_bonk} (at {bonk_time_hm}). Please wait.")
        return msg

    @app_commands.command(name="mybonks", description="See how many times you've been bonked.")
    async def mybonks(self, interaction: discord.Interaction):
        leaderboard = load_json_file(get_file(BONK_LEADERBOARD_FILE))
        score = leaderboard.get("bonks").get(str(interaction.user.id)).get("score")
        if not score:
            await interaction.response.send_message("You have not been bonked yet.", ephemeral=True)
            return
        await interaction.response.send_message(f"You have been bonked {score} time{'s'[:score ^ 1]} so far.",
                                                ephemeral=True)

    @app_commands.command(name="bonktimeout", description="Put a user on bonk timeout, increasing their wait time "
                                                          "between bonks from 5 minutes to 4 hours.", )
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

    @app_commands.command(name="hallofshame", description="Show the Bonk leaderboard/hall of shame.")
    async def bonk_leaderboard(self, interaction: discord.Interaction):
        names, scores, total = self.get_top_n(10)

        # colors
        colors = ['#BFDAFE', '#DEEAE3', '#E3DFD5', '#E7CED4', '#DDC3D8', '#C5BDED', '#DAE795', '#FBFBCC', '#BCE0F0',
                  '#ECE4D0']

        fig1, ax1 = plt.subplots()
        fig1.set_facecolor('#36393E')

        def make_autopct(values):
            def my_autopct(pct):
                ttl = sum(values)
                val = int(round(pct * ttl / 100.0))
                actual_pct = val / total * 100
                return f'{val:d}\n({actual_pct:.0f}%)'

            return my_autopct

        patches, texts, autotexts = ax1.pie(scores, colors=colors, labels=names, autopct=make_autopct(scores),
                                            pctdistance=0.85, rotatelabels=True, shadow=True)
        for text in texts:
            text.set_color('white')
        for autotext in autotexts:
            autotext.set_color('grey')

        centre_circle = plt.Circle((0, 0), 0.70, fc='#36393E')
        fig = plt.gcf()
        fig.gca().add_artist(centre_circle)

        ax1.axis('equal')
        legend = plt.legend(patches[:3], names[:3], loc="center", title="Hall of Shame", labelcolor="white")
        legend.get_frame().set_facecolor('#36393E')
        plt.setp(legend.get_title(), color='white')
        plt.tight_layout()

        plt.savefig(HALL_OF_SHAME_FILE, transparent=True)

        await interaction.response.send_message(file=discord.File(HALL_OF_SHAME_FILE))
        os.remove(HALL_OF_SHAME_FILE)
        logging.info(f"Sent bonk leaderboard to {interaction.user.name}")

    def get_top_n(self, num):
        leaderboard = load_json_file(get_file(BONK_LEADERBOARD_FILE))
        filtered_leaderboard = dict(itertools.islice(leaderboard['bonks'].items(), num))
        total = leaderboard['total_bonks']

        names = []
        scores = []

        for k, v in filtered_leaderboard.items():
            names.append(v['name'])
            scores.append(v['score'])

        return names, scores, total

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
        if author_id not in last_bonks.keys():
            return None
        return last_bonks[author_id]["last_bonk"]

    def save_last_bonk(self, author):
        last_bonk_file = get_file(LAST_BONK_FILE)
        last_bonks = load_json_file(last_bonk_file)
        author_id = str(author.id)
        last_bonks[author_id] = {"name": author.name, "last_bonk": time.time()}
        save_json_file(last_bonks, last_bonk_file)


async def setup(bot: commands.Bot):
    await bot.add_cog(Bonk(bot))
