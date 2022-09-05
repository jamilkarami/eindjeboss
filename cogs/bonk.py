from discord.ext import commands
from discord import app_commands
import discord
from util.vars.eind_vars import *
import logging
from util.util import *
from table2ascii import table2ascii as t2a, PresetStyle
import os

N_CHANNEL_ID = os.getenv('N_CHANNEL_ID')
class Bonk(commands.Cog, name="Bonk"):

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        logging.info(f"{__name__} Cog is ready")

    @commands.command()
    async def bonk(self, ctx):
        if not ctx.message.reference:
            await ctx.message.reply("I need someone to bonk.")
            return

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

        self.add_to_leaderboard(bonkee)
        await ctx.message.reference.resolved.reply(BONK_EMOJI)
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
        sorted_leaderboard = {k: v for (k, v) in sorted(
            leaderboard.items(), key=lambda x: x[1]['score'], reverse=True)[:num]}
        for k, v in sorted_leaderboard.items():
            body.append([v['name'], v['score']])

        output = t2a(
            header=["Name", "Bonks"],
            body=body,
            style=PresetStyle.ascii_borderless
        )

        return output

    def add_to_leaderboard(self, author):
        leaderboard = load_json_file(BONK_LEADERBOARD_FILE)
        author_id = str(author.id)
        if str(author.id) in leaderboard.keys():
            leaderboard[author_id] = {'name': author.name,
                                      'score': leaderboard[author_id]['score']+1}
        else:
            leaderboard[author_id] = {'name': author.name, 'score': 1}
        save_json_file(leaderboard, BONK_LEADERBOARD_FILE)


async def setup(bot: commands.Bot):
    await bot.add_cog(Bonk(bot))
