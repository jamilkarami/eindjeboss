import discord
import random
import logging as lg
from util.vars.eind_vars import CHANNEL_IGNORE_LIST
from discord import app_commands
from discord.ext import commands

DEFAULT_ROLL = 20
ROLL_FOR_TEXT = "roll for "
HEY_ARNOL_TEXT = "hey arnol, "
EIGHT_BALL_OPTIONS = [
    "Yes ✅",
    "It is decidedly so ✅",
    "All signs point to yes ✅",
    "Definitely ✅",
    "No ❌",
    "I don't think so ❌",
    "Don't count on it ❌",
    "My sources say nope ❌",
]

EIGHT_BALL_DESCRIPTION = "Shake the magic 8 ball and get the answer you seek."
CH_DESC = "Let Arnol choose! Handy for when you don't know what to pick."


class Casino(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_message(self, msg):
        if msg.author == self.client.user:
            return
        if msg.channel.name in CHANNEL_IGNORE_LIST:
            return

        msg_cont: str = msg.content.lower()

        if msg_cont.startswith(ROLL_FOR_TEXT):
            reason_for_roll = msg_cont[len(ROLL_FOR_TEXT):]
            random.seed()
            num = random.randint(1, DEFAULT_ROLL)
            await msg.reply(
                f"You roll a D20 for _\"{reason_for_roll}\"_. You get: {num}.")
            return

        if msg_cont.startswith(HEY_ARNOL_TEXT) and msg_cont.endswith("?"):
            random.seed()
            answer = random.choice(EIGHT_BALL_OPTIONS)
            await msg.reply(answer)

    @commands.Cog.listener()
    async def on_ready(self):
        lg.info(f"[{__name__}] Cog is ready")

    @app_commands.command(name="roll", description="Roll a die.")
    async def roll(self, intr: discord.Interaction, maximum: int = None):
        if not maximum:
            maximum = DEFAULT_ROLL
        if maximum < 2:
            await intr.response.send_message(
                "The maximum can only be 2 and above.", ephemeral=True)
            return

        random.seed()
        num = random.randint(1, maximum)

        await intr.response.send_message(
            f"You roll a D{str(maximum)}. You get: {str(num)}.")

    @app_commands.command(name="8ball",
                          description=EIGHT_BALL_DESCRIPTION)
    async def ball(self, intr: discord.Interaction):
        random.seed()
        message = f"Magic 8 ball says: {random.choice(EIGHT_BALL_OPTIONS)}"
        await intr.response.send_message(message)

    @app_commands.command(description="Flip a coin.")
    async def coin(self, intr: discord.Interaction):
        options = ["Heads", "Tails"]
        random.seed()
        message = f"You flip a coin. It lands on: {random.choice(options)}"
        await intr.response.send_message(message)

    @app_commands.command(name="chooseforme",
                          description=CH_DESC)
    async def choose(self, intr: discord.Interaction, options: str):
        split_options = [x.strip().capitalize() for x in options.split(",")]
        resp_o = ", ".join([f"**{x}**" for x in split_options])
        random.seed()
        ch = (random.choice(split_options) if "takumi"
              not in (opt.lower() for opt in split_options) else "Takumi")
        resp = (f"You asked me to choose from {resp_o}.\n\nI choose: **{ch}**")

        await intr.response.send_message(resp)


async def setup(bot):
    await bot.add_cog(Casino(bot))
