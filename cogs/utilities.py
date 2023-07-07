import ast
import json
import logging as lg
import operator as op
import re

import discord
import requests
from discord import app_commands
from discord.ext import commands

from bot import Eindjeboss
from util.vars.eind_vars import CHANNEL_IGNORE_LIST

CALC_REGEX = r"(?:calc|calculate) (.{3,})"

operators = {ast.Add: op.add, ast.Sub: op.sub, ast.Mult: op.mul,
             ast.Div: op.truediv, ast.Pow: op.pow, ast.BitXor: op.xor,
             ast.USub: op.neg}

MSG_URL = "https://discord.com/api/v9/guilds/{}/messages/search?author_id={}"
MSG_TOTAL_DESC = "Find out how many messages you (or someone else) \
have/has sent in total in this server."


class Utilities(commands.Cog):

    def __init__(self, bot: Eindjeboss):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        lg.info(f"[{__name__}] Cog is ready")

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user:
            return
        if message.channel.id in CHANNEL_IGNORE_LIST:
            return

        message_content = message.content.lower()

        calc_pattern = re.compile(CALC_REGEX)
        matches = calc_pattern.match(message_content)

        if (matches):
            try:
                expression = matches.group(1)
                expression = make_replacements(expression)
                result = '{0:.2f}'.format(calculate(expression))
                lg.info("Calculated expression for %s", message.author.name)
            except TypeError as te:
                lg.error(f"Failed to calculate expression \"{expression}\""
                         f" for {message.author.name}")
                lg.debug(te)
                await message.reply(
                    'Your expression could not be calculated.'
                    ' Please check your formatting.')
            else:
                await message.reply(f"{result}")

    @app_commands.command(name="tagall")
    async def tagall(self, intr: discord.Interaction):
        max_members_tag = await self.bot.get_setting("max_members_tag")
        if type(intr.channel).__name__ != "Thread":
            await intr.response.send_message(
                "You can only use this command inside threads.",
                ephemeral=True)
            return

        users = await intr.channel.fetch_members()
        if len(users) > max_members_tag:
            await intr.response.send_message(
                "This thread has too many members. (>%s)" % max_members_tag,
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
        auth_header = await self.bot.get_setting("discord_auth_header")
        guild_id = intr.guild_id
        if not user:
            user = intr.user
        ttl_msg = self.get_total_messages(guild_id, user.id, auth_header)

        await intr.response.send_message(
            "%s has sent a total of around %s messages in this server."
            % (user.mention, ttl_msg))
        lg.info("Sent message total for %s to %s", user.name, intr.user.name)

    def get_total_messages(self, guild_id, user_id, auth_header):
        url = MSG_URL.format(guild_id, user_id)
        data = requests.get(url=url, headers={
            "Authorization": auth_header})
        return json.loads(data.content)["total_results"]


def make_replacements(expression: str):
    replacements = {
        "÷": "/",
        "x": "*"
    }

    for k, v in replacements.items():
        expression = expression.replace(k, v)

    return expression


def calculate(expression: str):
    node = ast.parse(expression, mode='eval').body
    return eval_(node)


def eval_(node):
    if isinstance(node, ast.Num):
        return node.n
    elif isinstance(node, ast.BinOp):
        return operators[type(node.op)](eval_(node.left), eval_(node.right))
    elif isinstance(node, ast.UnaryOp):
        return operators[type(node.op)](eval_(node.operand))
    else:
        raise TypeError(node)


async def setup(client: Eindjeboss):
    await client.add_cog(Utilities(client))
