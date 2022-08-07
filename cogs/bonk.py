from discord.ext import commands
from cogs.eind_vars import *
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

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user:
            return
        if message.channel.name in CHANNEL_IGNORE_LIST:
            return
            
        message_content = message.content.lower()

        # Bonk users
        if any(word.lower() in message_content for word in BONK_TRIGGERS):
            await message.reply("<a:bonk:995996313650999387>")
            return

async def setup(bot: commands.Bot):
    await bot.add_cog(Bonk(bot))