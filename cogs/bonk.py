from discord.ext import commands
from vars.eind_vars import *
import logging

class Bonk(commands.Cog, name="Bonk"):

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        logging.info(f"{__name__} Cog is ready")

    @commands.command()
    async def bonk(self, ctx):
        await ctx.message.reference.resolved.reply("<a:bonk:995996313650999387>")

async def setup(bot: commands.Bot):
    await bot.add_cog(Bonk(bot))