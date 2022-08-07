import logging
from discord.ext import commands
import random
import time

class Casino(commands.Cog):

    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_ready(self):
        logging.info(f"{__name__} Cog is ready")

    @commands.command(aliases=[])
    async def roll(self, ctx, *args):
        max = 20 if not args else int(args[0])

        random.seed(time.time())
        num = random.randint(1, max)

        await ctx.message.reply("You roll a D{max}. You get: {num}.".format(max = str(max), num = str(num)))
        return

    @commands.command(aliases=["8ball"])
    async def ball(self, ctx):
        options = ["Yes ✅", "No ❌", "Ask again...", "Definitely ✅", "I don't think so ❌"]
        random.seed(time.time())
        await ctx.message.reply(random.choice(options))

    @commands.command(aliases=[])
    async def coin(self, ctx):
        options = ["Heads", "Tails"]
        random.seed(time.time())
        await ctx.message.reply(random.choice(options))

async def setup(bot):
    await bot.add_cog(Casino(bot))