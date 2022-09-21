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

        if ctx.message.channel.id == int(N_CHANNEL_ID):
            await ctx.message.reply("This is a bonk-free zone.")
            return
        if(bonkee == self.bot.user):
            await ctx.message.reply(f"No u {BONK_EMOJI}")
            self.add_to_leaderboard(bonker)
            return
        if(bonkee == bonker):
            await ctx.message.reply("No self-bonking.")
            return
        if(bonk_timeout_role in bonker.roles and self.get_last_bonk(bonker) is not None and time.time() - self.get_last_bonk(bonker) < BONK_TIMEOUT_SLOW):
            await ctx.message.reply("You're on bonk timeout. You can only bonk once every 4 hours. Please wait.")
            return
        if(self.get_last_bonk(bonker) is not None and time.time() - self.get_last_bonk(bonker) < BONK_TIMEOUT):
            await ctx.message.reply("You can only bonk once every 5 minutes. Please wait.")
            return

        self.add_to_leaderboard(bonkee)
        self.save_last_bonk(bonker)
        await ctx.message.reference.resolved.add_reaction(BONK_EMOJI)
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
        embed_title = "Hall of Shame"
        output = self.get_top_n(10)
        embed = discord.Embed(title=embed_title, description=f"```{output}```")
        await interaction.response.send_message(embed=embed)

    def get_top_n(self, num):
        body = []

        leaderboard = load_json_file(BONK_LEADERBOARD_FILE)
        filtered_leaderboard = dict(itertools.islice(leaderboard.items(), num))
        for k, v in filtered_leaderboard.items():
            body.append([v['name'], v['score']])

        output = t2a(
            header=["Name", "Bonks"],
            body=body,
            style=PresetStyle.ascii_borderless
        )

        return output

    def get_last_bonk(self, author):
        last_bonks = load_json_file(LAST_BONK_FILE)
        author_id = str(author.id)
        if(author_id not in last_bonks.keys()):
            return None
        return last_bonks[author_id]["last_bonk"]

    def save_last_bonk(self, author):
        last_bonks = load_json_file(LAST_BONK_FILE)
        author_id = str(author.id)
        last_bonks[author_id] = {'name': author.name,
                                    'last_bonk': time.time()}
        save_json_file(last_bonks, LAST_BONK_FILE)


    def add_to_leaderboard(self, author):
        leaderboard = load_json_file(BONK_LEADERBOARD_FILE)
        author_id = str(author.id)
        if str(author.id) in leaderboard.keys():
            leaderboard[author_id] = {'name': author.name,
                                      'score': leaderboard[author_id]['score']+1}
        else:
            leaderboard[author_id] = {'name': author.name, 'score': 1}
        sorted_leaderboard = {k: v for (k, v) in sorted(
            leaderboard.items(), key=lambda x: x[1]['score'], reverse=True)}
        save_json_file(sorted_leaderboard, BONK_LEADERBOARD_FILE)


async def setup(bot: commands.Bot):
    await bot.add_cog(Bonk(bot))
